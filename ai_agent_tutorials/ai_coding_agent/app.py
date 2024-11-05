import streamlit as st
import pandas as pd
import os
from crewai import Crew
from langchain_groq import ChatGroq
import streamlit_ace as st_ace
import traceback
import contextlib
import io
from crewai_tools import FileReadTool
import matplotlib.pyplot as plt
import glob
from dotenv import load_dotenv
from autotabml_agents import initialize_agents
from autotabml_tasks import create_tasks


TEMP_DIR = "temp_dir"
OUTPUT_DIR = "Output_dir"
# Ensure the temporary directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Ensure the Output directory exits 
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    file_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# load the .env file
load_dotenv()
# Set up Groq API key
groq_api_key = os.environ.get("GROQ_API_KEY")  # os.environ["GROQ_API_KEY"] =


def main():
    # Set custom CSS for UI
    set_custom_css()

    # Initialize session state for edited code
    if 'edited_code' not in st.session_state:
        st.session_state['edited_code'] = ""
    
    # Initialize session state for whether the initial code is generated
    if 'code_generated' not in st.session_state:
        st.session_state['code_generated'] = False

    # Header with futuristic design
    st.markdown("""
        <div class="header">
            <h1>AutoTabML</h1>
            <p>Automated Machine Learning Code Generation for Tabluar Data</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar for customization options
    st.sidebar.title('LLM Model')
    model = st.sidebar.selectbox(
        'Model',
        ["llama3-70b-8192"]
    )

    # Initialize LLM
    llm = initialize_llm(model)

    

    # User inputs
    user_question = st.text_area("Describe your ML problem:", key="user_question")
    uploaded_file = st.file_uploader("Upload a sample .csv of your data", key="uploaded_file")
    try:
        file_name = uploaded_file.name
    except: 
        file_name = "dataset.csv"

    # Initialize agents
    agents = initialize_agents(llm,file_name,TEMP_DIR)
    # Process uploaded file
    if uploaded_file:
        try:
            file_path = save_uploaded_file(uploaded_file)
            df = pd.read_csv(uploaded_file)
            st.write("Data successfully uploaded:")
            st.dataframe(df.head())
            data_upload = True
        except Exception as e:
            st.error(f"Error reading the file: {e}")
            data_upload = False
    else:
        df = None
        data_upload = False

    # Process button
    if st.button('Process'):
        tasks = create_tasks("Process",user_question,file_name, data_upload, df, None, st.session_state['edited_code'], None, agents)
        with st.spinner('Processing...'):
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                verbose=2
            )

            result = crew.kickoff()

            if result:  # Only call st_ace if code has a valid value
                code = result.strip("```")
                try:
                    filt_idx = code.index("```")
                    code = code[:filt_idx]
                except:
                    pass
                st.session_state['edited_code'] = code
                st.session_state['code_generated'] = True

        st.session_state['edited_code'] = st_ace.st_ace(
            value=st.session_state['edited_code'],
            language='python',
            theme='monokai',
            keybinding='vscode',
            min_lines=20,
            max_lines=50
        )

    if st.session_state['code_generated']:
        # Show options for modification, debugging, and running the code
        suggestion = st.text_area("Suggest modifications to the generated code (optional):", key="suggestion")
        if st.button('Modify'):
            if st.session_state['edited_code'] and suggestion:
                tasks = create_tasks("Modify",user_question,file_name, data_upload, df, suggestion, st.session_state['edited_code'], None, agents)
                with st.spinner('Modifying code...'):
                    crew = Crew(
                        agents=list(agents.values()),
                        tasks=tasks,
                        verbose=2
                    )

                    result = crew.kickoff()

                    if result:  # Only call st_ace if code has a valid value
                        code = result.strip("```")
                        try:
                            filter_idx = code.index("```")
                            code = code[:filter_idx]
                        except:
                            pass
                        st.session_state['edited_code'] = code

                st.write("Modified code:")
                st.session_state['edited_code']= st_ace.st_ace(
                    value=st.session_state['edited_code'],
                    language='python',
                    theme='monokai',
                    keybinding='vscode',
                    min_lines=20,
                    max_lines=50
                )

        debugger = st.text_area("Paste error message here for debugging (optional):", key="debugger")
        if st.button('Debug'):
            if st.session_state['edited_code'] and debugger:
                tasks = create_tasks("Debug",user_question,file_name, data_upload, df, None, st.session_state['edited_code'], debugger, agents)
                with st.spinner('Debugging code...'):
                    crew = Crew(
                        agents=list(agents.values()),
                        tasks=tasks,
                        verbose=2
                    )

                    result = crew.kickoff()

                    if result:  # Only call st_ace if code has a valid value
                        code = result.strip("```")
                        try:
                            filter_idx = code.index("```")
                            code = code[:filter_idx]
                        except:
                            pass
                        st.session_state['edited_code'] = code

                st.write("Debugged code:")
                st.session_state['edited_code'] = st_ace.st_ace(
                    value=st.session_state['edited_code'],
                    language='python',
                    theme='monokai',
                    keybinding='vscode',
                    min_lines=20,
                    max_lines=50
                )

        if st.button('Run'):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                try:
                    globals().update({'dataset': df})
                    final_code = st.session_state["edited_code"]
                    
                    with st.expander("Final Code"):
                        st.code(final_code, language='python')

                    exec(final_code, globals())
                    result = output.getvalue()
                    success = True
                except Exception as e:
                    result = str(e)
                    success = False

            st.subheader('Output:')
            st.text(result)

            figs = [manager.canvas.figure for manager in plt._pylab_helpers.Gcf.get_all_fig_managers()]
            if figs:
                st.subheader('Generated Plots:')
                for fig in figs:
                    st.pyplot(fig)

            if success:
                st.success("Code executed successfully!")
            else:
                st.error("Code execution failed! Waiting for debugging input...")

            # Move the generated files section to the sidebar
            with st.sidebar:
                st.header('Output_dir :')
                files = glob.glob(os.path.join(OUTPUT_DIR, '*'))
                for file in files:
                    if os.path.isfile(file):
                        with open(file, 'rb') as f:
                            st.download_button(label=f'Download {os.path.basename(file)}', data=f, file_name=os.path.basename(file))



# Function to set custom CSS for futuristic UI
def set_custom_css():
    st.markdown("""
        <style>
            body {
                background: #0e0e0e;
                color: #e0e0e0;
                font-family: 'Roboto', sans-serif;
            }
            .header {
                background: linear-gradient(135deg, #6e3aff, #b839ff);
                padding: 10px;
                border-radius: 10px;
            }
            .header h1, .header p {
                color: white;
                text-align: center;
            }
            .stButton button {
                background-color: #b839ff;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px 20px;
            }
            .stButton button:hover {
                background-color: #6e3aff;
                color: #e0e0e0;
            }
            .spinner {
                display: flex;
                justify-content: center;
                align-items: center;
            }
        </style>
    """, unsafe_allow_html=True)

# Function to initialize LLM
def initialize_llm(model):
    return ChatGroq(
        temperature=0,
        groq_api_key=groq_api_key,
        model_name=model
    )

if __name__ == "__main__":
    main()