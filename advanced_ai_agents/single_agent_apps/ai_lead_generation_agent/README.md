## 🎯 AI Lead Generation Agent - Powered by Firecrawl's Extract Endpoint

The AI Lead Generation Agent automates the process of finding and qualifying potential leads from Quora. It uses Firecrawl's search and the new Extract endpoint to identify relevant user profiles, extract valuable information, and organize it into a structured format in Google Sheets. This agent helps sales and marketing teams efficiently build targeted lead lists while saving hours of manual research.

### Features
- **Targeted Search**: Uses Firecrawl's search endpoint to find relevant Quora URLs based on your search criteria
- **Intelligent Extraction**: Leverages Firecrawl's new Extract endpoint to pull user information from Quora profiles
- **Automated Processing**: Formats extracted user information into a clean, structured format
- **Google Sheets Integration**: Automatically creates and populates Google Sheets with lead information
- **Customizable Criteria**: Allows you to define specific search parameters to find your ideal leads for your niche

### How to Get Started
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_lead_generation_agent
   ```
3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Important thing to do in composio**:
    - in the terminal, run this command: `composio add googlesheets`
    - In your compposio dashboard, create a new google sheet intergation and make sure it is active in the active integrations/connections tab

5. **Set up your API keys**:
   - Get your Firecrawl API key from [Firecrawl's website](https://www.firecrawl.dev/app/api-keys)
   - Get your Composio API key from [Composio's website](https://composio.ai)
   - Get your OpenAI API key from [OpenAI's website](https://platform.openai.com/api-keys)

6. **Run the application**:
   ```bash
   streamlit run ai_lead_generation_agent.py
   ```

