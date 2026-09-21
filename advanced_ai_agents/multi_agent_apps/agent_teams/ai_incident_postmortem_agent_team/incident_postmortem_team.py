"""AI Incident Postmortem Agent Team.

Turns raw incident material (alerts, chat logs, deploy history, rough notes) into a
blameless postmortem. Five specialists analyse the incident independently, then an
editor merges their findings into one document.

Built with Swarms. The orchestration topology is selectable at runtime, so you can
see how the same five agents behave under different architectures.
"""

import os
from datetime import datetime

import streamlit as st
from swarms import Agent, ConcurrentWorkflow, MixtureOfAgents, SequentialWorkflow

st.set_page_config(page_title="AI Incident Postmortem Agent Team", layout="wide")

BLAMELESS = (
    "This is a BLAMELESS postmortem. Never name or blame an individual. Where a person "
    "acted, describe the system that made that action reasonable at the time. Assume "
    "everyone acted sensibly given the information they had."
)

SPECIALISTS = {
    "Timeline Reconstructor": (
        "You reconstruct incident timelines. From the raw material, build a precise "
        "chronology: detection, escalation, mitigation, resolution. Mark each entry with "
        "a timestamp where one exists and write 'time unknown' where it does not. Never "
        "invent a timestamp. Separate what happened from when people learned it happened, "
        "because the gap between those two is usually the real finding."
    ),
    "Root Cause Analyst": (
        "You find root causes. Distinguish the trigger (what set it off) from the cause "
        "(the condition that made the trigger harmful). Apply five-whys but stop when you "
        "reach a systemic condition rather than a person. If the evidence does not support "
        "a single root cause, say so and list the candidates with what would confirm each."
    ),
    "Contributing Factors Analyst": (
        "You identify contributing factors: the conditions that made this incident more "
        "likely, harder to detect, or slower to resolve. Look at monitoring gaps, alert "
        "fatigue, missing runbooks, deploy practices, on-call load, and unclear ownership. "
        "These are usually where the durable fixes live."
    ),
    "Blast Radius Analyst": (
        "You quantify impact. Who was affected, how many, for how long, and in what way. "
        "Separate confirmed impact from estimated impact and label which is which. Include "
        "internal impact such as engineer hours consumed. If the raw material does not "
        "support a number, state what data would be needed rather than guessing."
    ),
    "Remediation Planner": (
        "You write action items. Each one must be specific, testable, and assigned to a "
        "role rather than a person. Sort into immediate (stop the bleeding), short term "
        "(prevent recurrence), and long term (remove the class of failure). Reject vague "
        "items like 'improve monitoring'. Say exactly what alert, on what signal, at what "
        "threshold."
    ),
}

EDITOR_PROMPT = (
    "You are an incident postmortem editor. You receive analyses from five specialists. "
    "Merge them into one blameless postmortem in markdown with these sections: Summary, "
    "Impact, Timeline, Root Cause, Contributing Factors, What Went Well, Action Items, "
    "and Open Questions.\n\n"
    "Where specialists disagree, surface the disagreement in Open Questions rather than "
    "averaging it away. Where the raw material was insufficient, say so explicitly. A "
    "postmortem that admits what it does not know is more useful than one that reads as "
    "complete but is quietly guessing.\n\n" + BLAMELESS
)

ARCHITECTURES = {
    "MixtureOfAgents (recommended)": "Specialists analyse independently, editor synthesises.",
    "SequentialWorkflow": "Each specialist builds on the previous one's output.",
    "ConcurrentWorkflow": "All specialists run in parallel, raw output, no synthesis.",
}


def build_specialists(model: str) -> list[Agent]:
    """One agent per analytical lens, each unaware of the others."""
    return [
        Agent(
            agent_name=name,
            agent_description=prompt.split(".")[0],
            system_prompt=f"{prompt}\n\n{BLAMELESS}",
            model_name=model,
            max_loops=1,
        )
        for name, prompt in SPECIALISTS.items()
    ]


def build_editor(model: str) -> Agent:
    return Agent(
        agent_name="Postmortem Editor",
        agent_description="Merges specialist analyses into the final document.",
        system_prompt=EDITOR_PROMPT,
        model_name=model,
        max_loops=1,
    )


def run_team(architecture: str, model: str, task: str) -> str:
    specialists = build_specialists(model)

    if architecture.startswith("MixtureOfAgents"):
        swarm = MixtureOfAgents(
            agents=specialists,
            aggregator_agent=build_editor(model),
            layers=1,
            max_loops=1,
        )
    elif architecture == "SequentialWorkflow":
        swarm = SequentialWorkflow(agents=specialists + [build_editor(model)], max_loops=1)
    else:
        swarm = ConcurrentWorkflow(agents=specialists)

    return str(swarm.run(task))


st.title("🚨 AI Incident Postmortem Agent Team")
st.caption(
    "Paste the raw material from an incident. Five specialists analyse it independently "
    "and an editor writes the blameless postmortem."
)

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    model = st.selectbox(
        "Model",
        ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-6", "gemini/gemini-2.5-pro"],
        help="Any LiteLLM-compatible model. Set the matching provider key above.",
    )

    architecture = st.selectbox("Orchestration", list(ARCHITECTURES.keys()))
    st.caption(ARCHITECTURES[architecture])

    st.divider()
    st.markdown(
        "**Why the topology matters**\n\n"
        "Under `MixtureOfAgents` the five specialists never see each other's work, so their "
        "errors stay uncorrelated and the editor has real disagreement to reconcile. Under "
        "`SequentialWorkflow` each one anchors on the last, which is faster to read but lets "
        "an early wrong conclusion propagate. Same agents, different failure mode."
    )

st.subheader("Incident material")
st.caption("Alerts, chat transcript, deploy log, graphs described in words, rough notes. Messy input is fine.")

incident = st.text_area(
    "Raw material",
    height=280,
    placeholder=(
        "14:02 PagerDuty: checkout-api p99 latency > 3s\n"
        "14:05 oncall ack, dashboards show DB connection pool saturated\n"
        "14:11 someone notes a config change shipped at 13:47\n"
        "14:19 rolled back, latency recovering\n"
        "14:35 fully recovered\n"
        "customer support saw ~40 complaints\n"
        "the pool size was lowered from 100 to 10 by a typo in a values.yaml\n"
        "no alert fired on pool saturation itself, we found it by eye"
    ),
)

col1, col2 = st.columns([1, 4])
with col1:
    run = st.button("Generate postmortem", type="primary")

if run:
    if not api_key:
        st.error("Add an API key in the sidebar.")
    elif not incident.strip():
        st.error("Paste the incident material first.")
    else:
        task = (
            "Produce a blameless postmortem from the following incident material.\n\n"
            "Where the material is silent on something you need, say so explicitly rather "
            "than inferring it.\n\n"
            f"--- INCIDENT MATERIAL ---\n{incident}"
        )
        with st.spinner(f"Running {len(SPECIALISTS)} specialists via {architecture}..."):
            try:
                result = run_team(architecture, model, task)
            except Exception as exc:
                st.error(f"Run failed: {exc}")
            else:
                st.success("Done")
                st.markdown(result)
                st.download_button(
                    "Download as markdown",
                    data=result,
                    file_name=f"postmortem-{datetime.now():%Y-%m-%d-%H%M}.md",
                    mime="text/markdown",
                )
