import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.media import Image
from agno.models.google import Gemini
import tempfile
import os

def main():
    # Streamlit app title
    st.title("Multimodal Reasoning AI Agent 🧠")

    # Get Gemini API key from user in sidebar
    with st.sidebar:
        st.header("🔑 Configuration")
        gemini_api_key = st.text_input("Enter your Gemini API Key", type="password")
        st.caption(
            "Get your API key from [Google AI Studio]"
            "(https://aistudio.google.com/apikey) 🔑"
        )

    # Instruction
    st.write(
        "Upload an image and provide a reasoning-based task for the AI Agent. "
        "The AI Agent will analyze the image and respond based on your input."
    )

    if not gemini_api_key:
        st.warning("Please enter your Gemini API key in the sidebar to continue.")
        return

    # Set up the reasoning agent
    agent = Agent(
        model=Gemini(id="gemini-2.5-pro", api_key=gemini_api_key), 
        markdown=True
    )

    # File uploader for image
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            # Save uploaded file to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name

            # Display the uploaded image
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

            # Input for dynamic task
            task_input = st.text_area(
                "Enter your task/question for the AI Agent:"
            )

            # Button to process the image and task
            if st.button("Analyze Image") and task_input:
                with st.spinner("AI is thinking... 🤖"):
                    try:
                        # Call the agent with the dynamic task and image path
                        response: RunOutput = agent.run(task_input, images=[Image(filepath=temp_path)])
                        
                        # Display the response from the model
                        st.markdown("### AI Response:")
                        st.markdown(response.content)
                    except Exception as e:
                        st.error(f"An error occurred during analysis: {str(e)}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

        except Exception as e:
            st.error(f"An error occurred while processing the image: {str(e)}")

if __name__ == "__main__":
    main()