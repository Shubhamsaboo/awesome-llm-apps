import json
import os
import sys
from typing import Any, Dict, List, Optional

import streamlit as st
from agno.agent import Agent
from agno.memory.v2 import Memory
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools


def require_env(var_name: str) -> None:
    if not os.getenv(var_name):
        print(f"Error: {var_name} not set. export {var_name}=...")
        sys.exit(1)


def create_company_finder_agent() -> Agent:
    exa_tools = ExaTools(category="company")
    memory = Memory()
    return Agent(
        model=OpenAIChat(id="gpt-5"),
        tools=[exa_tools],
        memory=memory,
        add_history_to_messages=True,
        num_history_responses=6,
        session_id="gtm_outreach_company_finder",
        show_tool_calls=True,
        instructions=[
            "You are CompanyFinderAgent. Use ExaTools to search the web for companies that match the targeting criteria.",
            "Return ONLY valid JSON with key 'companies' as a list; respect the requested limit provided in the user prompt.",
            "Each item must have: name, website, why_fit (1-2 lines).",
        ],
    )


def create_contact_finder_agent() -> Agent:
    exa_tools = ExaTools()
    memory = Memory()
    return Agent(
        model=OpenAIChat(id="gpt-4o"),
        tools=[exa_tools],
        memory=memory,
        add_history_to_messages=True,
        num_history_responses=6,
        session_id="gtm_outreach_contact_finder",
        show_tool_calls=True,
        instructions=[
            "You are ContactFinderAgent. Use ExaTools to find 1-2 relevant decision makers per company and their emails if available.",
            "Prioritize roles from Founder's Office, GTM (Marketing/Growth), Sales leadership, Partnerships/Business Development, and Product Marketing.",
            "Search queries can include patterns like '<Company> email format', 'contact', 'team', 'leadership', and role titles.",
            "If direct emails are not found, infer likely email using common formats (e.g., first.last@domain), but mark inferred=true.",
            "Return ONLY valid JSON with key 'companies' as a list; each has: name, contacts: [{full_name, title, email, inferred}]",
        ],
    )


def get_email_style_instruction(style_key: str) -> str:
    styles = {
        "Professional": "Style: Professional. Clear, respectful, and businesslike. Short paragraphs; no slang.",
        "Casual": "Style: Casual. Friendly, approachable, first-name basis. No slang or emojis; keep it human.",
        "Cold": "Style: Cold email. Strong hook in opening 2 lines, tight value proposition, minimal fluff, strong CTA.",
        "Consultative": "Style: Consultative. Insight-led, frames observed problems and tailored solution hypotheses; soft CTA.",
    }
    return styles.get(style_key, styles["Professional"])


def create_email_writer_agent(style_key: str = "Professional") -> Agent:
    memory = Memory()
    style_instruction = get_email_style_instruction(style_key)
    return Agent(
        model=OpenAIChat(id="gpt-5"),
        tools=[],
        memory=memory,
        add_history_to_messages=True,
        num_history_responses=6,
        session_id="gtm_outreach_email_writer",
        show_tool_calls=False,
        instructions=[
            "You are EmailWriterAgent. Write concise, personalized B2B outreach emails.",
            style_instruction,
            "Return ONLY valid JSON with key 'emails' as a list of items: {company, contact, subject, body}.",
            "Length: 120-160 words. Include 1-2 lines of strong personalization referencing research insights (company website and Reddit findings).",
            "CTA: suggest a short intro call; include sender company name and calendar link if provided.",
        ],
    )


def create_research_agent() -> Agent:
    """Agent to gather interesting insights from company websites and Reddit."""
    exa_tools = ExaTools()
    memory = Memory()
    return Agent(
        model=OpenAIChat(id="gpt-5"),
        tools=[exa_tools],
        memory=memory,
        add_history_to_messages=True,
        num_history_responses=6,
        session_id="gtm_outreach_researcher",
        show_tool_calls=True,
        instructions=[
            "You are ResearchAgent. For each company, collect concise, valuable insights from:",
            "1) Their official website (about, blog, product pages)",
            "2) Reddit discussions (site:reddit.com mentions)",
            "Summarize 2-4 interesting, non-generic points per company that a human would bring up in an email to show genuine effort.",
            "Return ONLY valid JSON with key 'companies' as a list; each has: name, insights: [strings].",
        ],
    )


def extract_json_or_raise(text: str) -> Dict[str, Any]:
    """Extract JSON from a model response. Assumes the response is pure JSON."""
    try:
        return json.loads(text)
    except Exception as e:
        # Try to locate a JSON block if extra text snuck in
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
        raise ValueError(f"Failed to parse JSON: {e}\nResponse was:\n{text}")


def run_company_finder(agent: Agent, target_desc: str, offering_desc: str, max_companies: int) -> List[Dict[str, str]]:
    prompt = (
        f"Find exactly {max_companies} companies that are a strong B2B fit given the user inputs.\n"
        f"Targeting: {target_desc}\n"
        f"Offering: {offering_desc}\n"
        "For each, provide: name, website, why_fit (1-2 lines)."
    )
    resp = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    companies = data.get("companies", [])
    return companies[: max(1, min(max_companies, 10))]


def run_contact_finder(agent: Agent, companies: List[Dict[str, str]], target_desc: str, offering_desc: str) -> List[Dict[str, Any]]:
    prompt = (
        "For each company below, find 2-3 relevant decision makers and emails (if available). Ensure at least 2 per company when possible, and cap at 3.\n"
        "If not available, infer likely email and mark inferred=true.\n"
        f"Targeting: {target_desc}\nOffering: {offering_desc}\n"
        f"Companies JSON: {json.dumps(companies, ensure_ascii=False)}\n"
        "Return JSON: {companies: [{name, contacts: [{full_name, title, email, inferred}]}]}"
    )
    resp = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("companies", [])


def run_research(agent: Agent, companies: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    prompt = (
        "For each company, gather 2-4 interesting insights from their website and Reddit that would help personalize outreach.\n"
        f"Companies JSON: {json.dumps(companies, ensure_ascii=False)}\n"
        "Return JSON: {companies: [{name, insights: [string, ...]}]}"
    )
    resp = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("companies", [])


def run_email_writer(agent: Agent, contacts_data: List[Dict[str, Any]], research_data: List[Dict[str, Any]], offering_desc: str, sender_name: str, sender_company: str, calendar_link: Optional[str]) -> List[Dict[str, str]]:
    prompt = (
        "Write personalized outreach emails for the following contacts.\n"
        f"Sender: {sender_name} at {sender_company}.\n"
        f"Offering: {offering_desc}.\n"
        f"Calendar link: {calendar_link or 'N/A'}.\n"
        f"Contacts JSON: {json.dumps(contacts_data, ensure_ascii=False)}\n"
        f"Research JSON: {json.dumps(research_data, ensure_ascii=False)}\n"
        "Return JSON with key 'emails' as a list of {company, contact, subject, body}."
    )
    resp = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("emails", [])


def run_pipeline(target_desc: str, offering_desc: str, sender_name: str, sender_company: str, calendar_link: Optional[str], num_companies: int):
    company_agent = create_company_finder_agent()
    contact_agent = create_contact_finder_agent()
    research_agent = create_research_agent()

    companies = run_company_finder(company_agent, target_desc, offering_desc, max_companies=num_companies)
    contacts_data = run_contact_finder(contact_agent, companies, target_desc, offering_desc) if companies else []
    research_data = run_research(research_agent, companies) if companies else []
    return {
        "companies": companies,
        "contacts": contacts_data,
        "research": research_data,
        "emails": [],
    }


def main() -> None:
    st.set_page_config(page_title="GTM B2B Outreach", layout="wide")

    # Sidebar: API keys
    st.sidebar.header("API Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    exa_key = st.sidebar.text_input("Exa API Key", type="password", value=os.getenv("EXA_API_KEY", ""))
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if exa_key:
        os.environ["EXA_API_KEY"] = exa_key

    if not openai_key or not exa_key:
        st.sidebar.warning("Enter both API keys to enable the app")

    # Inputs
    st.title("GTM B2B Outreach Multi Agent Team")
    st.info(
        "GTM teams often need to reach out for demos and discovery calls, but manual research and personalization is slow. "
        "This app uses GPT-5 with a multi-agent workflow to find target companies, identify contacts, research genuine insights (website + Reddit), "
        "and generate tailored outreach emails in your chosen style."
    )
    col1, col2 = st.columns(2)
    with col1:
        target_desc = st.text_area("Target companies (industry, size, region, tech, etc.)", height=100)
        offering_desc = st.text_area("Your product/service offering (1-3 sentences)", height=100)
    with col2:
        sender_name = st.text_input("Your name", value="Sales Team")
        sender_company = st.text_input("Your company", value="Our Company")
        calendar_link = st.text_input("Calendar link (optional)", value="")
        num_companies = st.number_input("Number of companies", min_value=1, max_value=10, value=5)
        email_style = st.selectbox(
            "Email style",
            options=["Professional", "Casual", "Cold", "Consultative"],
            index=0,
            help="Choose the tone/format for the generated emails",
        )

    if st.button("Start Outreach", type="primary"):
        # Validate
        if not openai_key or not exa_key:
            st.error("Please provide API keys in the sidebar")
        elif not target_desc or not offering_desc:
            st.error("Please fill in target companies and offering")
        else:
            # Stage-by-stage progress UI
            progress = st.progress(0)
            stage_msg = st.empty()
            details = st.empty()
            try:
                # Prepare agents
                company_agent = create_company_finder_agent()
                contact_agent = create_contact_finder_agent()
                research_agent = create_research_agent()
                email_agent = create_email_writer_agent(email_style)

                # 1. Companies
                stage_msg.info("1/4 Finding companies...")
                companies = run_company_finder(
                    company_agent,
                    target_desc.strip(),
                    offering_desc.strip(),
                    max_companies=int(num_companies),
                )
                progress.progress(25)
                details.write(f"Found {len(companies)} companies")

                # 2. Contacts
                stage_msg.info("2/4 Finding contacts (2–3 per company)...")
                contacts_data = run_contact_finder(
                    contact_agent,
                    companies,
                    target_desc.strip(),
                    offering_desc.strip(),
                ) if companies else []
                progress.progress(50)
                details.write(f"Collected contacts for {len(contacts_data)} companies")

                # 3. Research
                stage_msg.info("3/4 Researching insights (website + Reddit)...")
                research_data = run_research(research_agent, companies) if companies else []
                progress.progress(75)
                details.write(f"Compiled research for {len(research_data)} companies")

                # 4. Emails
                stage_msg.info("4/4 Writing personalized emails...")
                emails = run_email_writer(
                    email_agent,
                    contacts_data,
                    research_data,
                    offering_desc.strip(),
                    sender_name.strip() or "Sales Team",
                    sender_company.strip() or "Our Company",
                    calendar_link.strip() or None,
                ) if contacts_data else []
                progress.progress(100)
                details.write(f"Generated {len(emails)} emails")

                st.session_state["gtm_results"] = {
                    "companies": companies,
                    "contacts": contacts_data,
                    "research": research_data,
                    "emails": emails,
                }
                stage_msg.success("Completed")
            except Exception as e:
                stage_msg.error("Pipeline failed")
                st.error(f"{e}")

    # Show results if present
    results = st.session_state.get("gtm_results")
    if results:
        companies = results.get("companies", [])
        contacts = results.get("contacts", [])
        research = results.get("research", [])
        emails = results.get("emails", [])

        st.subheader("Top target companies")
        if companies:
            for idx, c in enumerate(companies, 1):
                st.markdown(f"**{idx}. {c.get('name','')}**  ")
                st.write(c.get("website", ""))
                st.write(c.get("why_fit", ""))
        else:
            st.info("No companies found")
        st.divider()

        st.subheader("Contacts found")
        if contacts:
            for c in contacts:
                st.markdown(f"**{c.get('name','')}**")
                for p in c.get("contacts", [])[:3]:
                    inferred = " (inferred)" if p.get("inferred") else ""
                    st.write(f"- {p.get('full_name','')} | {p.get('title','')} | {p.get('email','')}{inferred}")
        else:
            st.info("No contacts found")
        st.divider()

        st.subheader("Research insights")
        if research:
            for r in research:
                st.markdown(f"**{r.get('name','')}**")
                for insight in r.get("insights", [])[:4]:
                    st.write(f"- {insight}")
        else:
            st.info("No research insights")
        st.divider()

        st.subheader("Suggested Outreach Emails")
        if emails:
            for i, e in enumerate(emails, 1):
                with st.expander(f"{i}. {e.get('company','')} → {e.get('contact','')}"):
                    st.write(f"Subject: {e.get('subject','')}")
                    st.text(e.get("body", ""))
        else:
            st.info("No emails generated")


if __name__ == "__main__":
    main()


