import os
import json
import re
from typing import Optional, List, Any, Tuple
from dotenv import load_dotenv
from PIL import Image
import io
import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from PIL import Image
from together import Together
from e2b_code_interpreter import Sandbox

# Load environment variables
load_dotenv()

# Regex pattern to extract code from LLM response
pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)

def code_interpret(e2b_code_interpreter: Sandbox, code: str) -> Optional[List[Any]]:
    """
    Runs the given Python code in the E2B sandbox.
    
    Args:
        e2b_code_interpreter: The E2B sandbox instance
        code: Python code to execute
        
    Returns:
        Optional[List[Any]]: Results from code execution
    """
    with st.spinner('Executing code in E2B sandbox...'):
        exec = e2b_code_interpreter.run_code(code,
            on_stderr=lambda stderr: st.error(f"[Code Interpreter] {stderr}"),
            on_stdout=lambda stdout: st.info(f"[Code Interpreter] {stdout}"))

        if exec.error:
            st.error(f"[Code Interpreter ERROR] {exec.error}")
            return None
        return exec.results

def match_code_blocks(llm_response: str) -> str:
    """
    Extracts Python code blocks from the LLM response.
    
    Args:
        llm_response: The response from the LLM
        
    Returns:
        str: Extracted Python code or empty string
    """
    match = pattern.search(llm_response)
    if match:
        code = match.group(1)
        return code
    return ""

def chat_with_llm(e2b_code_interpreter: Sandbox, user_message: str, dataset_path: str) -> Tuple[Optional[List[Any]], str]:
    """
    Sends the user message to the LLM and executes the generated code.
    
    Args:
        e2b_code_interpreter: The E2B sandbox instance
        user_message: User's query message
        dataset_path: Path to the uploaded dataset
        
    Returns:
        Tuple[Optional[List[Any]], str]: Code execution results and LLM response
    """
    # Update system prompt to include dataset path information
    system_prompt = f"""You're a Python data scientist and data visualization expert. You are given a dataset at path '{dataset_path}' and also the user's query.
You need to analyze the dataset and answer the user's query with a response and you run Python code to solve them.
IMPORTANT: Always use the dataset path variable '{dataset_path}' in your code when reading the CSV file."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    with st.spinner('Getting response from together AI...'):
        client = Together(api_key=st.session_state.together_api_key)
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=messages,
        )

        response_message = response.choices[0].message
        python_code = match_code_blocks(response_message.content)
        
        if python_code:
            code_interpreter_results = code_interpret(e2b_code_interpreter, python_code)
            return code_interpreter_results, response_message.content
        else:
            st.warning(f"Failed to match any Python code in model's response")
            return None, response_message.content

def upload_dataset(code_interpreter: Sandbox, uploaded_file) -> str:
    """
    Uploads the dataset to the E2B sandbox.
    
    Args:
        code_interpreter: The E2B sandbox instance
        uploaded_file: Streamlit uploaded file
        
    Returns:
        str: Path where file was uploaded
    """
    dataset_path = f"./{uploaded_file.name}"
    
    try:
        code_interpreter.files.write(dataset_path, uploaded_file)
        return dataset_path
    except Exception as error:
        st.error(f"Error during file upload: {error}")
        raise error


def main():
    """Main Streamlit application."""
    st.title("AI Data Visualization Assistant")
    st.write("Upload your dataset and ask questions about it!")

    # Sidebar for API keys and model name
    with st.sidebar:
        st.header("API Keys and Model Configuration")
        st.session_state.together_api_key = st.text_input("Enter Together API Key", type="password")
        st.session_state.e2b_api_key = st.text_input("Enter E2B API Key", type="password")
        st.session_state.model_name = st.text_input("Enter Model Name", value="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Display dataset preview
        df = pd.read_csv(uploaded_file)
        st.write("Dataset Preview:")
        st.dataframe(df.head())
        
        # Query input
        query = st.text_area("What would you like to know about your data?",
                            "Can you compare the average cost for two people between different categories?")
        
        if st.button("Analyze"):
            if not st.session_state.together_api_key or not st.session_state.e2b_api_key:
                st.error("Please enter both API keys in the sidebar.")
            else:
                with Sandbox(api_key=st.session_state.e2b_api_key) as code_interpreter:
                    # Upload the dataset
                    dataset_path = upload_dataset(code_interpreter, uploaded_file)
                    
                    # Pass dataset_path to chat_with_llm
                    code_results, llm_response = chat_with_llm(code_interpreter, query, dataset_path)
                    
                    # Display LLM's text response
                    st.write("AI Response:")
                    st.write(llm_response)
                    
                    # Display results/visualizations
                    if code_results:
                        for result in code_results:
                            if hasattr(result, 'png') and result.png:  # Check if PNG data is available
                                # Decode the base64-encoded PNG data
                                png_data = base64.b64decode(result.png)
                                
                                # Convert PNG data to an image and display it
                                image = Image.open(BytesIO(png_data))
                                st.image(image, caption="Generated Visualization", use_container_width=False)
                            elif hasattr(result, 'figure'):  # For matplotlib figures
                                fig = result.figure  # Extract the matplotlib figure
                                st.pyplot(fig)  # Display using st.pyplot
                            elif hasattr(result, 'show'):  # For plotly figures
                                st.plotly_chart(result)
                            elif isinstance(result, (pd.DataFrame, pd.Series)):
                                st.dataframe(result)
                            else:
                                st.write(result)  

if __name__ == "__main__":
    main()