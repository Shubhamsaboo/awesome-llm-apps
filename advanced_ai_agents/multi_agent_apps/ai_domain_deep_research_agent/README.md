# 🔍 AI Domain Deep Research Agent

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-domain-deep-research-agent) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

An advanced AI research agent built using the Agno Agent framework, Together AI's Qwen model, and Composio tools. This agent helps users conduct comprehensive research on any topic by generating research questions, finding answers through multiple search engines, and compiling professional reports with Google Docs integration.

## Features

- 🧠 **Intelligent Question Generation**:

  - Automatically generates 5 specific research questions about your topic
  - Tailors questions to your specified domain
  - Focuses on creating yes/no questions for clear research outcomes
- 🔎 **Multi-Source Research**:

  - Uses Tavily Search for comprehensive web results
  - Leverages Perplexity AI for deeper analysis
  - Combines multiple sources for thorough research
- 📊 **Professional Report Generation**:

  - Compiles research findings into a McKinsey-style report
  - Structures content with executive summary, analysis, and conclusion
  - Creates a Google Doc with the complete report
- 🖥️ **User-Friendly Interface**:

  - Clean Streamlit UI with intuitive workflow
  - Real-time progress tracking
  - Expandable sections to view detailed results

## How to Run

1. **Setup Environment**

   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_domain_deep_research_agent

   # Install dependencies
   pip install -r requirements.txt

   composio add googledocs
   composio add perplexityai
   ```
2. **Configure API Keys**

   - Get Together AI API key from [Together AI](https://together.ai)
   - Get Composio API key from [Composio](https://composio.ai)
   - Add these to a `.env` file or enter them in the app sidebar
3. **Run the Application**

   ```bash
   streamlit run ai_domain_deep_research_agent.py
   ```

## Usage

1. Launch the application using the command above
2. Enter your Together AI and Composio API keys in the sidebar
3. Input your research topic and domain in the main interface
4. Click "Generate Research Questions" to create specific questions
5. Review the questions and click "Start Research" to begin the research process
6. Once research is complete, click "Compile Final Report" to generate a professional report
7. View the report in the app and access it in Google Docs

## Technical Details

- **Agno Framework**: Used for creating and orchestrating AI agents
- **Together AI**: Provides the Qwen 3 235B model for advanced language processing
- **Composio Tools**: Integrates search engines and Google Docs functionality
- **Streamlit**: Powers the user interface with interactive elements

## Example Use Cases

- **Academic Research**: Quickly gather information on academic topics across various disciplines
- **Market Analysis**: Research market trends, competitors, and industry developments
- **Policy Research**: Analyze policy implications and historical context
- **Technology Evaluation**: Research emerging technologies and their potential impact

## Dependencies

- agno
- composio_agno
- streamlit
- python-dotenv

## License

This project is part of the awesome-llm-apps collection and is available under the MIT License.
