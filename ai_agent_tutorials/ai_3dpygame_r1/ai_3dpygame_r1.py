import streamlit as st
from openai import OpenAI
from phi.agent import Agent as PhiAgent
from phi.model.anthropic import Claude
import asyncio
from browser_use import Agent as BrowserAgent, SystemPrompt
from langchain_anthropic import ChatAnthropic

st.set_page_config(page_title="PyGame Code Generator", layout="wide")

# Initialize session state
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {
        "deepseek": "",
        "claude": ""
    }

# Streamlit sidebar for API keys
with st.sidebar:
    st.title("API Keys Configuration")
    st.session_state.api_keys["deepseek"] = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=st.session_state.api_keys["deepseek"]
    )
    st.session_state.api_keys["claude"] = st.text_input(
        "Claude API Key",
        type="password",
        value=st.session_state.api_keys["claude"]
    )

# Main UI
st.title("AI 3D Visualizer with R1")
example_query = "Create a particle system simulation where 100 particles emit from the mouse position and respond to keyboard-controlled wind forces"
query = st.text_area(
    "Enter your PyGame query:",
    height=70,
    placeholder=f"e.g.: {example_query}"
)
generate_btn = st.button("Generate Code and Visualisation")

if generate_btn and query:
    if not st.session_state.api_keys["deepseek"] or not st.session_state.api_keys["claude"]:
        st.error("Please provide both API keys in the sidebar")
        st.stop()

    # Initialize Deepseek client
    deepseek_client = OpenAI(
        api_key=st.session_state.api_keys["deepseek"],
        base_url="https://api.deepseek.com"
    )

    system_prompt = """You are a Pygame and Python Expert that specializes in making games and visualisation through pygame and python programming. 
    During your reasoning and thinking, include clear, concise, and well-formatted Python code in your reasoning. 
    Always include explanations for the code you provide."""

    try:
        # Get reasoning from Deepseek
        with st.spinner("Generating solution..."):
            deepseek_response = deepseek_client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=1  
            )

        reasoning_content = deepseek_response.choices[0].message.reasoning_content
        print("\nDeepseek Reasoning:\n", reasoning_content)
        with st.expander("R1's Reasoning"):      
            st.write(reasoning_content)

        # Initialize Claude agent (using PhiAgent)
        claude_agent = PhiAgent(
            model=Claude(
                id="claude-3-5-sonnet-20241022",
                api_key=st.session_state.api_keys["claude"]
            ),
            show_tool_calls=True,
            markdown=True
        )

        # Extract code
        extraction_prompt = f"""Extract ONLY the Python code from the following content which is reasoning of a particular query to make a pygame script. 
        Return nothing but the raw code without any explanations, or markdown backticks:
        {reasoning_content}"""

        with st.spinner("Extracting code..."):
            code_response = claude_agent.run(extraction_prompt)
            extracted_code = code_response.content

        with st.expander("Generated PyGame Code"):      
            st.code(extracted_code, language="python")

        # Initialize browser agent for Trinket interaction
        async def run_pygame_on_trinket(code: str) -> None:
            task_description = (
                "You are a Trinket.io PyGame expert. Follow these steps precisely:\n"
                "1. Navigate to https://trinket.io/features/pygame\n"
                "2. In the main.py file, clear any existing code in the editor\n"
                "3. Paste this code into the editor:\n{0}\n"
                "4. Click the Run button on the right to execute the code\n"
                "5. Wait for the pygame visualisation to appear, once it does, view it for 10 seconds and then Quit the pygame window\n"
            ).format(code)

            browser_agent = BrowserAgent(
                task=task_description,
                llm=ChatAnthropic(
                    model="claude-3-5-sonnet-20240620",
                    api_key=st.session_state.api_keys["claude"]
                ),
                max_actions_per_step=5,
                max_failures=3
            )

            with st.spinner("Running code on Trinket..."):
                try:
                    result = await browser_agent.run()
                    if result and hasattr(result, 'final_response'):
                        share_url = result.final_response
                        st.success("Code is running on Trinket!")
                        st.write("You can view the visualization here:")
                        st.write(share_url)
                    else:
                        st.error("Failed to get a sharing URL from Trinket")
                except Exception as e:
                    st.error(f"Error running code on Trinket: {str(e)}")
                    st.info("You can still copy the code above and run it manually on Trinket")

        # Run the async function
        asyncio.run(run_pygame_on_trinket(extracted_code))

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

elif generate_btn and not query:
    st.warning("Please enter a query before generating code")