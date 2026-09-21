## 🚨 AI Incident Postmortem Agent Team

Paste the mess you have after an outage (alerts, chat transcript, deploy log, half-remembered notes) and get back a blameless postmortem. Five specialist agents analyse the incident independently and an editor merges their findings into one document.

Built with [Swarms](https://github.com/kyegomez/swarms). The orchestration topology is selectable in the UI, so you can watch the same five agents behave differently under different architectures.

### Features

- **Five analytical lenses, run independently**
    - Timeline Reconstructor separates what happened from when people learned it happened
    - Root Cause Analyst distinguishes the trigger from the condition that made it harmful
    - Contributing Factors Analyst finds the monitoring gaps and ownership ambiguity
    - Blast Radius Analyst quantifies impact and labels confirmed versus estimated
    - Remediation Planner writes action items specific enough to be testable
- **Blameless by construction.** Every agent is instructed to describe the system that made an action reasonable rather than the person who took it.
- **Admits uncertainty.** Agents are told to say what the material does not support instead of filling gaps with plausible fiction. Disagreements between specialists surface in an Open Questions section rather than being averaged away.
- **Swappable orchestration.** Choose `MixtureOfAgents`, `SequentialWorkflow` or `ConcurrentWorkflow` and compare. Under MixtureOfAgents the specialists never see each other's work, so their errors stay uncorrelated. Under SequentialWorkflow each anchors on the last, which reads more coherently but lets an early wrong conclusion propagate.
- **Model agnostic.** Swarms routes through LiteLLM, so GPT, Claude and Gemini all work with the same code.
- **Markdown export** for pasting straight into your incident tracker.

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_incident_postmortem_agent_team
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) and obtain your API key.
- Any other LiteLLM-supported provider works too. Pick the matching model in the sidebar and set that provider's key.

4. Run the Streamlit App

```bash
streamlit run incident_postmortem_team.py
```

### How it works

1. **Independent analysis.** The raw incident material goes to all five specialists at once. None of them sees another's output, which is deliberate: correlated agents produce correlated blind spots.
2. **Synthesis.** The editor receives all five analyses and writes the postmortem: Summary, Impact, Timeline, Root Cause, Contributing Factors, What Went Well, Action Items, Open Questions.
3. **Disagreement is preserved.** Where two specialists reach different conclusions, the editor reports both in Open Questions instead of picking one. A postmortem that names its uncertainty is more useful than one that reads as complete but is quietly guessing.

### Why a team instead of one agent

A single agent asked for a postmortem tends to produce a fluent narrative that commits early to one root cause and then rationalises everything else to fit. Splitting the work forces the question to be asked five different ways before anything is written down, and the editor has to reconcile genuine disagreement rather than a single confident story.

Switch the sidebar to `SequentialWorkflow` and run the same incident to see the difference directly. The sequential output usually reads better and is more often wrong in the same direction throughout.
