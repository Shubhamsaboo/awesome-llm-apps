import streamlit as st
import pandas as pd
import os
import tempfile
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Page Configuration ---
st.set_page_config(
    page_title="Conversational Data Agent",
    page_icon=""
)

# --- Main App ---
st.title(" Conversational Data Agent ")
st.write("Upload a CSV or Excel file and ask questions about your data!")

# --- Sidebar for API Key ---
with st.sidebar:
    st.header("API Configuration")
    google_api_key = st.text_input("Enter your Google AI API key:", type="password")
    if google_api_key:
        st.session_state.google_api_key = google_api_key
        st.success("API key saved!")
    else:
        st.warning("Please enter your Google AI API key to proceed.")
    
    # Add a button to clear the chat history
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.success("Chat history cleared!")


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None and "google_api_key" in st.session_state:
    try:
        if 'processed_file_path' not in st.session_state or st.session_state.processed_file_name != uploaded_file.name:
            # Read the uploaded file into a Pandas DataFrame
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Create a temporary file to store the data as a CSV
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".csv") as temp_file:
                df.to_csv(temp_file.name, index=False)
                st.session_state.processed_file_path = temp_file.name
                st.session_state.processed_file_name = uploaded_file.name

            st.success(f"File '{uploaded_file.name}' uploaded and processed successfully!")
            st.write("Data Preview:")
            st.dataframe(df.head())
        
      
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=st.session_state.google_api_key
        )
        
        agent = create_csv_agent(
            llm=llm,
            path=st.session_state.processed_file_path,
            verbose=True,
            allow_dangerous_code=True
        )

      
        if user_query := st.chat_input("Ask a question about your data..."):
          
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner('The agent is thinking...'):
                    try:
                        # --- NEW: Construct prompt with history ---
                        # We create a string from the last few messages to give the agent context.
                        history = "\n".join([f'{m["role"]}: {m["content"]}' for m in st.session_state.messages[-4:]])
                        prompt_with_history = f"Considering the previous conversation:\n{history}\n\nAnswer the following question: {user_query}"

                        # Run the agent with the enhanced prompt
                        response = agent.run(prompt_with_history)
                        
                        st.markdown(response)

                        # Add assistant's response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    except Exception as e:
                        error_message = f"An error occurred: {e}"
                        st.error(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": error_message})

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")