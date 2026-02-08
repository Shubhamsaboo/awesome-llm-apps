"""
Multi-Agent AI App with Shared Memory using Aegis Memory

Demonstrates multi-agent coordination with scope-aware memory.
Three agents (Researcher, Analyst, Writer) collaborate using
private, shared, and global memory scopes.
"""

import streamlit as st
from openai import OpenAI
from aegis_memory import AegisClient
from datetime import datetime

st.set_page_config(page_title="Multi-Agent Memory Demo", page_icon="🧠", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_log" not in st.session_state:
    st.session_state.memory_log = []

with st.sidebar:
    st.title("⚙️ Configuration")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    aegis_url = st.text_input("Aegis Memory URL", value="http://localhost:8000")
    st.divider()
    st.markdown("### 📚 Memory Scopes")
    st.markdown("- **Private**: Only the agent can see\n- **Shared**: Specific agents can see\n- **Global**: All agents can see")
    if st.button("🗑️ Clear Memory Log"):
        st.session_state.memory_log = []
        st.rerun()

st.title("🧠 Multi-Agent AI with Shared Memory")

if not openai_api_key:
    st.warning("Please enter your OpenAI API key in the sidebar.")
    st.stop()

llm = OpenAI(api_key=openai_api_key)
memory = AegisClient(api_key="dev-key", base_url=aegis_url)


def log_memory(agent: str, action: str, content: str, scope: str):
    st.session_state.memory_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent, "action": action,
        "content": content[:80] + "..." if len(content) > 80 else content,
        "scope": scope
    })


def call_llm(system: str, user: str, context: str = "") -> str:
    messages = [{"role": "system", "content": system}]
    if context:
        messages.append({"role": "system", "content": f"Context from other agents:\n{context}"})
    messages.append({"role": "user", "content": user})
    return llm.chat.completions.create(model="gpt-4o-mini", messages=messages).choices[0].message.content


def researcher_agent(query: str) -> dict:
    st.markdown("#### 🔬 Researcher Agent")
    with st.spinner("Researching..."):
        findings = call_llm(
            "You are a research agent. Provide 3-5 key findings as bullet points.",
            query
        )
        st.markdown(findings)
        
        # Store in SHARED memory (Analyst can access)
        memory.add(
            content=f"Research on '{query}': {findings}",
            agent_id="researcher",
            scope="agent-shared",
            shared_with_agents=["analyst"]
        )
        log_memory("Researcher", "STORE", findings, "shared → analyst")
        
        # Private notes
        memory.add(content=f"Researched: {query}", agent_id="researcher", scope="private")
        log_memory("Researcher", "STORE", f"Notes on {query}", "private")
        
    return {"findings": findings, "query": query}


def analyst_agent(data: dict) -> dict:
    st.markdown("#### 📊 Analyst Agent")
    with st.spinner("Analyzing..."):
        # Query Researcher's memories
        memories = memory.query_cross_agent(
            query=data["query"],
            requesting_agent_id="analyst",
            target_agent_ids=["researcher"]
        )
        context = "\n".join([m.content for m in memories]) if memories else ""
        log_memory("Analyst", "QUERY", "Cross-agent query to Researcher", "shared")
        
        analysis = call_llm(
            "Provide: 1) Summary (2-3 sentences), 2) Key insights (3 bullets), 3) Recommendations (2 bullets)",
            data["findings"], context
        )
        st.markdown(analysis)
        
        # Store for Writer
        memory.add(
            content=f"Analysis: {analysis}",
            agent_id="analyst",
            scope="agent-shared",
            shared_with_agents=["writer"]
        )
        log_memory("Analyst", "STORE", analysis, "shared → writer")
        
        # Vote on research helpfulness
        if memories:
            memory.vote(memory_id=memories[0].id, outcome="helpful", voter_agent_id="analyst")
            log_memory("Analyst", "VOTE", "Research was helpful", "vote")
        
    return {"analysis": analysis, "query": data["query"]}


def writer_agent(data: dict) -> str:
    st.markdown("#### ✍️ Writer Agent")
    with st.spinner("Writing..."):
        memories = memory.query_cross_agent(
            query=data["query"],
            requesting_agent_id="writer",
            target_agent_ids=["analyst"]
        )
        context = "\n".join([m.content for m in memories]) if memories else ""
        log_memory("Writer", "QUERY", "Cross-agent query to Analyst", "shared")
        
        report = call_llm(
            "Write a concise executive summary (3-5 sentences).",
            data["analysis"], context
        )
        st.markdown(report)
        
        # Store in GLOBAL memory
        memory.add(
            content=f"Report on '{data['query']}': {report}",
            agent_id="writer",
            scope="global"
        )
        log_memory("Writer", "STORE", report, "global")
        
        if memories:
            memory.vote(memory_id=memories[0].id, outcome="helpful", voter_agent_id="writer")
            log_memory("Writer", "VOTE", "Analysis was helpful", "vote")
        
    return report


col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Agent Collaboration")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask the agents to research something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            st.markdown("### 🚀 Multi-Agent Pipeline")
            st.divider()
            research = researcher_agent(prompt)
            st.divider()
            analysis = analyst_agent(research)
            st.divider()
            report = writer_agent(analysis)
            st.divider()
            st.success("✅ Complete!")
        
        st.session_state.messages.append({"role": "assistant", "content": f"**Report:**\n\n{report}"})

with col2:
    st.markdown("### 📊 Memory Log")
    if st.session_state.memory_log:
        for log in reversed(st.session_state.memory_log[-10:]):
            icon = {"private": "🔒", "shared → analyst": "🔄", "shared → writer": "🔄", 
                    "shared": "🔍", "global": "🌐", "vote": "👍"}.get(log["scope"], "📝")
            st.markdown(f"**{log['time']}** | {log['agent']}\n\n{icon} `{log['action']}` ({log['scope']})\n\n_{log['content']}_\n\n---")
    else:
        st.info("Memory actions will appear here...")

st.divider()
st.markdown('<div style="text-align:center;color:#888;">Built with <a href="https://github.com/quantifylabs/aegis-memory">Aegis Memory</a></div>', unsafe_allow_html=True)
