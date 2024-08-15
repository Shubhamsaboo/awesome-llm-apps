import streamlit as st
from litellm import completion

# Set up the Streamlit app
st.title("Multi-LLM Chat Playground")

# Get API keys from the user
openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password")
anthropic_api_key = st.text_input("Enter your Anthropic API Key:", type="password")
cohere_api_key = st.text_input("Enter your Cohere API Key:", type="password")

# Check if all API keys are provided
if openai_api_key and anthropic_api_key and cohere_api_key:

    # Create a text input for user messages
    user_input = st.text_input("Enter your message:")

    if st.button("Send to All LLMs"):
        if user_input:
            messages = [{"role": "user", "content": user_input}]
            
            # Create three columns for side-by-side display
            col1, col2, col3 = st.columns(3)
            
            # GPT-4o response
            with col1:
                st.subheader("GPT-4o")
                try:
                    gpt_response = completion(model="gpt-4o", messages=messages, api_key=openai_api_key)
                    st.write(gpt_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error with GPT-4o: {str(e)}")
            
            # Claude-3-sonnet response
            with col2:
                st.subheader("Claude 3.5 Sonnet")
                try:
                    claude_response = completion(model="claude-3-5-sonnet-20240620", messages=messages, api_key=anthropic_api_key)
                    st.write(claude_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error with Claude 3.5 Sonnet: {str(e)}")
            
            # Cohere response
            with col3:
                st.subheader("Cohere")
                try:
                    cohere_response = completion(model="command-r-plus", messages=messages, api_key=cohere_api_key)
                    st.write(cohere_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error with Cohere: {str(e)}")
            
            # Compare responses
            st.subheader("Response Comparison")
            st.write("You can see how the three models responded differently to the same input.")
            st.write("This demonstrates the ability to use multiple LLMs in a single application.")
        else:
            st.warning("Please enter a message.")
else:
    st.warning("Please enter all API keys to use the chat.")

# Add some information about the app
st.sidebar.title("About this app")

st.sidebar.write(
    "This app demonstrates the use of multiple Language Models (LLMs) "
    "in a single application using the LiteLLM library."
)

st.sidebar.subheader("Key features:")
st.sidebar.markdown(
    """
    - Utilizes three different LLMs:
        - OpenAI's GPT-4o
        - Anthropic's Claude 3.5 Sonnet
        - Cohere's Command R Plus
    - Sends the same user input to all models
    - Displays responses side-by-side for easy comparison
    - Showcases the ability to use multiple LLMs in one application
    """
)

st.sidebar.write(
    "Try it out to see how different AI models respond to the same prompt!"
)
