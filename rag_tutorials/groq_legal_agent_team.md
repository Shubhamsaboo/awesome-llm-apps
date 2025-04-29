🧠 Free Legal Agent Team Using Groq (Instead of OpenAI)

This tutorial shows how to build a fully functioning legal AI multi-agent system using Groq — without needing to pay for OpenAI tokens.

✅ Works with awesome-llm-apps by Unwind AI
✅ Up to 6,000 tokens/min free via Groq
✅ Customizable legal agents (compliance, risk, drafting, etc.)

🔄 Why Swap Out OpenAI?

The default setup in most awesome-llm-apps projects uses OpenAI's GPT-4 or 3.5 models, but:

🔒 Requires API key & payment

🚫 Rate limits apply fast (especially on multi-agent setups)

By switching to Groq's hosted LLaMA 3 model (llama3-8b-8192), we avoid paywalls and unlock free agent usage.

⚙️ How To Swap OpenAI for Groq

1. Replace OpenAI imports with Groq:

from groq import Groq

2. Update the client to use Groq:

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

3. Swap the model name in .create():

model="llama3-8b-8192"

➡️ Done! You're now using Groq’s free hosted model instead of OpenAI.

🧠 What the Legal Agent Team Does

We used a modified version of the legal_agent_team.py file in the multi_agent_apps folder to:

Extract text from uploaded legal documents (PDF)

Run 4 specialized AI agents in parallel:

Agent Role

Purpose

Contract Analyst

Lists key obligations, deadlines, and SEC risk factors

Legal Strategist

Checks compatibility with 3(c)(1) exemption and integration doctrine

Legal Researcher

Provides citations or legal authority for compliance points

Clause Generator

Suggests clause enhancements based on investment club law

All results are displayed in real-time in Streamlit, under expandable tabs.

💡 Real-World Use Case: SEC 3(c)(1) Exemption

The custom agents were trained to:

Review contracts for private investment clubs

Ensure no more than 100 members, no public advertisement

Flag potential violations of the SEC integration doctrine

Example input:

Upload: DPVIP Compliance MOU

Agent output:

"Section 3(a) may conflict with SEC rules under 3(c)(1). Consider redrafting..."

🚀 How to Run It

Fork this repo

Paste the updated legal_agent_team.py (linked below)

Run the app:

streamlit run legal_agent_team.py

Upload a PDF

Review the outputs from each legal agent

📦 Files Updated

multi_agent_apps/agent_teams/legal_agent_team.py ✅ Updated for Groq

.env file with your Groq API key

✅ Try It Live

Grab your free Groq key from https://console.groq.com/ and you're good to go!

🙋‍♀️ Built by @Kbryan5393 for Unwind AI

Open-source AI that actually works for legal + compliance professionals.

Pull request welcome 💬

