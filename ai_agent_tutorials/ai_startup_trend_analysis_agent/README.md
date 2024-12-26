## 📈 AI Startup Trend Analysis Agent 
The AI Startup Trend Analysis Agent is tool for budding entrepreneurs that generates actionable insights by identifying nascent trends, potential market gaps, and growth opportunities in specific sectors. Entrepreneurs can use these data-driven insights to validate ideas, spot market opportunities, and make informed decisions about their startup ventures. It combines Newspaper4k and DuckDuckGo to scan and analyze startup-focused articles and market data. Using Claude 3.5 Sonnet, it processes this information to extract emerging patterns and enable entrepreneurs to identify promising startup opportunities.


### Features
- **User Prompt**: Entrepreneurs can input specific startup sectors or technologies of interest for research.
- **News Collection**: This agent gathers recent startup news, funding rounds, and market analyses using DuckDuckGo.
- **Summary Generation**: Concise summaries of verified information are generated using Newspaper4k.
- **Trend Analysis**: The system identifies emerging patterns in startup funding, technology adoption, and market opportunities across analyzed stories.
- **Streamlit UI**: The application features a user-friendly interface built with Streamlit for easy interaction.

### How to Get Started
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git 
   cd awesome-llm-apps/ai_agent_tutorials/ai_startup_trend_analysis_agent
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # For macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # For Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   streamlit run startup_trends_agent.py
   ```
### Important Note
- The system specifically uses Claude's API for advanced language processing. You can obtain your Anthropic API key from [Anthropic's website](https://www.anthropic.com/api).


