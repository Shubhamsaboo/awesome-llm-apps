### AI Email GTM Outreach Agent

An end-to-end, multi-agent Streamlit app that automates B2B outreach using GPT-5 and Exa. It discovers relevant companies, finds the right contacts (Founder's Office, GTM/Sales leadership, Partnerships/BD, Product Marketing), researches website + Reddit insights, and drafts tailored emails in your selected style.

## Features

- **Multi-agent workflow**:
  - **Company Finder**: Uses Exa to discover companies matching your targeting and offering.
  - **Contact Finder**: Finds 2–3 relevant decision makers per company and emails (marks inferred emails clearly if needed).
  - **Researcher**: Pulls 2–4 interesting insights per company from their website and Reddit to enable genuine personalization.
  - **Email Writer**: Uses GPT-5 to produce concise, structured outreach emails.

- **Operator controls**:
  - **Number of companies** to target (1–10)
  - **Email style**: Professional, Casual, Cold, or Consultative
  - Live stage-by-stage progress UI and results with clean section dividers

- **Security-first**:
  - API keys entered in the Streamlit sidebar; not hardcoded or committed

## Requirements

Install dependencies from `requirements.txt`:

```bash
pip install -r advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent/requirements.txt
```

Required environment variables (set via sidebar or your shell):

- `OPENAI_API_KEY`
- `EXA_API_KEY`

## How to Run

```bash
streamlit run advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent/ai_email_gtm_outreach_agent.py
```

## Usage

1. Enter your `OPENAI_API_KEY` and `EXA_API_KEY` in the left sidebar.
2. Provide targeting description and offering.
3. Choose number of companies and an email style.
4. Click “Start Outreach”. Watch the stages: Companies → Contacts → Research → Emails.
5. Review companies, contacts, research insights, and download or copy suggested emails.

## Notes

- The app uses the `gpt-5` model via OpenAI. If unavailable in your account, switch the model in `ai_email_gtm_outreach_agent.py` to one you have access to.
- Exa is used for web discovery; ensure your `EXA_API_KEY` is valid.

## Troubleshooting

- If the app stalls on a stage, verify your API keys and network connectivity.
- If JSON parsing errors occur, rerun the stage; models occasionally add extra text around JSON.
- For rate limits, reduce number of companies.


