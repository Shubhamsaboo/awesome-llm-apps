<p align="center">
 <a href="http://www.theunwindai.com">
 <img src="docs/banner/unwind_black.png" width="900px" alt="Unwind AI">
 </a>
</p>

<div align="center">

# Awesome LLM Apps

**100+ open-source AI agents, agent skills, and RAG apps. Hand-built, tested end-to-end, Apache-2.0.**

Clone it, ship it, sell it - 100% free and open-source

Works with Claude, Gemini, GPT, DeepSeek, Llama, Qwen and other open-source models.

**[Step-by-step tutorials on Unwind AI](https://www.theunwindai.com)** \u00b7 **[Quick start](#-run-one-now)** \u00b7 **[Browse all templates](#-browse-all-templates)**

<a href="https://trendshift.io/repositories/9876" target="_blank">
 <img src="https://trendshift.io/api/badge/repositories/9876" width="220" alt="Featured on Trendshift as the #1 repository of the day">
</a>



</div>

<table>
 <tr>
 <td width="33.3%" align="center">
 <a href="agent_skills/project-graveyard/"><img src="docs/gallery/project-graveyard.png" alt="Project Graveyard: an agent that autopsies your dead side projects"></a>
 <sub><b>Project Graveyard</b></sub>
 </td>
 <td width="33.3%" align="center">
 <a href="voice_ai_agents/insurance_claim_live_agent_team/"><img src="docs/gallery/insurance-claim-live-team.png" alt="Insurance Claim Live Agent Team: voice claims settled in real time"></a>
 <sub><b>Insurance Claim Live Agent Team</b></sub>
 </td>
 <td width="33.3%" align="center">
 <a href="advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent/"><img src="docs/gallery/ai-fraud-investigation.png" alt="AI Fraud Investigation Agent: public records, cross-examined"></a>
 <sub><b>AI Fraud Investigation Agent</b></sub>
 </td>
 </tr>
 <tr>
 <td align="center">
 <a href="agent_skills/self-improving-agent-skills/"><img src="docs/gallery/self-improving-agent-skills.png" alt="Self-Improving Agent Skills: skills that rewrite themselves against evals"></a>
 <sub><b>Self-Improving Agent Skills</b></sub>
 </td>
 <td align="center">
 <a href="advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent"><img src="docs/gallery/ai-home-renovation.png" alt="AI Home Renovation Agent: photo in, photoreal redesign out"></a>
 <sub><b>AI Home Renovation Agent</b></sub>
 </td>
 <td align="center">
 <a href="always_on_agents/always_on_hn_briefing_agent/"><img src="docs/gallery/always-on-hn-briefing.png" alt="Always-on HN Briefing Agent: it reads Hacker News while you sleep"></a>
 <sub><b>Always-on HN Briefing Agent</b></sub>
 </td>
 </tr>
</table>

## \ud83d\ude80 Run one now

Give your coding agent a new skill in 10 seconds:

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/project-graveyard
```

Then ask it: *"why do I never finish my side projects?"*

Or clone and run any agent in 30 seconds:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
streamlit run travel_agent.py
```

> \ud83d\udcec New templates drop weekly. [Get them in your inbox on Unwind AI](https://www.theunwindai.com).

## \ud83d\udcc2 Browse all templates

### \ud83e\udde9 Agent Skills

*Give your coding agent new abilities. One command to install, plain English to use. Every skill ships real code and passes a security + eval CI gate. Works with Claude Code, Codex, Cursor, and other coding agents. [Browse all skills \u2192](agent_skills/)*

* [\u26b0\ufe0f Project Graveyard](agent_skills/project-graveyard/) - Finds every side project you abandoned, tells you why each one died, and helps you finish the one worth going back to
* [\ud83d\udd2d Scope Creep Detector](agent_skills/scope-creep-detector/) - Checks whether a diff grew beyond its stated intent and recommends what to keep, split, or justify
* [\ud83c\udffa Commit Archaeologist](agent_skills/commit-archaeologist/) - Reconstructs why a file or code region exists from its introducing commit, later edits, co-changes, and intent clues
* [\ud83e\udeba Dependency Doctor](agent_skills/dependency-doctor/) - Checks a dependency manifest for standard-library pins, obsolete backports, unpinned entries, duplicate constraints, and yanked releases
* [\ud83e\udde0 Advisor Orchestrator Worker](agent_skills/advisor-orchestrator-worker/) - Meta Loop with Claude Fable 5 as advisor, GPT-5.6 as orchestrator, and Gemini 3.5 Flash as worker
* [\u267e\ufe0f Self-Improving Agent Skills](agent_skills/self-improving-agent-skills/) - Automatically optimize agent skills using Gemini and ADK

### \ud83c\udf31 Starter AI Agents

*Single-file agents that run with just an API key - a great place to start.*

* [\ud83c\udf99\ufe0f AI Blog to Podcast Agent](starter_ai_agents/ai_blog_to_podcast_agent/) - Turn any blog URL into a narrated podcast episode
* [\u2764\ufe0f\u200d\ud83e\ude79 AI Breakup Recovery Agent](starter_ai_agents/ai_breakup_recovery_agent/) - An agent team that talks you through the post-breakup spiral
* [\ud83d\udcca AI Data Analysis Agent](starter_ai_agents/ai_data_analysis_agent/) - Ask questions of any CSV or Excel file in plain English
* [\ud83e\udebc AI Medical Imaging Agent](starter_ai_agents/ai_medical_imaging_agent/) - Diagnostic analysis of X-rays and scans with Gemini
* [\ud83d\ude02 AI Meme Generator Agent (Browser)](starter_ai_agents/ai_meme_generator_agent_browseruse/) - Makes memes by driving a real browser, not an image API
* [\ud83c\udfb5 AI Music Generator Agent](starter_ai_agents/ai_music_generator_agent/) - Prompt in, MP3 track out
* [\ud83d\udeeb AI Travel Agent (Local & Cloud)](starter_ai_agents/ai_travel_agent/) - Personalized day-by-day travel itineraries
* [\u2728 Gemini Multimodal Agent](starter_ai_agents/multimodal_ai_agent/) - Video analysis plus web search in one agent
* [\ud83d\udd04 Mixture of Agents](starter_ai_agents/mixture_of_agents/) - Multiple LLMs answer, one aggregates the best response
* [\ud83d\udcca xAI Finance Agent](starter_ai_agents/xai_finance_agent/) - Real-time stock analysis powered by Grok
* [\ud83d\udd0d OpenAI Research Agent](starter_ai_agents/openai_research_agent/) - Multi-agent topic research with the OpenAI Agents SDK
* [\ud83d\udd78\ufe0f Web Scraping AI Agent](starter_ai_agents/web_scraping_ai_agent/) - Describe what to extract and the agent scrapes it

### \ud83d\ude80 Advanced AI Agents

*Production-style agents with tools, memory, and multi-step reasoning.*

* [\ud83c\udfda\ufe0f \ud83c\udf4c AI Home Renovation Agent with Nano Banana Pro](advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent) - Photos of your space in, renovation plan and photorealistic renders out
* [\ud83e\udde0 DevPulse AI - Multi-Agent Signal Intelligence](advanced_ai_agents/multi_agent_apps/devpulse_ai/) - Aggregates and scores technical signals into a daily intelligence digest
* [\ud83d\udd0d AI Deep Research Agent](advanced_ai_agents/single_agent_apps/ai_deep_research_agent/) - Comprehensive web research with the OpenAI Agents SDK and Firecrawl
* [\ud83d\udcca AI VC Due Diligence Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team) - Multi-agent startup investment analysis with Gemini 3
* [\ud83d\udd2c AI Research Planner & Executor (Google Interactions API)](advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api) - Multi-phase research with stateful conversations and auto-generated infographics
* [\ud83e\udd1d AI Consultant Agent](advanced_ai_agents/single_agent_apps/ai_consultant_agent) - Market analysis and strategy recommendations with live web research
* [\ud83c\udfd7\ufe0f AI System Architect Agent](advanced_ai_agents/single_agent_apps/ai_system_architect_r1/) - Architecture reviews using DeepSeek R1 reasoning plus Claude
* [\ud83d\udcb0 AI Financial Coach Agent](advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent/) - Personalized budget, debt, and savings analysis
* [\ud83c\udfac AI Movie Production Agent](advanced_ai_agents/single_agent_apps/ai_movie_production_agent/) - Script drafts and casting ideas from a one-line movie concept
* [\ud83d\udcc8 AI Investment Agent](advanced_ai_agents/single_agent_apps/ai_investment_agent/) - Stock comparison reports built on Yahoo Finance data
* [\ud83d\udce1 Earnings Call Analyst Agent](advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/) - Turns YouTube earnings calls into a playback-synced analyst workspace
* [\ud83c\udfcb\ufe0f\u200d\u2642\ufe0f AI Health & Fitness Agent](advanced_ai_agents/single_agent_apps/ai_health_fitness_agent/) - Tailored diet and workout plans from your goals
* [\ud83d\ude80 AI Product Launch Intelligence Agent](advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent) - Go-to-market intelligence on competitor launches
* [\ud83d\udd0d AI Fraud Investigation Agent](advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent/) - Cross-references public records to flag facilities that don't add up
* [\ud83d\udcf0 AI Journalist Agent](advanced_ai_agents/single_agent_apps/ai_journalist_agent/) - Researches, writes, and edits articles on any topic
* [\ud83e\udde0 AI Mental Wellbeing Agent](advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent/) - A coordinated agent team for mental health support plans
* [\ud83d\udcd1 AI Meeting Agent](advanced_ai_agents/single_agent_apps/ai_meeting_agent/) - Context, industry insights, and strategy briefs before you walk in
* [\ud83e\uddec AI Self-Evolving Agent](advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/) - Agents that rewrite their own workflows with EvoAgentX
* [\ud83d\udc68\ud83c\udffb\u200d\ud83d\udcbc AI Sales Intelligence Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team) - Generates competitive sales battle cards in real time
* [\ud83c\udfa7 AI Social Media News and Podcast Agent](advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/) - Curates your trusted sources into briefs and generated podcasts
* [\ud83c\udf10 Openwork - Open Browser Automation Agent](https://github.com/accomplish-ai/openwork) <sub>\u2197 external</sub> - Open-source agent that operates a real browser
* [\ud83d\udee1\ufe0f Trust-Gated Multi-Agent Research Team](advanced_ai_agents/multi_agent_apps/trust_gated_agent_team/) - Every agent verified, every action in a hash-chained audit trail

### \ud83d\udef0\ufe0f Always-on Agents

*Background agents that run on schedules or events, monitor changing context, decide what needs attention, and proactively deliver updates, artifacts, or actions.*

* [\ud83d\udcf0 Always-on Hacker News Briefing Agent](always_on_agents/always_on_hn_briefing_agent/) - A scheduled scout that ships a ranked daily brief to Slack or email
* [\ud83d\udce1 Release Radar Agent](always_on_agents/release_radar_agent/) - Watches dependency releases and briefs you on breaking, deprecated, security, and major-version changes

### \ud83e\udd1d Multi-agent Teams

*Multiple agents collaborating to accomplish complex, cross-domain tasks.*

* [\ud83e\uddf2 AI Competitor Intelligence Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team/) - Structured competitor teardowns built from their own websites
* [\ud83d\udcb2 AI Finance Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team/) - A financial analyst team in 20 lines of Python
* [\ud83c\udfa8 AI Game Design Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team/) - Full game concepts from a swarm of design specialists
* [\ud83e\udded AG2 Adaptive Research Team](advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team/) - Agent teamwork with routing and fallback, built on AG2
* [\ud83d\udc68\u200d\u2696\ufe0f AI Legal Agent Team (Cloud & Local)](advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team/) - Research, contract analysis, and strategy from a full legal bench
* [\ud83d\udcbc AI Recruitment Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team/) - Resume screening to interview scheduling, end to end
* [\ud83c\udfe0 AI Real Estate Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team) - Property search, market analysis, and recommendations
* [\ud83d\udc68\u200d\ud83d\udcbc AI Services Agency (CrewAI)](advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency/) - A digital agency that scopes and plans your software project
* [\ud83d\udc68\u200d\ud83c\udf93 AI Teaching Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/) - A faculty of agents that builds your complete learning path
* [\ud83d\udcbb Multimodal Coding Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team/) - Snap a photo of a coding problem, get a sandboxed solution
* [\u2728 Multimodal Design Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team/) - Design critiques from a Gemini-powered expert panel
* [\ud83c\udfa8 \ud83c\udf4c Multimodal UI/UX Feedback Agent Team](advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team/) - Landing page feedback plus an auto-generated improved version
* [\ud83c\udf0f AI Travel Planner Agent Team](/advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/) - A complete trip itinerary, crafted by a team

### \ud83d\udde3\ufe0f Voice AI Agents

*Speech-in, speech-out agents using real-time voice APIs.*

* [\ud83d\udde3\ufe0f AI Audio Tour Agent](voice_ai_agents/ai_audio_tour_agent/) - Self-guided audio tours from your location, interests, and pace
* [\ud83d\udcde Customer Support Voice Agent](voice_ai_agents/customer_support_voice_agent/) - Voice answers grounded in your own docs
* [\ud83d\udee1\ufe0f Insurance Claim Live Agent Team](voice_ai_agents/insurance_claim_live_agent_team/) - Real-time voice claim intake with Gemini Live
* [\ud83d\udd0a Voice RAG Agent (OpenAI SDK)](voice_ai_agents/voice_rag_openaisdk/) - Ask your PDFs questions, hear the answers
* [\ud83c\udf99\ufe0f OpenSource Voice Dictation Agent (Wispr Flow clone)](https://github.com/akshayaggarwal99/jarvis-ai-assistant) <sub>\u2197 external</sub> - Open-source dictation that types where you talk

### \ud83d\uddbc\ufe0f Generative UI and Agentic Frontends

*Agents that render interactive UI components, not just text: forms, cards, charts, editable plans.*

* [\ud83d\udcc2 Generative UI Starter Project](generative_ui_agents/generative-ui-starter-project/) - A chat-driven kanban board you and the agent work together
* [\ud83e\ude99 AI Financial Coach Agent](generative_ui_agents/ai-financial-coach-agent/) - Budget, savings, and debt plans rendered as interactive cards
* [\ud83d\udcca AI Dashboard Canvas Agent](generative_ui_agents/ai-dashboard-canvas-agent/) - Describe a dashboard in chat, charts assemble on a live canvas
* [\ud83d\udeed\ufe0f AI MCP App Builder](generative_ui_agents/ai-mcp-app-builder/) - Describe an MCP app, get a live sandboxed instance back
* [\u2708\ufe0f MCP Apps Generative UI Showcase](generative_ui_agents/mcp-apps-generative-ui-showcase/) - MCP apps that render real interactive UI, flight search included
* [\ud83c\udf9b\ufe0f AI Shadcn Component Generator](generative_ui_agents/ai-shadcn-component-generator/) - Chat your way to production-ready shadcn components
* [\ud83d\udd0d AI Deep Research Agent](generative_ui_agents/ai-deep-research-agent/) - Research where every tool call renders as a live workspace card

### \ud83c\udfae Autonomous Game-Playing Agents

*Agents that play games end-to-end: reasoning, strategy, and action.*

* [\ud83c\udfae AI 3D Pygame Agent](advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1/) - DeepSeek R1 writes PyGame code, browser agents run it live
* [\u265c AI Chess Agent](advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent/) - Agent White vs Agent Black with validated moves
* [\ud83c\udfb2 AI Tic-Tac-Toe Agent](advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent/) - Two different LLMs battle it out, move by move

### \u267e\ufe0f MCP AI Agents

*Agents that connect to external tools and data via Model Context Protocol.*

* [\u267e\ufe0f Browser MCP Agent](mcp_ai_agents/browser_mcp_agent/) - Drive a real browser with natural language over MCP
* [\ud83d\udc19 GitHub MCP Agent](mcp_ai_agents/github_mcp_agent/) - Explore and analyze any repo in plain English
* [\ud83d\udcd1 Notion MCP Agent](mcp_ai_agents/notion_mcp_agent) - Talk to your Notion pages from the terminal
* [\ud83c\udf0d AI Travel Planner MCP Agent](mcp_ai_agents/ai_travel_planner_mcp_agent_team) - Itineraries built on live Airbnb and Google Maps data
* [\ud83d\udd00 Multi-MCP Agent Router](mcp_ai_agents/multi_mcp_agent_router/) - Specialist agents, each wired to its own MCP server
* [\ud83d\udd10 NexusGenesis Agent Demo](mcp_ai_agents/nexusgenesis_agent_demo/) - Post-quantum self-custody keys for AI agents, with human takeover

### \ud83d\udcc0 RAG (Retrieval Augmented Generation)

*Retrieval pipelines, from simple chains to agentic and multi-source.*

* [\ud83d\udd25 Agentic RAG with Embedding Gemma](rag_tutorials/agentic_rag_embedding_gemma) - Fully local agentic RAG with EmbeddingGemma and Llama 3.2
* [\ud83e\uddd0 Agentic RAG with Reasoning](rag_tutorials/agentic_rag_with_reasoning/) - Watch the agent's step-by-step reasoning as it retrieveslidated moves\n* [\\ud83c\\udfb2 AI Tic-Tac-Toe Agent](advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent/) - Two different LLMs battle it out, move by move\n\n### \\u267e\\ufe0f MCP AI Agents\n\n*Agents that connect to external tools and data via Model Context Protocol.*\n\n* [\\u267e\\ufe0f Browser MCP Agent](mcp_ai_agents/browser_mcp_agent/) - Drive a real browser with natural language over MCP\n* [\\ud83d\\udc19 GitHub MCP Agent](mcp_ai_agents/github_mcp_agent/) - Explore and analyze any repo in plain English\n* [\\ud83d\\udcd1 Notion MCP Agent](mcp_ai_agents/notion_mcp_agent) - Talk to your Notion pages from the terminal\n* [\\ud83c\\udf0d AI Travel Planner MCP Agent](mcp_ai_agents/ai_travel_planner_mcp_agent_team) - Itineraries built on live Airbnb and Google Maps data\n* [\\ud83d\\udd00 Multi-MCP Agent Router](mcp_ai_agents/multi_mcp_agent_router/) - Specialist agents, each wired to its own MCP server\n* [\\ud83d\\udd10 NexusGenesis Agent Demo](mcp_ai_agents/nexusgenesis_agent_demo/) - Post-quantum self-custody keys for AI agents, with human takeover\n\n### \\ud83d\\udcc0 RAG (Retrieval Augmented Generation)\n\n*Retrieval pipelines, from simple chains to agentic and multi-source.*\n\n* [\\ud83d\\udd25 Agentic RAG with Embedding Gemma](rag_tutorials/agentic_rag_embedding_gemma) - Fully local agentic RAG with EmbeddingGemma and Llama 3.2\n* [\\ud83e\\uddd0 Agentic RAG with Reasoning](rag_tutorials/agentic_rag_with_reasoning/) - Watch the agent's step-by-step reasoning as it retrieves\n"}]