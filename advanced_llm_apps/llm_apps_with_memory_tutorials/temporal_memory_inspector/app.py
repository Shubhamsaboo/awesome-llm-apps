"""Interactive current-versus-historical memory inspector."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
from lians import LocalLiansClient

from temporal_memory import (
    HISTORICAL_CUTOFF,
    contents,
    recall,
    seed_timeline,
)

st.set_page_config(page_title="Temporal Memory Inspector", page_icon="🕰️")
st.title("🕰️ Temporal Memory Inspector")
st.caption("Ask an agent what is true now—or what was true before a correction.")

if "lians_db" not in st.session_state:
    session_dir = Path(tempfile.mkdtemp(prefix="lians-memory-"))
    st.session_state.lians_db = str(session_dir / "memory.db")
    with LocalLiansClient(
        db_path=st.session_state.lians_db,
        embedding_provider="sentence-transformers",
    ) as memory:
        seed_timeline(memory)

st.subheader("Order 1842 timeline")
left, right = st.columns(2)
left.info("August 1, 9:00 UTC\n\nEstimate: **Friday**")
right.warning("August 2, 15:00 UTC\n\nCorrected estimate: **Monday**")

perspective = st.radio(
    "Memory boundary",
    ("Current state", "August 2 at noon"),
    horizontal=True,
)

if st.button("Recall shipping estimate", type="primary", use_container_width=True):
    as_of = None if perspective == "Current state" else HISTORICAL_CUTOFF
    with LocalLiansClient(
        db_path=st.session_state.lians_db,
        embedding_provider="sentence-transformers",
    ) as memory:
        result = recall(memory, as_of=as_of)

    recalled = contents(result)
    st.success(recalled[0] if recalled else "No memory matched the query.")

    with st.expander("Inspect verifiable receipt"):
        st.code(result.get("receipt_sha256", "No receipt hash returned"))
        st.json(result.get("receipt", {}))

st.divider()
st.markdown(
    "Powered by [Lians](https://github.com/Lians-ai/Lians), "
    "local temporal memory for AI agents."
)
