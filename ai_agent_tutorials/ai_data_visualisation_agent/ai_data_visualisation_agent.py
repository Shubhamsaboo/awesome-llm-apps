import streamlit as st
import pandas as pd
import tempfile
import os
import re
from together import Together
import csv
import uuid
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from typing import Optional, Union, List

# Load environment variables
load_dotenv()

# Function to preprocess and save the uploaded file to a temporary file
def preprocess_and_save(file):
    try:
        # Read the uploaded file into a DataFrame
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, na_values=['NA', 'N/A', 'missing'])
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None, None, None
        
        # Ensure string columns are properly quoted
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)
        
        # Parse dates and numeric columns
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    # Keep as is if conversion fails
                    pass
        
        # Create a temporary file to save the preprocessed data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_path = temp_file.name
            # Save the DataFrame to the temporary CSV file
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)
        
        return temp_path, df.columns.tolist(), df  # Return the DataFrame as well
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None

# Function to execute Python code in E2B sandbox
def code_interpret(code: str) -> str:
    """
    Execute Python code in E2B sandbox.
    
    Args:
        code: Python code to execute
        
    Returns:
        String containing stdout from code execution
    """
    print("Running code in E2B sandbox...")
    
    sbx = Sandbox(api_key=st.session_state.e2b_api_key)
    
    try:
        execution = sbx.run_code("code")
        # Convert list output to string if needed
        stdout = execution.logs.stdout
        if isinstance(stdout, list):
            return '\n'.join(map(str, stdout))
        return stdout if stdout else ""
    except Exception as e:
        return f"Error executing code: {str(e)}"

# Function to communicate with LLM
def chat_with_llm(user_message, file_path, columns):
    print(f"\n{'='*50}\nUser message: {user_message}\n{'='*50}")

    # Update the system prompt with the file path, columns, and plot path
    system_prompt = SYSTEM_PROMPT.format(
        file_path=file_path,
        columns=columns,
    )

    # Add a hint to include a plot if the user asks for visualization
    if "plot" in user_message.lower():
        system_prompt += " Include a plot in your response and output the base64 string of the plot image."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Use the Together API key from session state
    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        messages=messages,
    )

    response_message = response.choices[0].message.content
    print("LLM Response:", response_message)  # Debug: Print the LLM's response
    python_code = match_code_blocks(response_message)
    print("Extracted Python Code:", python_code)  # Debug: Print the extracted code

    if python_code:
        # Modify the code to handle the 'approx_cost(for two people)' column correctly
        python_code = python_code.replace(
            "df['approx_cost(for two people)'] = df['approx_cost(for two people)'].str.replace(',', '')",
            "df['approx_cost(for two people)'] = df['approx_cost(for two people)'].astype(str).str.replace(',', '')"
        )
        stdout = code_interpret(python_code)
        return response_message, stdout, None
    else:
        print(f"Failed to match any Python code in model's response {response_message}")
        return response_message, None, None

# Set up Streamlit app
st.title("AI Data Scientist")

# Sidebar for API keys and file upload
st.sidebar.header("API Keys")
together_api_key = st.sidebar.text_input("Together AI API Key", type="password")
e2b_api_key = st.sidebar.text_input("E2B API Key", type="password")

# Store API keys in session state
if 'together_api_key' not in st.session_state:
    st.session_state.together_api_key = None
if 'e2b_api_key' not in st.session_state:
    st.session_state.e2b_api_key = None

uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel File", type=['csv', 'xlsx'])

# System prompt (dynamic based on the uploaded file)
SYSTEM_PROMPT = """
You are a Python data scientist. You have access to a CSV file located at '{file_path}'.
The dataset has the following columns: {columns}.
You can read this file into a DataFrame using `df = pd.read_csv('{file_path}')` and perform data analysis tasks based on user queries.
Make sure to handle missing values and data type inconsistencies. When generating plots,
use matplotlib or seaborn and output the plot as a base64 string.
Always respond with the Python code to answer the user's query, and include visualizations only if explicitly requested.
"""

# Function to match Python code blocks
pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)

def match_code_blocks(llm_response):
    match = pattern.search(llm_response)
    if match:
        code = match.group(1)
        # Remove comments and extra text
        code = "\n".join([line for line in code.split("\n") if not line.strip().startswith("#")])
        return code
    return ""

# Function to extract base64 image from stdout
def extract_base64_image(stdout: Optional[Union[str, List[str]]]) -> Optional[str]:
    """
    Extract base64 image from stdout content.
    
    Args:
        stdout: String or list of strings containing output
        
    Returns:
        Base64 encoded image string if found, None otherwise
    """
    if stdout is None:
        return None
    
    # Convert list to string if needed
    if isinstance(stdout, list):
        stdout = '\n'.join(map(str, stdout))
    elif not isinstance(stdout, str):
        stdout = str(stdout)
    
    # Look for base64 image data in the stdout
    image_pattern = re.compile(r'base64_image:\s*(.*?)\n', re.DOTALL)
    match = image_pattern.search(stdout)
    if match:
        return match.group(1)
    return None

# Main app logic
if 'together_api_key' in st.session_state and 'e2b_api_key' in st.session_state and uploaded_file:
    # Preprocess and save the uploaded file to a temporary file
    temp_path, columns, df = preprocess_and_save(uploaded_file)
    if temp_path:
        # Initialize Together AI client using the API key from session state
        client = Together(api_key=st.session_state.together_api_key)
        
        # User query input
        user_query = st.text_input("Ask a query about the data:")
        if st.button("Submit Query"):
            # Chat with LLM
            response_message, stdout, stderr = chat_with_llm(user_query, temp_path, columns)
            # Display AI's response
            st.write("AI's Response:")
            st.write(response_message)
            
            # Display any printed output
            if stdout:
                st.write("Code Output:")
                st.write(stdout)
            else:
                st.write("No output produced by the code.")
            
            # Extract base64 image from stdout
            base64_image = extract_base64_image(stdout)
            if base64_image:
                # Display the image
                st.image(base64_image, use_container_width=True)
            else:
                st.write("No plot generated.")
    else:
        st.error("Failed to preprocess and save the data.")
else:
    st.warning("Please provide API keys and upload a file.")