import os
import tempfile
import time
from typing import List, Optional, Tuple, Any

import streamlit as st
import requests
import json
import re
from contextual import ContextualAI


def init_session_state() -> None:
    if "api_key_submitted" not in st.session_state:
        st.session_state.api_key_submitted = False
    if "contextual_api_key" not in st.session_state:
        st.session_state.contextual_api_key = ""
    if "base_url" not in st.session_state:
        st.session_state.base_url = "https://api.contextual.ai/v1"
    if "agent_id" not in st.session_state:
        st.session_state.agent_id = ""
    if "datastore_id" not in st.session_state:
        st.session_state.datastore_id = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "processed_file" not in st.session_state:
        st.session_state.processed_file = False
    if "last_raw_response" not in st.session_state:
        st.session_state.last_raw_response = None
    if "last_user_query" not in st.session_state:
        st.session_state.last_user_query = ""


def sidebar_api_form() -> bool:
    with st.sidebar:
        st.header("API & Resource Setup")

        if st.session_state.api_key_submitted:
            st.success("API verified")
            if st.button("Reset Setup"):
                st.session_state.clear()
                st.rerun()
            return True

        with st.form("contextual_api_form"):
            api_key = st.text_input("Contextual AI API Key", type="password")
            base_url = st.text_input(
                "Base URL",
                value=st.session_state.base_url,
                help="Include /v1 (e.g., https://api.contextual.ai/v1)",
            )
            existing_agent_id = st.text_input("Existing Agent ID (optional)")
            existing_datastore_id = st.text_input("Existing Datastore ID (optional)")

            if st.form_submit_button("Save & Verify"):
                try:
                    client = ContextualAI(api_key=api_key, base_url=base_url)
                    _ = client.agents.list()

                    st.session_state.contextual_api_key = api_key
                    st.session_state.base_url = base_url
                    st.session_state.agent_id = existing_agent_id
                    st.session_state.datastore_id = existing_datastore_id
                    st.session_state.api_key_submitted = True

                    st.success("Credentials verified!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Credential verification failed: {str(e)}")
        return False


def ensure_client():
    if not st.session_state.get("contextual_api_key"):
        raise ValueError("Contextual AI API key not provided")
    return ContextualAI(api_key=st.session_state.contextual_api_key, base_url=st.session_state.base_url)


def create_datastore(client, name: str) -> Optional[str]:
    try:
        ds = client.datastores.create(name=name)
        return getattr(ds, "id", None)
    except Exception as e:
        st.error(f"Failed to create datastore: {e}")
        return None


ALLOWED_EXTS = {".pdf", ".html", ".htm", ".mhtml", ".doc", ".docx", ".ppt", ".pptx"}

def upload_documents(client, datastore_id: str, files: List[bytes], filenames: List[str], metadata: Optional[dict]) -> List[str]:
    doc_ids: List[str] = []
    for content, fname in zip(files, filenames):
        try:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_EXTS:
                st.error(f"Unsupported file extension for {fname}. Allowed: {sorted(ALLOWED_EXTS)}")
                continue
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as f:
                if metadata:
                    result = client.datastores.documents.ingest(datastore_id, file=f, metadata=metadata)
                else:
                    result = client.datastores.documents.ingest(datastore_id, file=f)
                doc_ids.append(getattr(result, "id", ""))
        except Exception as e:
            st.error(f"Failed to upload {fname}: {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    return doc_ids


def wait_until_documents_ready(api_key: str, datastore_id: str, base_url: str, max_checks: int = 30, interval_sec: float = 5.0) -> None:
    url = f"{base_url.rstrip('/')}/datastores/{datastore_id}/documents"
    headers = {"Authorization": f"Bearer {api_key}"}

    for _ in range(max_checks):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                docs = resp.json().get("documents", [])
                if not any(d.get("status") in ("processing", "pending") for d in docs):
                    return
            time.sleep(interval_sec)
        except Exception:
            time.sleep(interval_sec)


def create_agent(client, name: str, description: str, datastore_id: str) -> Optional[str]:
    try:
        agent = client.agents.create(name=name, description=description, datastore_ids=[datastore_id])
        return getattr(agent, "id", None)
    except Exception as e:
        st.error(f"Failed to create agent: {e}")
        return None


def query_agent(client, agent_id: str, query: str) -> Tuple[str, Any]:
    try:
        resp = client.agents.query.create(agent_id=agent_id, messages=[{"role": "user", "content": query}])
        if hasattr(resp, "content"):
            return resp.content, resp
        if hasattr(resp, "message") and hasattr(resp.message, "content"):
            return resp.message.content, resp
        if hasattr(resp, "messages") and resp.messages:
            last_msg = resp.messages[-1]
            return getattr(last_msg, "content", str(last_msg)), resp
        return str(resp), resp
    except Exception as e:
        return f"Error querying agent: {e}", None


def show_retrieval_info(client, raw_response, agent_id: str) -> None:
    try:
        if not raw_response:
            st.info("No retrieval info available.")
            return
        message_id = getattr(raw_response, "message_id", None)
        retrieval_contents = getattr(raw_response, "retrieval_contents", [])
        if not message_id or not retrieval_contents:
            st.info("No retrieval metadata returned.")
            return
        first_content_id = getattr(retrieval_contents[0], "content_id", None)
        if not first_content_id:
            st.info("Missing content_id in retrieval metadata.")
            return
        ret_result = client.agents.query.retrieval_info(message_id=message_id, agent_id=agent_id, content_ids=[first_content_id])
        metadatas = getattr(ret_result, "content_metadatas", [])
        if not metadatas:
            st.info("No content metadatas found.")
            return
        page_img_b64 = getattr(metadatas[0], "page_img", None)
        if not page_img_b64:
            st.info("No page image provided in metadata.")
            return
        import base64
        img_bytes = base64.b64decode(page_img_b64)
        st.image(img_bytes, caption="Top Attribution Page", use_container_width=True)
        # Removed raw object rendering to keep UI clean
    except Exception as e:
        st.error(f"Failed to load retrieval info: {e}")


def update_agent_prompt(client, agent_id: str, system_prompt: str) -> bool:
    try:
        client.agents.update(agent_id=agent_id, system_prompt=system_prompt)
        return True
    except Exception as e:
        st.error(f"Failed to update system prompt: {e}")
        return False


def evaluate_with_lmunit(client, query: str, response_text: str, unit_test: str):
    try:
        result = client.lmunit.create(query=query, response=response_text, unit_test=unit_test)
        st.subheader("Evaluation Result")
        st.code(str(result), language="json")
    except Exception as e:
        st.error(f"LMUnit evaluation failed: {e}")


def post_process_answer(text: str) -> str:
    text = re.sub(r"\(\s*\)", "", text)
    text = text.replace("• ", "\n- ")
    return text


init_session_state()

st.title("Contextual AI RAG Agent")

if not sidebar_api_form():
    st.info("Please enter your Contextual AI API key in the sidebar to continue.")
    st.stop()

client = ensure_client()

with st.expander("1) Create or Select Datastore", expanded=True):
    if not st.session_state.datastore_id:
        default_name = "contextualai_rag_datastore"
        ds_name = st.text_input("Datastore Name", value=default_name)
        if st.button("Create Datastore"):
            ds_id = create_datastore(client, ds_name)
            if ds_id:
                st.session_state.datastore_id = ds_id
                st.success(f"Created datastore: {ds_id}")
    else:
        st.success(f"Using Datastore: {st.session_state.datastore_id}")

with st.expander("2) Upload Documents", expanded=True):
    uploaded_files = st.file_uploader("Upload PDFs or text files", type=["pdf", "txt", "md"], accept_multiple_files=True)
    metadata_json = st.text_area("Custom Metadata (JSON)", value="", placeholder='{"custom_metadata": {"field1": "value1"}}')
    if uploaded_files and st.session_state.datastore_id:
        contents = [f.getvalue() for f in uploaded_files]
        names = [f.name for f in uploaded_files]
        if st.button("Ingest Documents"):
            parsed_metadata = None
            if metadata_json.strip():
                try:
                    parsed_metadata = json.loads(metadata_json)
                except Exception as e:
                    st.error(f"Invalid metadata JSON: {e}")
                    parsed_metadata = None
            ids = upload_documents(client, st.session_state.datastore_id, contents, names, parsed_metadata)
            if ids:
                st.success(f"Uploaded {len(ids)} document(s)")
                wait_until_documents_ready(st.session_state.contextual_api_key, st.session_state.datastore_id, st.session_state.base_url)
                st.info("Documents are ready.")

with st.expander("3) Create or Select Agent", expanded=True):
    if not st.session_state.agent_id and st.session_state.datastore_id:
        agent_name = st.text_input("Agent Name", value="ContextualAI RAG Agent")
        agent_desc = st.text_area("Agent Description", value="RAG agent over uploaded documents")
        if st.button("Create Agent"):
            a_id = create_agent(client, agent_name, agent_desc, st.session_state.datastore_id)
            if a_id:
                st.session_state.agent_id = a_id
                st.success(f"Created agent: {a_id}")
    elif st.session_state.agent_id:
        st.success(f"Using Agent: {st.session_state.agent_id}")

with st.expander("4) Agent Settings (Optional)"):
    if st.session_state.agent_id:
        system_prompt_val = st.text_area("System Prompt", value="", placeholder="Paste a new system prompt to update your agent")
        if st.button("Update System Prompt") and system_prompt_val.strip():
            ok = update_agent_prompt(client, st.session_state.agent_id, system_prompt_val.strip())
            if ok:
                st.success("System prompt updated.")

st.divider()

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"]) 

query = st.chat_input("Ask a question about your documents")
if query:
    st.session_state.last_user_query = query
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    if st.session_state.agent_id:
        with st.chat_message("assistant"):
            answer, raw = query_agent(client, st.session_state.agent_id, query)
            st.session_state.last_raw_response = raw
            processed = post_process_answer(answer)
            st.markdown(processed)
            st.session_state.chat_history.append({"role": "assistant", "content": processed})
    else:
        st.error("Please create or select an agent first.")

with st.expander("Debug & Evaluation", expanded=False):
    st.caption("Tools to inspect retrievals and evaluate answers")
    if st.session_state.agent_id:
        if st.checkbox("Show Retrieval Info", value=False):
            show_retrieval_info(client, st.session_state.last_raw_response, st.session_state.agent_id)
        st.markdown("")
        unit_test = st.text_area("LMUnit rubric / unit test", value="Does the response avoid unnecessary information?", height=80)
        if st.button("Evaluate Last Answer with LMUnit"):
            if st.session_state.last_user_query and st.session_state.chat_history:
                last_assistant_msgs = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
                if last_assistant_msgs:
                    evaluate_with_lmunit(client, st.session_state.last_user_query, last_assistant_msgs[-1]["content"], unit_test)
                else:
                    st.info("No assistant response to evaluate yet.")
            else:
                st.info("Ask a question first to run an evaluation.")

with st.sidebar:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.last_raw_response = None
            st.session_state.last_user_query = ""
            st.rerun()
    with col2:
        if st.button("Reset App"):
            st.session_state.clear()
            st.rerun()


