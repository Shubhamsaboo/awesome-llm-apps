"""Streamlit Critique & Improvement Loop Demo using GPT-OSS via Groq

This implements the "Automatic Critique + Improvement Loop" pattern:
1. Generate initial answer (Pro Mode style)
2. Have a critic model identify flaws/missing pieces
3. Revise the answer addressing all critiques
4. Repeat if needed

Run with:
    streamlit run streamlit_app.py
"""

import os
import time
import concurrent.futures as cf
from typing import List, Dict, Any

import streamlit as st
from groq import Groq, GroqError

MODEL = "openai/gpt-oss-120b"
MAX_COMPLETION_TOKENS = 1024  # stay within Groq limits

SAMPLE_PROMPTS = [
    "Explain how to implement a binary search tree in Python.",
    "What are the best practices for API design?",
    "How would you optimize a slow database query?",
    "Explain the concept of recursion with examples.",
]

# --- Helper functions --------------------------------------------------------

def _one_completion(client: Groq, messages: List[Dict[str, str]], temperature: float) -> str:
    """Single non-streaming completion with basic retries."""
    delay = 0.5
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                top_p=1,
                stream=False,
            )
            return resp.choices[0].message.content
        except GroqError:
            if attempt == 2:
                raise
            time.sleep(delay)
            delay *= 2


def generate_initial_answer(client: Groq, prompt: str) -> str:
    """Generate initial answer using parallel candidates + synthesis (Pro Mode)."""
    # Generate 3 candidates in parallel
    candidates = []
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        futures = [
            ex.submit(_one_completion, client, 
                     [{"role": "user", "content": prompt}], 0.9)
            for _ in range(3)
        ]
        for fut in cf.as_completed(futures):
            candidates.append(fut.result())
    
    # Synthesize candidates
    candidate_texts = []
    for i, c in enumerate(candidates):
        candidate_texts.append(f"--- Candidate {i+1} ---\n{c}")
    
    synthesis_prompt = (
        f"You are given 3 candidate answers. Synthesize them into ONE best answer, "
        f"eliminating repetition and ensuring coherence:\n\n"
        f"{chr(10).join(candidate_texts)}\n\n"
        f"Return the single best final answer."
    )
    
    return _one_completion(client, [{"role": "user", "content": synthesis_prompt}], 0.2)


def critique_answer(client: Groq, prompt: str, answer: str) -> str:
    """Have a critic model identify flaws and missing pieces."""
    critique_prompt = (
        f"Original question: {prompt}\n\n"
        f"Answer to critique:\n{answer}\n\n"
        f"Act as a critical reviewer. List specific flaws, missing information, "
        f"unclear explanations, or areas that need improvement. Be constructive but thorough. "
        f"Format as a bulleted list starting with '•'."
    )
    
    return _one_completion(client, [{"role": "user", "content": critique_prompt}], 0.3)


def revise_answer(client: Groq, prompt: str, original_answer: str, critiques: str) -> str:
    """Revise the original answer addressing all critiques."""
    revision_prompt = (
        f"Original question: {prompt}\n\n"
        f"Original answer:\n{original_answer}\n\n"
        f"Critiques to address:\n{critiques}\n\n"
        f"Revise the original answer to address every critique point. "
        f"Maintain the good parts, fix the issues, and add missing information. "
        f"Return the improved answer."
    )
    
    return _one_completion(client, [{"role": "user", "content": revision_prompt}], 0.2)


def critique_improvement_loop(prompt: str, max_iterations: int = 2, groq_api_key: str | None = None) -> Dict[str, Any]:
    """Main function implementing the critique and improvement loop."""
    client = Groq(api_key=groq_api_key) if groq_api_key else Groq()
    
    results = {
        "iterations": [],
        "final_answer": "",
        "total_iterations": 0
    }
    
    # Generate initial answer
    with st.spinner("Generating initial answer..."):
        initial_answer = generate_initial_answer(client, prompt)
        results["iterations"].append({
            "type": "initial",
            "answer": initial_answer,
            "critiques": None
        })
    
    current_answer = initial_answer
    
    # Improvement loop
    for iteration in range(max_iterations):
        with st.spinner(f"Critiquing iteration {iteration + 1}..."):
            critiques = critique_answer(client, prompt, current_answer)
        
        with st.spinner(f"Revising iteration {iteration + 1}..."):
            revised_answer = revise_answer(client, prompt, current_answer, critiques)
            
            results["iterations"].append({
                "type": "improvement",
                "answer": revised_answer,
                "critiques": critiques
            })
            
            current_answer = revised_answer
    
    results["final_answer"] = current_answer
    results["total_iterations"] = len(results["iterations"])
    
    return results


# --- Streamlit UI ------------------------------------------------------------

st.set_page_config(page_title="Critique & Improvement Loop", page_icon="🔄", layout="wide")
st.title("🔄 Critique & Improvement Loop")

st.markdown(
    "Generate high-quality answers through iterative critique and improvement using GPT-OSS."
)

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Groq API Key", value=os.getenv("GROQ_API_KEY", ""), type="password")
    max_iterations = st.slider("Max Improvement Iterations", 1, 3, 2)
    st.markdown("---")
    st.caption("Each iteration adds critique + revision steps for higher quality.")

# Initialize prompt in session state if not present
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""

def random_prompt_callback():
    import random
    st.session_state["prompt"] = random.choice(SAMPLE_PROMPTS)

prompt = st.text_area("Your prompt", height=150, placeholder="Ask me anything…", key="prompt")

col1, col2 = st.columns([1, 1])
with col1:
    st.button("🔄 Random Sample Prompt", on_click=random_prompt_callback)
with col2:
    generate_clicked = st.button("🚀 Start Critique Loop")

if generate_clicked:
    if not prompt.strip():
        st.error("Please enter a prompt.")
        st.stop()

    try:
        results = critique_improvement_loop(prompt, max_iterations, groq_api_key=api_key or None)
    except Exception as e:
        st.exception(e)
        st.stop()

    # Display results
    st.subheader("🎯 Final Answer")
    st.write(results["final_answer"])
    
    # Show improvement history
    with st.expander(f"📋 Show Improvement History ({results['total_iterations']} iterations)"):
        for i, iteration in enumerate(results["iterations"]):
            if iteration["type"] == "initial":
                st.markdown(f"### 🚀 Initial Answer")
                st.write(iteration["answer"])
            else:
                st.markdown(f"### 🔍 Iteration {i}")
                
                # Show critiques
                if iteration["critiques"]:
                    st.markdown("**Critiques:**")
                    st.write(iteration["critiques"])
                
                # Show improved answer
                st.markdown("**Improved Answer:**")
                st.write(iteration["answer"])
            
            if i < len(results["iterations"]) - 1:
                st.markdown("---")

    # Summary metrics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Iterations", results["total_iterations"])
    with col2:
        st.metric("Improvement Rounds", max_iterations)
    with col3:
        st.metric("Final Answer Length", len(results["final_answer"])) 