# 🚀 Product Launch Intelligence Agent

A **streamlined intelligence hub** for Go-To-Market (GTM) & Product-Marketing teams.  
Built with **Agno + Firecrawl + Streamlit**, the app turns scattered public-web data into concise, actionable launch insights.


## 🎯 Core Use-Cases

| Tab | What You Get |
|-----|--------------|
| **Competitor Analysis** | GTM-focused breakdown of a rival's latest launches – key messaging, differentiators, pricing cues & launch channels |
| **Market Sentiment** | Consolidated review themes & social chatter split by 🚀 *positive* / ⚠️ *negative* drivers |
| **Launch Metrics** | Publicly available KPIs – press coverage, engagement numbers, qualitative "buzz" signals |


Responses are neatly rendered in markdown with a two-step process:
1. First, a concise bullet list of key findings
2. Then, an expanded 1200-word analysis with executive summary, deep dive, and recommendations


## 🛠️ Tech Stack

| Layer | Details |
|-------|---------|
| Data | **Firecrawl** search + crawl (async, poll-based) |
| Agent | **Agno** single-agent with FirecrawlTools & markdown output |
| UI | **Streamlit** wide layout, custom CSS, tabbed workflow |
| LLM | **OpenAI GPT-4o** for analysis and insights |


### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. **Set up API Keys**
   You can provide your API keys in two ways:
   - **Environment Variables**: Add to `.env` file
     ```ini
     OPENAI_API_KEY=sk-************************
     FIRECRAWL_API_KEY=fc-************************
     ```
   - **UI Input**: Enter keys directly in the app's sidebar

3. **Run**
   ```bash
   streamlit run product_launch_intelligence_agent.py
   ```

4. **Navigate** to <http://localhost:8501> and start exploring.


## 🕹️ Using the Application

1. **Enter API Keys** in the sidebar if not set in environment variables
2. Pick a tab (Competitor ▸ Sentiment ▸ Metrics)
3. Enter the **company / product / hashtag** requested
4. Hit **Analyze** – a spinner indicates data gathering
5. Review the two-part analysis:
   - Initial bullet points for quick insights
   - Expanded report with detailed analysis