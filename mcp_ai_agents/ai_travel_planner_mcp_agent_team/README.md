# 🌍 AI Travel Planner — MCP Agent Team (Airbnb, Google Maps, Weather)

This project is a *multi-agent travel planning assistant* built using [Agno](https://github.com/agnodice/agno), powered by multiple [Model Context Protocol (MCP)](https://modelcontextprotocol.org/) tools. It integrates:

•⁠  ⁠🏠 *Airbnb Listings*  
•⁠  ⁠🗺️ *Google Maps for routing and places*  
•⁠  ⁠🌦️ *Weather information via AccuWeather*  
•⁠  ⁠📅 (Optional) *Google Calendar integration via Gumloop MCP*

All handled through a simple terminal interface powered by Python + asyncio.

---

## ⚙️ Requirements

•⁠  ⁠Python 3.10+
•⁠  ⁠Node.js + ⁠ npx ⁠
•⁠  ⁠[uvx](https://github.com/uvx/cli) for running MCP servers from Git
•⁠  ⁠Internet access for MCP calls

---

## 📦 Installation

1.⁠ ⁠*Clone the repo*

⁠ bash
git clone https://github.com/yourusername/ai-travel-planner.git
cd ai-travel-planner
 ⁠

2.⁠ ⁠*Create Virtual Env*

conda create -n env_name python=3.10 -y
conda activate env_name
pip install -r requirements.txt


3.⁠ ⁠*Create env file*

GOOGLE_MAPS_API_KEY=your_google_maps_api_key
ACCUWEATHER_API_KEY=your_accuweather_api_key
OPENAI_API_KEY=your_openai_api_key


---

## 🧠 Built With
-- Agno

-- FastMCP

-- OpenAI

-- Google Maps Platform

-- Airbnb MCP

-- Accuweather