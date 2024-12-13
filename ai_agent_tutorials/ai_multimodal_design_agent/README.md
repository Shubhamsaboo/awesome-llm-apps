# Multimodal AI Design Agent Team

A multimodal design analysis tool powered by Google's Gemini 2.0 multimodal capabilities. This application leverages multiple specialized AI agents to provide comprehensive analysis of UI/UX designs of your product and your competitors, combining visual understanding, user experience evaluation, and market research insights.

## Demo


## About

The Design Agent Team utilizes Gemini 2.0's advanced multimodal capabilities to analyze design assets from multiple perspectives:

- 🎨 **Visual Design Analysis**: Evaluates design elements, patterns, color schemes, typography, and visual hierarchy
- 🔄 **UX Analysis**: Assesses user flows, interaction patterns, usability, and accessibility
- 📊 **Market Analysis**: Provides market insights, competitor analysis, and positioning recommendations

## Features

- **Multiple Analysis Types**: Choose from Visual Design, UX, and Market Analysis
- **Comparative Analysis**: Upload competitor designs for comparative insights
- **Customizable Focus Areas**: Select specific aspects for detailed analysis
- **Context-Aware**: Provide additional context for more relevant insights
- **Real-time Processing**: Get instant analysis with progress indicators
- **Structured Output**: Receive well-organized, actionable insights

## How to Run

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_multimodal_design_agent

   # Create and activate virtual environment (optional)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Get API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create or select a project
   - Generate an API key

3. **Run the Application**
   ```bash
   streamlit run design_agent_team.py
   ```

4. **Use the Application**
   - Enter your Gemini API key in the sidebar
   - Upload design files (supported formats: JPG, JPEG, PNG)
   - Select analysis types and focus areas
   - Add context if needed
   - Click "Run Analysis" to get insights


## Technical Stack

- **Frontend**: Streamlit
- **AI Model**: Google Gemini 2.0
- **Image Processing**: Pillow
- **Market Research**: DuckDuckGo Search API
- **Framework**: Phidata for agent orchestration

## Tips for Best Results

- Upload clear, high-resolution images
- Include multiple views/screens for better context
- Add competitor designs for comparative analysis
- Provide specific context about your target audience

