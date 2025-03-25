# main.py
import os
import streamlit as st
import streamlit.components.v1 as components
import webbrowser
import subprocess
import traceback
import re

from frontend.frontend_dev import generate_frontend_code
from backend.backend_dev import generate_backend_code
from dsa.dsa_solver import solve_dsa_problem
from utils.code_execution import execute_python_code
from utils.code_extractor import extract_code_block

def main():
    # Set page configuration
    st.set_page_config(
        page_title="AI Software Development Agent", 
        page_icon="💻", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for improved styling
    st.markdown("""
    <style>
    .main-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .code-output {
        background-color: #f4f4f4;
        border-radius: 5px;
        padding: 10px;
        max-height: 400px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main title with custom styling
    st.markdown("<h1 style='text-align: center; color: #2C3E50;'>🚀 AI Software Development Agent</h1>", unsafe_allow_html=True)

    # Sidebar for API Key and task selection
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter your Gemini API Key", type="password")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

        task = st.selectbox("Select a task:", [
            "Frontend Development", 
            "Backend Development", 
            "DSA Problem Solving"
        ])

    # Main content area
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Task-specific sections with error handling
    try:
        if task == "Frontend Development":
            frontend_development()
        elif task == "Backend Development":
            backend_development()
        elif task == "DSA Problem Solving":
            dsa_problem_solving()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())

    st.markdown('</div>', unsafe_allow_html=True)

def frontend_development():
    st.subheader("🌐 Frontend Website Generation")
    
    # Input and validation
    website_name = st.text_input("Enter website type (e.g., Portfolio, E-Commerce, Blog)")
    
    if st.button("Generate & Preview Website"):
        if not website_name:
            st.warning("Please enter a website type.")
            return

        with st.spinner("Generating frontend code..."):
            try:
                # Generate the full HTML response
                html_response = generate_frontend_code(website_name)
                
                # Extract only the HTML code
                html_code = extract_code_block(html_response, 'html')
                
                # Save only the HTML code
                with open("generated_site.html", "w") as f:
                    f.write(html_code)
                
                # Display preview
                st.subheader("Live Preview:")
                components.html(html_code, height=600, scrolling=True)

                # Browser opening with error handling
                if st.button("Open in Browser"):
                    try:
                        webbrowser.open("file://" + os.path.abspath("generated_site.html"))
                    except Exception as e:
                        st.error(f"Could not open browser: {e}")

            except Exception as e:
                st.error(f"Error generating frontend code: {e}")
                st.error(traceback.format_exc())

def backend_development():
    st.subheader("🔧 Backend API Generation")
    
    api_description = st.text_area("Describe your API requirements")
    
    if st.button("Generate API Code"):
        if not api_description:
            st.warning("Please provide API requirements.")
            return

        with st.spinner("Generating backend code..."):
            try:
                # Generate the full backend code response
                backend_response = generate_backend_code(api_description)
                
                # Extract only the Python code
                backend_code = extract_code_block(backend_response, 'python')
                
                # Display code
                st.code(backend_code, language="python")

                # Save only the backend code
                with open("generated_api.py", "w") as f:
                    f.write(backend_code)
                
                # Run API with error handling
                try:
                    subprocess.Popen(["python", "generated_api.py"])
                    st.success("API is running! Test it on http://127.0.0.1:8000/docs")
                except Exception as api_error:
                    st.error(f"Could not start API: {api_error}")

            except Exception as e:
                st.error(f"Error generating backend code: {e}")
                st.error(traceback.format_exc())

def dsa_problem_solving():
    st.subheader("📊 DSA Problem Solver")
    
    problem_statement = st.text_area("Describe your DSA problem")
    
    if st.button("Solve DSA Problem"):
        if not problem_statement:
            st.warning("Please provide a problem statement.")
            return

        with st.spinner("Solving DSA problem..."):
            try:
                # Generate the full DSA solution response
                dsa_response = solve_dsa_problem(problem_statement)
                
                # Extract only the Python code
                dsa_solution = extract_code_block(dsa_response, 'python')
                
                # Display code
                st.code(dsa_solution, language="python")
                
                # Execute solution with error handling
                try:
                    result = execute_python_code(dsa_solution)
                    st.subheader("Output:")
                    st.code(result, language="python")
                except Exception as exec_error:
                    st.error(f"Error executing DSA solution: {exec_error}")

            except Exception as e:
                st.error(f"Error solving DSA problem: {e}")
                st.error(traceback.format_exc())

if __name__ == "__main__":
    main()