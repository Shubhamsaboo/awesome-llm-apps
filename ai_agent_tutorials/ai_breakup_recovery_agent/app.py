import streamlit as st
from agents import create_breakup_team
from PIL import Image

# --- Streamlit Layout ---
st.title("💔 Breakup Recovery Agent Team")
st.write("Receive support and emotional outlet messages from specialized AI agents.")

# --- API Keys Input ---
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
submit_button = st.sidebar.button("Submit")

# --- Store API Keys ---
if submit_button:
    if openai_api_key:
        st.session_state["openai_api_key"] = openai_api_key
        st.success("API keys saved successfully!")
    else:
        st.error("Please enter both API keys!")

# --- User Input ---
user_input = st.text_area("Describe how you're feeling...")

# --- Image Upload ---
uploaded_image = st.file_uploader("Upload a chat screenshot (optional)", type=["png", "jpg", "jpeg"])

# --- Display Uploaded Image ---
extracted_text = ""
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Screenshot", use_column_width=True)

    # # ✅ Extract text from the image
    # extracted_text = extract_text_with_easyocr(image)
    # st.text_area("Extracted Text from Image:", extracted_text)

# --- Execute Agent Team ---
if st.button("Get Recovery Support"):
    with st.spinner("Agents are processing..."):
        if not user_input and not uploaded_image:
            st.error("Please enter what you feel.")
        else:
            breakup_team = create_breakup_team()

            # Set environment variables
            import os
            os.environ["OPENAI_API_KEY"] = st.session_state.get("openai_api_key", "")

            # Prepare the input
            input_data = user_input
            if uploaded_image:
                input_data += "\n\n[Attached Image Included]"  # Add image indicator

            # Execute the team
            response = breakup_team.run(user_input)

            # Display responses
            st.subheader("💡 Team's Responses")

            # Display individual agent responses
            if response.member_responses:
                for member_response in response.member_responses:
                    st.markdown(f"### 🛡️ {member_response.agent_id}")
                    st.write(member_response.content)
            else:
                st.warning("⚠️ No individual agent responses received. Showing team leader's summary only.")

            # Display team leader's final summary
            st.subheader("📜 Team Leader's Summary")
            st.write(response.content)
