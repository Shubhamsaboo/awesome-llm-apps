import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
import os

# Import Camel-AI and OWL modules
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.societies import RolePlaying
from camel.toolkits import (
    ExcelToolkit,
    SearchToolkit,
    CodeExecutionToolkit,
    FileWriteToolkit,
)
from owl.utils import run_society
from owl.utils import DocumentProcessingToolkit

# Set log level to see detailed logs (optional)
set_log_level("DEBUG")

# Load environment variables from .env file if available

load_dotenv()

def construct_society(question: str) -> RolePlaying:
    r"""Construct a society of agents based on the given question.

    Args:
        question (str): The task or question to be addressed by the society.

    Returns:
        RolePlaying: A configured society of agents ready to address the question.
    """

    # Create models for different components
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
    }

    # Configure toolkits
    tools = [
        *CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
        SearchToolkit().search_duckduckgo,
        SearchToolkit().search_wiki,
        SearchToolkit().search_baidu,
        *ExcelToolkit().get_tools(),
        *FileWriteToolkit(output_dir="./").get_tools(),
    ]

    # Configure agent roles and parameters
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Configure task parameters
    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    # Create and return the society
    society = RolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )

    return society

def summarize_section():
    st.header("Summarize Medical Text")
    text = st.text_area("Enter medical text to summarize:", height=200)
    if st.button("Summarize"):
        if text:
            # Create a task prompt for summarization
            task_prompt = f"Summarize the following medical text:\n\n{text}"
            society = construct_society(task_prompt)
            with st.spinner("Running summarization society..."):
                answer, chat_history, token_count = run_society(society)
                st.subheader("Summary:")
                st.write(answer)
                st.write(chat_history)
        else:
            st.warning("Please enter some text to summarize.")

def write_and_refine_article_section():
    st.header("Write and Refine Research Article")
    topic = st.text_input("Enter the topic for the research article:")
    outline = st.text_area("Enter an outline (optional):", height=150)
    if st.button("Write and Refine Article"):
        if topic:
            # Create a task prompt for article writing and refinement
            task_prompt = f"Write a research article and save it locally on the topic: {topic}."
            if outline.strip():
                task_prompt += f" Use the following outline as guidance:\n{outline}"
            society = construct_society(task_prompt)
            with st.spinner("Running research article society..."):
                print(task_prompt)
                answer, chat_history, token_count = run_society(society)
                st.subheader("Article:")
                st.write(answer)
                st.write(chat_history)
        else:
            st.warning("Please enter a topic for the research article.")

def sanitize_data_section():
    st.header("Sanitize Medical Data (PHI)")
    data = st.text_area("Enter medical data to sanitize:", height=200)
    if st.button("Sanitize Data"):
        if data:
            # Create a task prompt for data sanitization
            task_prompt = f"Sanitize the following medical data by removing any protected health information (PHI) and save it locally:\n\n{data}"
            society = construct_society(task_prompt)
            with st.spinner("Running data sanitization society..."):
                answer, chat_history, token_count = run_society(society)
                st.subheader("Sanitized Data:")
                st.write(answer)
                st.write(chat_history)
        else:
            st.warning("Please enter medical data to sanitize.")

def main():
    st.set_page_config(page_title="Multi-Agent AI System with Camel & OWL", layout="wide")
    st.title("Multi-Agent AI System with Camel-AI and OWL")

    st.sidebar.title("Select Task")
    task = st.sidebar.selectbox("Choose a task:", [
        "Summarize Medical Text",
        "Write and Refine Research Article",
        "Sanitize Medical Data (PHI)"
    ])

    if task == "Summarize Medical Text":
        summarize_section()
    elif task == "Write and Refine Research Article":
        write_and_refine_article_section()
    elif task == "Sanitize Medical Data (PHI)":
        sanitize_data_section()

if __name__ == "__main__":
    main()
