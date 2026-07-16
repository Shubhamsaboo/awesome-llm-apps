# Agentlas OS Agent Operation Environment (AOE) MCP Workforce Finder

A Streamlit tutorial for the Agent Workforce Ontology in the Agentlas OS Agent
Operation Environment (AOE). The app creates a redacted, typed WorkOrder and
uses the remote MCP server to retrieve qualified public agent and team
candidates.

This tutorial follows the public Agentlas OS Agent Operation Environment (AOE)
v1.1.48 workforce contract and pins ontology menu `awo:2026-07-15.2`.

## Features

- Connects to a remote MCP server with the official Python MCP SDK
- Builds an `agentlas.workforce-work-order.v1` object from a role profile
- Retrieves exact agent and team releases with content-fit evidence
- Excludes popularity and usage history from staffing fit
- Requires no API key or Agentlas account for public candidate search

## Architecture

```text
Redacted task brief + typed role profile
  -> Streamlit app creates a WorkOrder
  -> workforce_search_candidates over Streamable HTTP MCP
  -> hard eligibility and content-only candidate retrieval
  -> exact public agent and team release candidates
  -> host LLM makes the staffing decision
```

The Agentlas OS Agent Operation Environment (AOE) does not let the server
choose the final worker, silently substitute one, or run an LLM on the server.
A full workforce run continues with a selection authored by the host LLM,
deterministic validation, and preparation of pinned BYOM runtime bundles. This
tutorial intentionally stops after the public, read-only candidate retrieval
step.

## Setup

### Requirements

- Python 3.10+
- Internet access to the public Agentlas OS Agent Operation Environment (AOE)
  MCP endpoint

### Installation

1. Clone this repository and open the app directory:

   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/agentlas_os_aoe_workforce_finder
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   streamlit run aoe_workforce_finder.py
   ```

4. Select a public role profile, enter a redacted task brief, and select
   **Search workforce**.

## How It Works

The example WorkOrder has one role slot and uses canonical community and skill
identifiers from the pinned ontology menu. Required constraint lists are kept
empty so the tutorial demonstrates broad retrieval; the selected role and
skill are optional content-fit signals. The MCP server still enforces release,
security, entity, runtime, tool, artifact, and authority constraints supplied
by the caller.

The response is an `agentlas.workforce-candidate-set.v1` object containing:

- an expiring selection session and candidate-set digest
- exact definition, release, package, and content identifiers
- fit and qualification evidence
- operational callability and installability
- aggregate coverage gaps
- `decisionOwner: host_llm` and `historyInfluence: none`

Composite tasks should use a host LLM to create multiple role slots and their
handoff or review edges. Deterministic code validates that structure and the
eventual selection, but never makes the staffing decision.

The endpoint defaults to:

```text
https://agentlas.cloud/api/mcp/hephaestus-network
```

Set `AGENTLAS_AOE_MCP_URL` to use another compatible endpoint.

## Learn More

- [Agentlas OS Agent Operation Environment (AOE)](https://github.com/agentlas-ai/Agentlas-OS)
- [Agent Workforce Ontology](https://github.com/agentlas-ai/Agentlas-OS/blob/main/docs/agent-workforce-ontology.md)
- [Agentlas OS Agent Operation Environment (AOE) workforce networking](https://github.com/agentlas-ai/Agentlas-OS/blob/main/docs/hephaestus-network-2.0.md)
- [Agentlas OS Agent Operation Environment (AOE) MCP connector](https://agentlas.cloud/connectors/hephaestus-network)
