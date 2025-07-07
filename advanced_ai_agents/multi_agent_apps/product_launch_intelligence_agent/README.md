# 🚀 AI Product Launch Intelligence Agent

A **streamlined intelligence hub** for Go-To-Market (GTM) & Product-Marketing teams.  
Built with **Streamlit + Agno (GPT-4o) + Firecrawl**, the app turns scattered public-web data into concise, actionable launch insights.

## 3 Specialized Agents

| Tab | What You Get |
|-----|--------------|
| **Competitor Analysis Agent** | Evidence-backed breakdown of a rival's latest launches – positioning, differentiators, pricing cues & channel mix |
| **Market Sentiment Agent** | Consolidated social chatter & review themes split by 🚀 *positive* / ⚠️ *negative* drivers |
| **Launch Metrics Agent** | Publicly available KPIs – adoption numbers, press coverage, qualitative "buzz" signals |

Additional goodies:

* 🔑 **Sidebar key input** – enter OpenAI & Firecrawl keys securely (type="password")
* 🧠 **Specialised multi-agent core** – three expert agents collaborate for richer insight
  * 🔍 Product Launch Analyst (GTM strategist)
  * 💬 Market Sentiment Specialist (consumer-perception guru)
  * 📈 Launch Metrics Specialist (performance analyst)
* ⚡ **Quick actions** – press **J/K/L** to trigger the three analyses without touching the UI
* 📑 **Auto-formatted Markdown reports** – bullet summary first, then expanded deep-dive
* 🛠️ **Sources section** – every report ends with the URLs that were crawled or searched

## 🛠️ Tech Stack

| Layer | Details |
|-------|---------|
| Data | **Firecrawl** async search + crawl API |
| Agents | **Agno** (GPT-4o) with FirecrawlTools |
| UI | **Streamlit** wide-layout, tabbed workflow |
| LLM | **OpenAI GPT-4o** |

## 🚀 Quick Start

1. **Clone** the repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent
```

2. **Install** dependencies

```bash
pip install -r requirements.txt
```

3. **Provide API keys** (choose either option)

   • **Environment variables** – create a `.env` file:
   ```ini
   OPENAI_API_KEY=sk-************************
   FIRECRAWL_API_KEY=fc-************************
   ```
   • **In-app sidebar** – paste the keys into the secure text inputs

4. **Run the app**

```bash
streamlit run product_launch_intelligence_agent.py
```

5. **Browse** to <http://localhost:8501> – you should see three analysis tabs.

## 🕹️ Using the Application

1. Enter **API keys** in the sidebar (or ensure they are in your environment).
2. Type a **company / product / hashtag** in the main input box.
3. Pick a tab and hit the corresponding **Analyze** button – a spinner will appear while the agent works.
4. Review the two-part analysis:
   * Bullet list of key findings
   * Expanded, richly-formatted report (tables, call-outs, recommendations)
