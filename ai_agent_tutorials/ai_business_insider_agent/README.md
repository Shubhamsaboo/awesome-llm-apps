## 📈 AI Business Insider Agent 
The AI Business Insider is a user-friendly news summarization and analysis tool built using the Phidata framework. It leverages built-in tools like Newspaper4k and DuckDuckGo to efficiently retrieve and read articles, creating a detailed report of the emerging trends in that particular sector/industry and also gives potential business opportunities. The application utilizes Anthropic Claude's LLM for advanced language processing, enabling users to gain insights and identify potential business opportunities based on current trends.

### Features
- **User Prompt**: Users can input a topic of interest for research.
- **News Collection**: The system gathers recent news articles using DuckDuckGo based on the provided topic.
- **Summary Generation**: Concise summaries of verified information are generated using Newspaper4k.
- **Trend Analysis**: The system identifies trends and patterns across the analyzed news stories, providing deeper insights for users' potential business ideas.
- **Streamlit UI**: The application features a user-friendly interface built with Streamlit for easy interaction.

### How to Get Started
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git 
   cd ai_agent_tutorials/ai_business_insider_agent
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
   streamlit run business_insider_agent.py
   ```
### Important Note
- The system specifically uses Claude's API for advanced language processing. You can obtain your Anthropic API key from [Anthropic's website](https://www.anthropic.com/api).


