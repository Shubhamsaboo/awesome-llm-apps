import streamlit as st
import os
from dotenv import load_dotenv
import json
import re
from together import Together
from e2b_code_interpreter import Sandbox
from typing import Optional, List, Any
import tempfile

# Load environment variables
load_dotenv()

# Get API keys from environment variables
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
E2B_API_KEY = os.getenv("E2B_API_KEY")

# Define the Together AI model to use
MODEL_NAME = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"

# System prompt for the LLM
SYSTEM_PROMPT = """You are a highly skilled Python data scientist. Your task is to analyze datasets and generate Python code to solve data-related problems. Follow these guidelines:

1. **Data Preprocessing**:
   - Always check for missing or invalid values in the dataset.
   - Handle missing values by either removing rows/columns or imputing them appropriately.
   - Convert columns to the correct data types (e.g., numeric, datetime).
   - Filter out rows with invalid or inconsistent data.

2. **Data Analysis**:
   - Perform exploratory data analysis (EDA) to understand the dataset.
   - Use statistical methods to analyze relationships between variables.
   - If the task involves machine learning (e.g., linear regression), ensure the data is properly prepared (e.g., feature scaling, train-test split).

3. **Visualization**:
   - Use libraries like `matplotlib` or `seaborn` for creating visualizations.
   - Ensure plots are clear, labeled, and informative (e.g., include titles, axis labels, legends).
   - Save plots as images (e.g., PNG) and return them as base64-encoded strings.

4. **Code Quality**:
   - Write clean, modular, and well-commented Python code.
   - Handle potential errors gracefully (e.g., invalid data, missing columns).
   - Include necessary imports (e.g., `pandas`, `numpy`, `matplotlib`, `seaborn`).

5. **Output**:
   - Always return the Python code to solve the task.
   - If the task involves visualization, include the code to generate and save the plot."""

# Function to execute code in the E2B Sandbox
def code_interpret(e2b_code_interpreter, code):
    print("Running code interpreter...")
    exec = e2b_code_interpreter.run_code(
        code,
        on_stderr=lambda stderr: print("[Code Interpreter]", stderr),
        on_stdout=lambda stdout: print("[Code Interpreter]", stdout),
    )

    if exec.error:
        print("[Code Interpreter ERROR]", exec.error)
    else:
        return exec.results

# Initialize Together AI client
client = Together(api_key=TOGETHER_API_KEY)

# Regex pattern to extract Python code blocks from LLM responses
pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)

# Function to extract Python code from LLM responses
def match_code_blocks(llm_response):
    match = pattern.search(llm_response)
    if match:
        code = match.group(1)
        print("Extracted Python code:")
        print(code)
        return code
    return ""

# Function to interact with the LLM and execute code in the sandbox
def chat_with_llm(e2b_code_interpreter, user_message):
    """
    Interact with LLM and execute code in sandbox.
    
    Args:
        e2b_code_interpreter: The E2B Sandbox instance
        user_message: User's query string
    
    Returns:
        List of results from code execution
    """
    print(f"\n{'='*50}\nUser message: {user_message}\n{'='*50}")

    # Add file path information to the user message
    enhanced_message = f"""
The dataset is located at '/data.csv' in the current directory. 
User query: {user_message}
Important: Always use '/data.csv' as the path when reading the dataset.
"""

    # Prepare messages for the LLM
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": enhanced_message},
    ]

    # Get response from Together AI
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )

    # Extract the response message
    response_message = response.choices[0].message.content
    print("LLM Response:")
    print(response_message)

    # Extract Python code from the response
    python_code = match_code_blocks(response_message)
    if python_code:
        # Execute the code in the sandbox
        code_interpreter_results = code_interpret(e2b_code_interpreter, python_code)
        return code_interpreter_results
    else:
        print(f"Failed to match any Python code in model's response: {response_message}")
        return []

# Function to upload a dataset to the E2B Sandbox
def upload_dataset(code_interpreter: Sandbox, uploaded_file: Any) -> str:
    """
    Upload a dataset to the E2B Sandbox from Streamlit's uploaded file.
    
    Args:
        code_interpreter: The E2B Sandbox instance
        uploaded_file: Streamlit's UploadedFile object
    
    Returns:
        str: Path to the uploaded dataset in the sandbox
    """
    print("Uploading dataset to Code Interpreter sandbox...")
    
    try:
        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            dataset_path = tmp_file.name

        # Upload the dataset to the sandbox
        with open(dataset_path, "rb") as f:
            code_interpreter.files.write("/data.csv", f)

        # Clean up the temporary file
        os.unlink(dataset_path)
        
        print("Dataset uploaded to: /data.csv")
        return "/data.csv"
    except Exception as error:
        print("Error during file upload:", error)
        raise error

def main():
    """Main function to run the Streamlit application."""
    st.title("AI Data Visualization Agent")
    st.write("Upload your dataset and ask questions about it!")

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    # Text input for the query
    user_query = st.text_input("Enter your visualization query:")
    
    # Process button
    if st.button("Generate Visualization") and uploaded_file is not None and user_query:
        try:
            with Sandbox(api_key=E2B_API_KEY) as code_interpreter:
                # Upload the dataset
                upload_dataset(code_interpreter, uploaded_file)
                
                # Get and execute the visualization code
                with st.spinner("Generating visualization..."):
                    code_results = chat_with_llm(code_interpreter, user_query)
                
                # Display results
                if code_results:
                    first_result = code_results[0]
                    
                    # If there's an image output
                    if hasattr(first_result, "png"):
                        st.image(first_result.png, caption="Generated Visualization")
                    else:
                        st.write("Results:", first_result)
                else:
                    st.error("No results generated")
                    
        except Exception as e:
            st.error(f"An error occurred: {e}")
    elif not uploaded_file:
        st.warning("Please upload a dataset first")
    elif not user_query:
        st.warning("Please enter a query")

if __name__ == "__main__":
    main()