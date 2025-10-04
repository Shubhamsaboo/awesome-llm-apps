# 🛡️ Life Insurance Coverage Advisor Agent

A Streamlit application that helps users estimate the amount of term life insurance they may need and surfaces currently available policy options. The app is powered by the [Agno](https://github.com/agno-agi/agno) agent framework, uses **Grok 4 Fast (via OpenRouter)** as the reasoning model, the **E2B** sandbox for deterministic coverage calculations, and **Firecrawl** for live web research.

## Highlights
- Minimal intake form (age, income, dependents, debt, assets, existing cover, horizon, location).
- The agent runs Python code inside an E2B sandbox to calculate coverage with a discounted cash-flow style income replacement model.
- Firecrawl search is used to gather the latest term-life products for the user’s geography and coverage needs.
- Returns a concise coverage estimate, calculation breakdown, and up to three product suggestions with source links.

## Prerequisites
You will need API keys for each external service:

| Service | Purpose | Where to get it |
| --- | --- | --- |
| OpenRouter (Grok 4 Fast) | Core reasoning model | https://openrouter.ai/keys |
| Firecrawl | Web search + crawl tooling | https://www.firecrawl.dev/app/api-keys |
| E2B | Secure code execution sandbox | https://e2b.dev |

> ℹ️ OpenRouter recommends setting the `HTTP-Referer` and `X-Title` headers on every request. The app defaults to
> `https://github.com/Shubhamsaboo/awesome-llm-apps` and `Life Insurance Coverage Advisor`, but you can override them
> by exporting `OPENROUTER_REFERRER` and `OPENROUTER_TITLE` before launching Streamlit.

## Installation
1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```
2. Create and activate a virtual environment (optional but recommended).

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run life_insurance_advisor.py
   ```

## Using the App
1. Enter your OpenRouter, Firecrawl, and E2B API keys in the sidebar (keys are kept in the local Streamlit session).
2. Provide the requested financial information and choose an income replacement horizon.
3. Click **Generate Coverage & Options** to launch the Agno agent workflow.
4. Review the recommended coverage, rationale, and suggested insurers. Raw agent output is available in an expander for debugging.

## Disclaimer
This project is for educational and prototyping purposes only and does **not** provide licensed financial advice. Always validate the output with a qualified professional and confirm details directly with insurance providers.
