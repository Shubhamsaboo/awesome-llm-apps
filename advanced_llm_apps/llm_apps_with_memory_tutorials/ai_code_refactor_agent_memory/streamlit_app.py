"""
Streamlit UI for AI Code Refactor Agent with Memory.
"""

import streamlit as st
import json
from datetime import datetime
from refactor_agent import CodeRefactorAgent

# Page configuration
st.set_page_config(
    page_title="AI Code Refactor Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔧 AI Code Refactor Agent with Learning Memory")
st.markdown("""
An intelligent agent that refactors Python code **and learns from failures**.
Each mistake teaches the agent what to avoid next time.
""")

# Session state
if "agent" not in st.session_state:
    st.session_state.agent = CodeRefactorAgent(model="mistral")
if "show_memory" not in st.session_state:
    st.session_state.show_memory = False

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    model_choice = st.selectbox(
        "Model",
        ["mistral", "llama2", "neural-chat", "openchat"],
        help="Ollama model to use. Make sure it's installed locally.",
    )
    
    ollama_host = st.text_input(
        "Ollama Host",
        value="http://localhost:11435",
        help="URL of your Ollama instance",
    )
    
    if model_choice != st.session_state.agent.model or ollama_host != st.session_state.agent.ollama_host:
        st.session_state.agent = CodeRefactorAgent(
            model=model_choice,
            ollama_host=ollama_host
        )
        st.success("Agent reinitialized!")
    
    st.divider()
    
    # Memory browser
    st.header("📚 Learning Memory")
    
    if st.button("View Learned Constraints"):
        st.session_state.show_memory = not st.session_state.show_memory
    
    if st.session_state.show_memory:
        if st.session_state.agent.discovered_constraints:
            st.subheader("Constraints Discovered")
            for i, constraint in enumerate(st.session_state.agent.discovered_constraints):
                with st.expander(f"Rule {i+1}: {constraint.constraint[:50]}..."):
                    st.write(f"**Constraint:** {constraint.constraint}")
                    st.write(f"**Explanation:** {constraint.explanation}")
                    st.write(f"**Severity:** {constraint.severity}")
                    st.write(f"**Context:** {constraint.context}")
                    st.write(f"**Times Violated:** {constraint.times_violated}")
                    st.write(f"**Times Helpful:** {constraint.times_helpful}")
        else:
            st.info("No constraints discovered yet. More refactoring = more learning!")
    
    st.divider()
    
    # Session summary
    st.header("📊 Session Summary")
    summary = st.session_state.agent.get_session_summary()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Refactorings", summary["total_refactorings"])
        st.metric("Successful", summary["successful"])
    with col2:
        st.metric("Failed", summary["failed"])
        st.metric("Success Rate", summary["success_rate"])
    
    if summary["constraints_discovered"] > 0:
        st.metric("Constraints Learned", summary["constraints_discovered"])
    
    if summary["strategy_adaptations"] > 0:
        st.metric("Strategy Adaptations", summary["strategy_adaptations"])

# Main content area
tab1, tab2, tab3 = st.tabs(["🔧 Refactor Code", "📖 How It Works", "🎓 Examples"])

with tab1:
    st.header("Refactor Your Code")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        code_input = st.text_area(
            "Paste your Python code here:",
            height=300,
            placeholder="def my_function():\n    pass",
        )
    
    with col2:
        st.subheader("Refactoring Options")
        
        refactoring_type = st.selectbox(
            "Type of Refactoring",
            options=list(CodeRefactorAgent.STRATEGIES.keys()),
            format_func=lambda x: f"{x.replace('_', ' ').title()}: {CodeRefactorAgent.STRATEGIES[x][:40]}...",
        )
        
        task_description = st.text_area(
            "What should be refactored?",
            height=100,
            placeholder="Make this code more Pythonic",
        )
        
        use_learned = st.checkbox(
            "✓ Use Learned Constraints",
            value=True,
            help="Learn from past mistakes to avoid repeating them",
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            refactor_btn = st.button("🚀 Refactor", use_container_width=True)
        with col_btn2:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_btn:
        code_input = ""
        task_description = ""
        st.rerun()
    
    if refactor_btn:
        if not code_input.strip():
            st.error("Please paste some code to refactor!")
        elif not task_description.strip():
            st.error("Please describe what you want to refactor!")
        else:
            with st.spinner("🤖 Agent is refactoring... (this may take 30-60s)"):
                outcome = st.session_state.agent.refactor_code(
                    code=code_input,
                    task=task_description,
                    refactoring_type=refactoring_type,
                    use_learned_constraints=use_learned,
                )
            
            # Display results
            st.divider()
            
            if outcome.status.value == "success":
                st.success("✅ Refactoring Successful!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Original Code")
                    st.code(outcome.code_input, language="python")
                
                with col2:
                    st.subheader("Refactored Code")
                    st.code(outcome.code_output, language="python")
                
                if outcome.key_insight:
                    with st.expander("💡 Agent's Explanation"):
                        st.write(outcome.key_insight)
            
            else:
                st.error("❌ Refactoring Failed")
                st.write(f"**Error:** {outcome.error_message}")
                st.write(f"**Root Cause:** {outcome.root_cause}")
                
                if st.session_state.agent.discovered_constraints:
                    st.info("✨ Agent learned from this failure! See 'Learning Memory' in the sidebar.")
            
            # Show if strategy adapted
            if st.session_state.agent.adaptations:
                latest_adaptation = st.session_state.agent.adaptations[-1]
                st.info(
                    f"🎯 **Strategy Adapted:** Changed from '{latest_adaptation.old_strategy}' "
                    f"to '{latest_adaptation.new_strategy}'"
                )

with tab2:
    st.header("How This Agent Works")
    
    st.subheader("🧠 Learning from Failures")
    st.markdown("""
    Traditional agents refactor code and move on. This agent **learns from every mistake**.
    
    **The Flow:**
    1. **Refactoring Attempt** → Agent tries to refactor your code
    2. **Outcome Tracking** → Records success or failure with error details
    3. **Constraint Discovery** → If it fails, analyzes WHY and extracts a rule
    4. **Memory Storage** → Saves the constraint for future reference
    5. **Strategy Adaptation** → After 3+ failures of same type, switches approach
    6. **Future Attempts** → Uses learned constraints to avoid past mistakes
    """)
    
    st.subheader("📚 What The Agent Remembers")
    st.markdown("""
    - **Execution Outcomes**: What succeeded, what failed, and why
    - **Constraints Discovered**: Rules like "NEVER rename functions without updating imports"
    - **Strategy Adaptations**: "Failed 3 times with approach A, now trying approach B"
    """)
    
    st.subheader("🎯 When Strategy Adapts")
    st.markdown("""
    The agent automatically shifts tactics when it detects repeated failures:
    
    | Condition | Old Strategy | New Strategy |
    |-----------|--------------|--------------|
    | Failed 3x on dataclasses | Try direct refactoring | Write tests first |
    | Repeated naming errors | Quick rename | Verify all imports updated |
    | Edge cases keep breaking | Rapid coding | Document constraints first |
    """)

with tab3:
    st.header("📚 Examples & Demonstrations")
    
    examples = {
        "Procedural to OOP": {
            "code": """def calculate_total(items):
    total = 0
    for item in items:
        total += item['price'] * item['qty']
    return total

def apply_discount(total, discount_pct):
    return total * (1 - discount_pct/100)""",
            "task": "Convert to an Order class with methods",
            "type": "procedural_to_oop",
        },
        "Add Type Hints": {
            "code": """def process_data(data):
    result = []
    for item in data:
        if item > 10:
            result.append(item * 2)
    return result""",
            "task": "Add comprehensive type hints",
            "type": "add_type_hints",
        },
        "Simplify with Comprehension": {
            "code": """def filter_and_transform(numbers):
    result = []
    for n in numbers:
        if n % 2 == 0:
            result.append(n ** 2)
    return result""",
            "task": "Simplify using list comprehension",
            "type": "simplify_logic",
        },
    }
    
    selected_example = st.selectbox("Choose an example:", list(examples.keys()))
    example = examples[selected_example]
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("Example Code")
        st.code(example["code"], language="python")
    
    with col2:
        st.subheader("Task")
        st.write(example["task"])
        st.write(f"**Type:** {example['type'].replace('_', ' ').title()}")
        
        if st.button("Try This Example"):
            st.session_state.code_input = example["code"]
            st.session_state.task_input = example["task"]
            st.session_state.refactoring_type = example["type"]
            st.success("Example loaded! Go to 'Refactor Code' tab to try it.")

# Footer
st.divider()
st.markdown("""
---
**🔗 Learn More:**
- [CogniCore Experience Memory](https://github.com/safetymind/cognicore)
- [Mem0 Documentation](https://mem0.ai)
- [Ollama Models](https://ollama.ai)

**⭐ Features:**
- ✅ Learns from failures
- ✅ Discovers constraints automatically  
- ✅ Adapts strategy based on experience
- ✅ 100% local & private (Ollama)
- ✅ No API keys needed

Made with ❤️ for the awesome-llm-apps community
""")
