"""Search the Agentlas OS Agent Operation Environment (AOE) over remote MCP."""

import asyncio
import json
import os
from typing import Any

import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = os.getenv(
    "AGENTLAS_AOE_MCP_URL",
    "https://agentlas.cloud/api/mcp/hephaestus-network",
)
ONTOLOGY_VERSION = "awo:2026-07-15.2"
DEFAULT_TASK = (
    "Review a software repository for security risks and produce a concise "
    "remediation plan."
)
ROLE_PROFILES = {
    "Security engineering": {
        "slot_id": "slot:security-engineer",
        "title": "Security reviewer",
        "community": "community:security-engineering",
        "skill": "skill:security-review",
    },
    "Backend engineering": {
        "slot_id": "slot:backend-engineer",
        "title": "Backend engineer",
        "community": "community:backend-engineering",
        "skill": "skill:server-implementation",
    },
    "Research": {
        "slot_id": "slot:researcher",
        "title": "Researcher",
        "community": "community:research",
        "skill": "skill:evidence-synthesis",
    },
}


def build_work_order(task: str, profile_name: str, limit: int) -> dict[str, Any]:
    """Create one redacted, typed role slot from a public tutorial profile."""
    profile = ROLE_PROFILES[profile_name]
    return {
        "schemaVersion": "agentlas.workforce-work-order.v1",
        "workOrderId": "work-order:test",
        "taskBrief": task,
        "redacted": True,
        "ontologyVersion": ONTOLOGY_VERSION,
        "roleSlots": [
            {
                "slotId": profile["slot_id"],
                "title": profile["title"],
                "task": task,
                "cardinality": 1,
                "criticality": "required",
                "requiredCommunities": [],
                "optionalCommunities": [profile["community"]],
                "excludedCommunities": [],
                "requiredRoles": [],
                "requiredSkills": [],
                "optionalSkills": [profile["skill"]],
                "requiredKnowledge": [],
                "requiredToolCapabilities": [],
                "consumes": [],
                "produces": [],
                "requiredAuthorities": [],
                "forbiddenAuthorities": [],
                "runtimes": [],
                "languages": [],
                "modalities": [],
                "allowedEntityKinds": ["agent", "team"],
                "minimumEvidenceLevel": "declared",
            }
        ],
        "edges": [],
        "forbiddenCommunities": [],
        "selectionPolicy": {
            "minimumCandidatesPerSlot": 2,
            "maximumCandidatesPerSlot": limit,
            "allowHistoryEvidence": False,
        },
    }


async def search_workforce(work_order: dict[str, Any]) -> dict[str, Any]:
    """Call the public, read-only workforce search tool over MCP."""
    async with streamablehttp_client(MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.call_tool(
                "workforce_search_candidates",
                {"workOrder": work_order},
            )

    if response.isError:
        raise RuntimeError(
            "Agentlas OS Agent Operation Environment (AOE) returned an MCP tool error."
        )

    text_blocks = [
        block.text for block in response.content if hasattr(block, "text")
    ]
    if not text_blocks:
        raise RuntimeError(
            "Agentlas OS Agent Operation Environment (AOE) returned no text result."
        )

    return json.loads("\n".join(text_blocks))


st.set_page_config(
    page_title="Agentlas OS Agent Operation Environment (AOE) Workforce Finder",
    layout="wide",
)
st.title("Agentlas OS Agent Operation Environment (AOE)")
st.subheader("MCP Workforce Finder")
st.caption("Retrieve a candidate set. The host LLM makes the staffing decision.")

profile_name = st.selectbox("Role profile", options=list(ROLE_PROFILES))
task = st.text_area("Redacted task brief", value=DEFAULT_TASK)
limit = st.slider("Maximum candidates", min_value=2, max_value=10, value=5)

if st.button("Search workforce", type="primary", use_container_width=True):
    if not task.strip():
        st.error("Enter a redacted task brief.")
    else:
        try:
            work_order = build_work_order(task.strip(), profile_name, limit)
            with st.spinner("Searching the public workforce ontology..."):
                payload = asyncio.run(search_workforce(work_order))
        except (OSError, RuntimeError, json.JSONDecodeError) as exc:
            st.error(f"Search failed: {exc}")
        else:
            slots = payload.get("slots", [])
            candidates = [
                candidate
                for slot in slots
                for candidate in slot.get("candidates", [])
            ]
            coverage_gaps = sorted(
                {
                    gap
                    for slot in slots
                    for gap in slot.get("coverageGaps", [])
                }
            )

            st.caption(
                f"Ontology: {payload.get('ontologyVersion')} | "
                f"Decision owner: {payload.get('decisionOwner')} | "
                f"History influence: {payload.get('historyInfluence')}"
            )

            if not candidates:
                st.info("No hard-eligible candidates were returned for this role slot.")
            else:
                st.success(f"Retrieved {len(candidates)} qualified candidate(s).")
                st.dataframe(
                    [
                        {
                            "Name": item.get("name"),
                            "Kind": item.get("entityKind"),
                            "Release": item.get("releaseVersion"),
                            "Callable": item.get("operational", {}).get("callable"),
                            "Installable": item.get("operational", {}).get(
                                "installable"
                            ),
                            "Communities": ", ".join(item.get("communities", [])),
                            "Fit evidence": ", ".join(item.get("fitEvidence", [])),
                        }
                        for item in candidates
                    ],
                    hide_index=True,
                    use_container_width=True,
                )

            if coverage_gaps:
                st.warning("Coverage gaps: " + ", ".join(coverage_gaps))
