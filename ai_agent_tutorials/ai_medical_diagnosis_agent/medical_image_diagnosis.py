import os
from PIL import Image
from phi.agent import Agent
from phi.model.google import Gemini
import streamlit as st
from phi.tools.duckduckgo import DuckDuckGo

st.set_page_config(
    page_title="Medical Imaging Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "GOOGLE_API_KEY" not in st.session_state:
    st.session_state.GOOGLE_API_KEY = None

medical_agent = Agent(
    model=Gemini(
        api_key=st.session_state.GOOGLE_API_KEY,
        id="gemini-2.0-flash-exp"
    ),
    tools=[DuckDuckGo()],
    markdown=True
) if st.session_state.GOOGLE_API_KEY else None

if not medical_agent:
    st.warning("Please configure your API key in the sidebar to continue")

MEDICAL_ANALYSIS_PROMPT = """
You are a highly skilled medical imaging diagnosis expert with extensive knowledge of radiology and diagnostic imaging. Your task is to analyze the given medical image and provide a detailed, structured, and professional analysis. Follow these instructions carefully:

### Analysis Requirements:
1. **Image Type and Region**:
   - Identify the type of medical imaging (e.g., X-ray, MRI, CT scan, ultrasound).
   - Specify the anatomical region visible in the image (e.g., chest, abdomen, brain, etc.).

2. **Key Findings**:
   - List all visible findings systematically.
   - Describe the appearance of each finding (e.g., size, shape, location, density, texture).
   - Highlight any abnormalities or areas of concern.

3. **Potential Diagnoses**:
   - Provide a list of potential diagnoses based on the findings.
   - Rank the diagnoses by likelihood, with reasoning for each.
   - Include differential diagnoses if applicable.

4. **Detailed Explanation of the image**:
   - Explain what is happening in the medical image provided to the user in simple terms instead of complex medical terms. Make sure he understands everything from first principles in detail.

5. **Image Severity Assessment**:
   - Assess the Severity of the image (e.g., Normal, Mild, Moderate, Severe).
   - Evaluate the positioning of the patient or device (e.g., proper alignment, coverage of the region of interest).

6. **Additional Observations**:
   - Use the Tool Duckduckgo and search the web to provide any other important information regarding the image, such as must know facts, historical news of image artifacts, technical issues, or unusual features.

### Ethical and Safety Guidelines:
1. **Transparency**:
   - If uncertain about any findings, clearly state the limitations of the analysis.
   - Avoid making definitive clinical judgments. Your analysis is for informational purposes only and should be reviewed by a qualified healthcare professional.

2. **Disclaimer**:
   - Include a disclaimer stating that your analysis is for informational purposes only and should not replace professional medical advice.

YOU MUST FOLLOW THIS STRUCTURE AND PROVIDE A COMPREHENSIVE ANALYSIS FOR EACH SECTION.
"""

with st.sidebar:
    st.title("ℹ️ Medical Imaging Analysis")
    
    if not st.session_state.GOOGLE_API_KEY:
        api_key = st.text_input(
            "Enter your Google API Key:"
        )
        st.caption(
            "Get your API key from [Google AI Studio]"
            "(https://aistudio.google.com/apikey) 🔑"
        )
        if api_key:
            st.session_state.GOOGLE_API_KEY = api_key
            st.success("API Key saved!")
            st.rerun()
    else:
        st.success("API Key is configured")
        if st.button("🔄 Reset API Key"):
            st.session_state.GOOGLE_API_KEY = None
            st.rerun()
    
    st.info(
        "This tool provides AI-powered analysis of medical imaging data using "
        "advanced computer vision and radiological expertise."
    )
    st.warning(
        "⚠️ DISCLAIMER: This tool is for educational and informational purposes only. "
        "All analyses should be reviewed by qualified healthcare professionals. "
        "Do not make medical decisions based solely on this analysis."
    )

st.title("🏥 Medical Imaging Diagnosis Assistant")

upload_container = st.container()
with upload_container:
    uploaded_file = st.file_uploader(
        "Upload a medical image for analysis",
        type=["jpg", "jpeg", "png", "dicom"],
        help="Supported formats: JPG, JPEG, PNG, DICOM"
    )

if uploaded_file:
    preview_container = st.container()
    analysis_container = st.container()
    
    with preview_container:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            image = Image.open(uploaded_file)
            width, height = image.size
            aspect_ratio = width / height
            
            max_width = 800
            new_width = min(width, max_width)
            new_height = int(new_width / aspect_ratio)
            resized_image = image.resize((new_width, new_height))
            
            st.image(
                resized_image, 
                caption="Uploaded Medical Image", 
                use_container_width=True
            )
            
            st.write("")
            
            analyze_button = st.button(
                "🔍 Analyze Image", 
                type="primary", 
                use_container_width=True
            )

    with analysis_container:
        if analyze_button:
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                try:
                    temp_file.write(uploaded_file.getbuffer())
                    image_path = temp_file.name

                    with st.spinner("🔄 Analyzing image... Please wait."):
                        response = medical_agent.run(MEDICAL_ANALYSIS_PROMPT, images=[image_path])

                        with st.expander("📋 Detailed Analysis Report", expanded=True):
                            st.markdown("""---""") 
                            st.markdown(response.content)
                            st.markdown("""---""") 
                            st.caption(
                                "Note: This analysis is generated by AI and should be reviewed by a qualified "
                                "healthcare professional before making any medical decisions."
                            )
                
                finally:
                    if os.path.exists(temp_file.name):
                        os.remove(temp_file.name)
else:
    st.info("👆 Please upload a medical image to begin analysis and fill in the API key in the sidebar")