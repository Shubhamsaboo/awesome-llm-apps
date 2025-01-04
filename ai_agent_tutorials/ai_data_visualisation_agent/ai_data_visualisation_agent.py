import streamlit as st
import pandas as pd
import tempfile
import re
from together import Together
import csv
from dotenv import load_dotenv
import base64
import matplotlib.pyplot as plt
import io
import seaborn as sns

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
        
        # Log the data types of columns before preprocessing
        st.write("Data types before preprocessing:")
        st.write(df.dtypes)
        
        # Ensure string columns are properly quoted
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)
        
        # Parse dates and numeric columns
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif df[col].dtype == 'object':
                try:
                    # Handle columns with values like "4.1/5"
                    if df[col].str.contains('/').any():
                        # Split the values and take the first part (e.g., "4.1/5" -> 4.1)
                        df[col] = df[col].str.split('/').str[0]
                    # Convert to numeric, coerce errors to NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except (ValueError, TypeError):
                    # Keep as is if conversion fails
                    st.warning(f"Could not convert column '{col}' to numeric. Keeping as string.")
                    pass
        
        # Drop rows with all NaN values
        df.dropna(how='all', inplace=True)
        
        # Log the data types of columns after preprocessing
        st.write("Data types after preprocessing:")
        st.write(df.dtypes)
        
        # Create a temporary file to save the preprocessed data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_path = temp_file.name
            # Save the DataFrame to the temporary CSV file
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)
        
        return temp_path, df.columns.tolist(), df  # Return the DataFrame as well
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None

# Function to execute Python code and generate plots
def execute_code(code: str, df):
    try:
        # Define locals with necessary imports and the DataFrame
        local_env = {
            'pd': pd,
            'df': df,
            'plt': plt,
            'sns': sns  # if seaborn is needed
        }
        # Execute the code in the local environment
        exec(code, globals(), local_env)
        
        # Check if a plot was generated
        if 'plt' in local_env:
            # Save the plot to a BytesIO object
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            # Encode the plot as base64
            base64_image = base64.b64encode(buf.read()).decode('utf-8')
            return base64_image
        else:
            st.warning("No plot generated. Ensure the data being plotted is numeric.")
            return None
    except Exception as e:
        st.error(f"Error executing code: {e}")
        return None

# Function to communicate with Together AI
def chat_with_llm(user_message, file_path, columns, df):
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
        # Execute the code and generate the plot
        base64_image = execute_code(python_code, df)
        return response_message, base64_image
    else:
        print(f"Failed to match any Python code in model's response {response_message}")
        return response_message, None

# Set up Streamlit app
st.title("AI Data Scientist")

# Sidebar for API keys and file upload
st.sidebar.header("API Keys")
together_api_key = st.sidebar.text_input("Together AI API Key", type="password")

# Store API key in session state
if 'together_api_key' not in st.session_state:
    st.session_state.together_api_key = None

uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel File", type=['csv', 'xlsx'])

# System prompt (dynamic based on the uploaded file)
SYSTEM_PROMPT = """
You are a Python data scientist. You have access to a CSV file located at '{file_path}'.
The dataset has the following columns: {columns}.
You can read this file into a DataFrame using `df = pd.read_csv('{file_path}')` and perform data analysis tasks based on user queries.
Make sure to handle missing values and data type inconsistencies. When generating plots,
use matplotlib or seaborn and output the plot as a base64 string.
Always check if the data being plotted is numeric. If the data is not numeric, preprocess it to convert it to numeric values.
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

# Main app logic
if uploaded_file:
    if not together_api_key:
        st.warning("Please provide the Together AI API key.")
    else:
        # Update session state with API key
        st.session_state.together_api_key = together_api_key
        
        # Initialize Together AI client only after confirming API key exists
        try:
            client = Together(api_key=together_api_key)
            
            # Preprocess and save the uploaded file
            temp_path, columns, df = preprocess_and_save(uploaded_file)
            if temp_path:
                # Rest of your code for user query handling
                user_query = st.text_input("Ask a query about the data:")
                if st.button("Submit Query"):
                    response_message, base64_image = chat_with_llm(user_query, temp_path, columns, df)
                    
                    # Display AI's response
                    st.write("AI's Response:")
                    st.write(response_message)
                    
                    # Display the plot if generated
                    if base64_image:
                        st.image(base64.b64decode(base64_image), use_container_width=True)
                    else:
                        st.write("No plot generated.")
            else:
                st.error("Failed to preprocess and save the data.")
        except Exception as e:
            st.error(f"Error initializing Together AI client: {str(e)}")
else:
    st.warning("Please upload a file.")