import streamlit as st
from agents import create_breakup_team
from image_input import analyze_chat_screenshot
from PIL import Image

# --- Streamlit Layout ---
st.title("💔 Breakup Recovery Agent Team")
st.write("Receive support and emotional outlet messages from specialized AI agents.")

# --- API Keys Input ---
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
submit_button = st.sidebar.button("Submit")

# --- Store API Keys ---
if submit_button:
    if gemini_api_key:
        st.session_state["gemini_api_key"] = gemini_api_key
        st.success("API key saved successfully!")
    else:
        st.error("Please enter the API key!")

# --- User Input ---
user_input = st.text_area("Describe how you're feeling...")

# --- Image Upload ---
uploaded_image = st.file_uploader("Upload a chat screenshot (optional)", type=["png", "jpg", "jpeg"])

# --- Display Uploaded Image and Analysis ---
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Screenshot", use_column_width=True)
    
    if st.button("Analyze Chat"):
        with st.spinner("Analyzing chat patterns..."):
            if not st.session_state.get("gemini_api_key"):
                st.error("Please enter your Gemini API key in the sidebar first.")
            else:
                try:
                    # Set environment variable for the analysis
                    import os
                    os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key"]
                    
                    # Analyze the chat screenshot
                    analysis = analyze_chat_screenshot(uploaded_image)
                    
                    # Display the analysis
                    st.subheader("🔍 Chat Analysis")
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")
                    st.info("Please check your Gemini API key and try again.")

# --- Execute Agent Team (only for text input) ---
if st.button("Get Recovery Support"):
    with st.spinner("Agents are processing..."):
        if not user_input:
            st.error("Please enter what you feel.")
        elif not st.session_state.get("gemini_api_key"):
            st.error("Please enter your Gemini API key in the sidebar first.")
        else:
            try:
                breakup_team = create_breakup_team()

                # Set environment variables
                import os
                os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key"]

                # Execute the team with text input
                response = breakup_team.run(user_input)

                # Display responses
                st.subheader("💡 Team's Responses")

                # Display individual agent responses
                if response.member_responses:
                    for index, member_response in enumerate(response.member_responses, start=0):
                        st.markdown(f"### 🛡️ {response.tools[index]['tool_args']['agent_name']}")
                        st.markdown(member_response.content)
                else:
                    st.warning("⚠️ No individual agent responses received. This might be due to an API error or configuration issue.")
                    st.info("Please check your Gemini API key and try again.")

                # Display team leader's final summary
                if response.content:
                    st.subheader("📜 Team Leader's Summary")
                    st.markdown(response.content)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your Gemini API key and try again.")
