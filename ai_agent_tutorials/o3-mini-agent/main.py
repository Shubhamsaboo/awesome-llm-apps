from typing import Optional, Dict, Any
import streamlit as st
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from e2b_code_interpreter import Sandbox
import os
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
load_dotenv()

def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = ''
    if 'gemini_key' not in st.session_state:
        st.session_state.gemini_key = ''
    if 'e2b_key' not in st.session_state:
        st.session_state.e2b_key = ''
    if 'sandbox' not in st.session_state:
        st.session_state.sandbox = None

def setup_sidebar() -> None:
    """Setup sidebar with API key inputs."""
    with st.sidebar:
        st.title("API Configuration")
        st.session_state.openai_key = st.text_input("OpenAI API Key", 
                                                   value=st.session_state.openai_key,
                                                   type="password")
        st.session_state.gemini_key = st.text_input("Gemini API Key", 
                                                   value=st.session_state.gemini_key,
                                                   type="password")
        st.session_state.e2b_key = st.text_input("E2B API Key",
                                                value=st.session_state.e2b_key,
                                                type="password")

def create_agents() -> tuple[Agent, Agent, Agent]:
    """Create vision, coding, and execution agents with API keys from session state."""
    vision_agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp", api_key=st.session_state.gemini_key),
        markdown=True,
    )

    coding_agent = Agent(
        model=OpenAIChat(
            id="o3-mini", 
            api_key=st.session_state.openai_key,
            system_prompt="""You are an expert Python programmer. You will receive coding problems similar to LeetCode questions, 
            which may include problem statements, sample inputs, and examples. Your task is to:
            1. Analyze the problem carefully
            2. Write clean, efficient Python code to solve it
            3. Include proper documentation and type hints
            4. The code will be executed in an e2b sandbox environment
            Please ensure your code is complete and handles edge cases appropriately."""
        ),
        markdown=True
    )
    
    execution_agent = Agent(
        model=OpenAIChat(
            id="o3-mini",
            api_key=st.session_state.openai_key,
            system_prompt="""You are an expert at executing Python code in sandbox environments.
            Your task is to:
            1. Take the provided Python code
            2. Execute it in the e2b sandbox
            3. Format and explain the results clearly
            4. Handle any execution errors gracefully
            Always ensure proper error handling and clear output formatting."""
        ),
        markdown=True
    )
    
    return vision_agent, coding_agent, execution_agent

def initialize_sandbox() -> None:
    """Initialize or reset the e2b sandbox."""
    try:
        if st.session_state.sandbox:
            st.session_state.sandbox.close()
        os.environ['E2B_API_KEY'] = st.session_state.e2b_key
        st.session_state.sandbox = Sandbox()
    except Exception as e:
        st.error(f"Failed to initialize sandbox: {str(e)}")
        st.session_state.sandbox = None

def run_code_in_sandbox(code: str) -> Dict[str, Any]:
    """
    Run code in e2b sandbox and return execution results.
    
    Args:
        code: Python code to execute
        
    Returns:
        Dict containing execution logs and any output
    """
    if not st.session_state.sandbox:
        initialize_sandbox()
    
    execution = st.session_state.sandbox.run_code(code)
    return {
        "logs": execution.logs,
        "files": st.session_state.sandbox.files.list("/")
    }

def process_image_with_gemini(vision_agent: Agent, image: Image) -> str:
    """
    Process uploaded image with Gemini Vision to extract code problem.
    
    Args:
        vision_agent: Initialized Gemini vision agent
        image: Uploaded image to process
        
    Returns:
        str: Extracted problem description in natural language
    """
    prompt = """Analyze this image and extract any coding problem or code snippet shown. 
    Describe it in clear natural language, including any:
    1. Problem statement
    2. Input/output examples
    3. Constraints or requirements
    Format it as a proper coding problem description."""
    
    # Convert image to bytes for Gemini
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=image.format)
    img_byte_arr = img_byte_arr.getvalue()
    
    response = vision_agent.run(prompt, images=[img_byte_arr])
    return response.content

def execute_code_with_agent(execution_agent: Agent, code: str, sandbox: Sandbox) -> str:
    """
    Use execution agent to run and explain code results.
    """
    try:
        execution = sandbox.run_code(code)
        
        # Handle execution errors
        if execution.error:
            error_prompt = f"""The code execution resulted in an error:
            Error: {execution.error}
            
            Please analyze the error and provide a clear explanation of what went wrong."""
            response = execution_agent.run(error_prompt)
            return f"⚠️ Execution Error:\n{response.content}"
        
        prompt = f"""Here is the code execution result:
        Logs: {execution.logs}
        Files: {sandbox.files.list("/")}
        
        Please provide a clear explanation of the results and any outputs."""
        
        response = execution_agent.run(prompt)
        return response.content
    except Exception as e:
        return f"⚠️ Sandbox Error: {str(e)}"

def main() -> None:
    """Main application function."""
    st.title("O3-Mini Coding Assistant")
    
    initialize_session_state()
    setup_sidebar()
    
    # Check all required API keys
    if not (st.session_state.openai_key and 
            st.session_state.gemini_key and 
            st.session_state.e2b_key):
        st.warning("Please enter all required API keys in the sidebar.")
        return
    
    vision_agent, coding_agent, execution_agent = create_agents()
    
    # Clean, single-column layout
    uploaded_image = st.file_uploader(
        "Upload an image of your coding problem (optional)",
        type=['png', 'jpg', 'jpeg']
    )
    
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
    
    user_query = st.text_area(
        "Or type your coding problem here:",
        placeholder="Example: Write a function to find the sum of two numbers. Include sample input/output cases.",
        height=100
    )
    
    # Process button
    if st.button("Generate & Execute Solution", type="primary"):
        if uploaded_image and not user_query:
            # Process image with Gemini
            with st.spinner("Processing image..."):
                image = Image.open(uploaded_image)
                extracted_query = process_image_with_gemini(vision_agent, image)
                
                st.info("📝 Extracted Problem:")
                st.write(extracted_query)
                
                # Pass extracted query to coding agent
                with st.spinner("Generating solution..."):
                    response = coding_agent.run(extracted_query)
                    
        elif user_query and not uploaded_image:
            # Direct text input processing
            with st.spinner("Generating solution..."):
                response = coding_agent.run(user_query)
                
        elif user_query and uploaded_image:
            st.error("Please use either image upload OR text input, not both.")
            return
        else:
            st.warning("Please provide either an image or text description of your coding problem.")
            return
        
        # Display and execute solution
        if 'response' in locals():
            st.divider()
            st.subheader("💻 Solution")
            
            # Extract code from markdown response
            code_blocks = response.content.split("```python")
            if len(code_blocks) > 1:
                code = code_blocks[1].split("```")[0].strip()
                
                # Display the code
                st.code(code, language="python")
                
                # Execute code with execution agent
                with st.spinner("Executing code..."):
                    if not st.session_state.sandbox:
                        initialize_sandbox()
                    
                    execution_results = execute_code_with_agent(
                        execution_agent,
                        code,
                        st.session_state.sandbox
                    )
                    
                    # Display execution results
                    st.divider()
                    st.subheader("🚀 Execution Results")
                    st.markdown(execution_results)
                    
                    # Display any generated files
                    files = st.session_state.sandbox.files.list("/")
                    if files:
                        st.markdown("📁 **Generated Files:**")
                        st.json(files)

if __name__ == "__main__":
    main()

