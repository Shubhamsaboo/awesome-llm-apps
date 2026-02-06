import streamlit as st
import requests
from typing import Optional


class RAGStackClient:
    def __init__(self, graphql_endpoint: str, api_key: str):
        self.endpoint = graphql_endpoint
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }

    def _request(self, query: str, variables: Optional[dict] = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        response = requests.post(
            self.endpoint, json=payload, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def search(self, query: str, max_results: int = 5) -> dict:
        gql = """
        query SearchKnowledgeBase($query: String!, $maxResults: Int) {
            searchKnowledgeBase(query: $query, maxResults: $maxResults) {
                query
                total
                error
                results { content source score }
            }
        }
        """
        return self._request(gql, {"query": query, "maxResults": max_results})

    def chat(self, query: str, conversation_id: Optional[str] = None) -> dict:
        gql = """
        query QueryKnowledgeBase($query: String!, $conversationId: String) {
            queryKnowledgeBase(query: $query, conversationId: $conversationId) {
                answer
                conversationId
                error
                sources { documentId s3Uri snippet documentUrl }
            }
        }
        """
        variables = {"query": query}
        if conversation_id:
            variables["conversationId"] = conversation_id
        return self._request(gql, variables)

    def get_documents(self) -> dict:
        gql = """
        query ListDocuments {
            listDocuments {
                documentId
                filename
                status
                fileType
                uploadTimestamp
            }
        }
        """
        return self._request(gql)

    def upload_url(self, filename: str, content_type: str) -> dict:
        gql = """
        mutation GetUploadUrl($filename: String!, $contentType: String!) {
            getUploadUrl(filename: $filename, contentType: $contentType) {
                uploadUrl
                documentId
            }
        }
        """
        return self._request(
            gql, {"filename": filename, "contentType": content_type}
        )


def main():
    st.set_page_config(page_title="Serverless RAG on AWS Lambda", layout="wide")

    st.title("Serverless RAG API on AWS Lambda")
    st.caption(
        "Query a [RAGStack](https://github.com/HatmanStack/RAGStack-Lambda) "
        "knowledge base — scale-to-zero architecture, $0 when idle."
    )

    # Sidebar config
    with st.sidebar:
        st.header("Configuration")
        endpoint = st.text_input("GraphQL Endpoint", type="default")
        api_key = st.text_input("API Key", type="password")

        if endpoint and api_key:
            st.session_state.client = RAGStackClient(endpoint, api_key)
            st.success("Connected")
        else:
            st.info("Enter your RAGStack endpoint and API key from the dashboard.")

    if "client" not in st.session_state:
        st.markdown(
            """
            ### Get Started

            1. **Deploy RAGStack** — [One-click on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-5afdiw2zrht6o)
               or `python publish.py --project-name my-docs --admin-email you@email.com`
            2. **Upload documents** via the dashboard
            3. **Copy your endpoint and API key** from Dashboard → Settings
            4. **Paste them in the sidebar** to start querying
            """
        )
        return

    client = st.session_state.client
    tab_chat, tab_search, tab_docs = st.tabs(["Chat", "Search", "Documents"])

    # Chat tab
    with tab_chat:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = None

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask a question about your documents"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = client.chat(
                            prompt, st.session_state.conversation_id
                        )
                        data = result.get("data", {}).get("queryKnowledgeBase", {})

                        if data.get("error"):
                            st.error(data["error"])
                        else:
                            answer = data.get("answer", "No answer generated.")
                            st.markdown(answer)

                            st.session_state.conversation_id = data.get(
                                "conversationId"
                            )

                            sources = data.get("sources", [])
                            if sources:
                                with st.expander(f"Sources ({len(sources)})"):
                                    for s in sources:
                                        uri = s.get("s3Uri", "")
                                        filename = uri.split("/")[-1] if uri else "Unknown"
                                        snippet = s.get("snippet", "")[:200]
                                        st.markdown(f"**{filename}**\n\n{snippet}")

                            st.session_state.messages.append(
                                {"role": "assistant", "content": answer}
                            )
                    except Exception as e:
                        st.error(f"Error: {e}")

        if st.session_state.messages:
            if st.button("Clear conversation"):
                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.rerun()

    # Search tab
    with tab_search:
        query = st.text_input("Search query")
        max_results = st.slider("Max results", 1, 20, 5)

        if st.button("Search") and query:
            with st.spinner("Searching..."):
                try:
                    result = client.search(query, max_results)
                    data = result.get("data", {}).get("searchKnowledgeBase", {})

                    if data.get("error"):
                        st.error(data["error"])
                    else:
                        results = data.get("results", [])
                        st.markdown(f"**{data.get('total', len(results))} results**")

                        for r in results:
                            source = r.get("source", "Unknown")
                            score = r.get("score", 0)
                            content = r.get("content", "")[:500]

                            with st.expander(
                                f"{source.split('/')[-1]} (score: {score:.2f})"
                            ):
                                st.markdown(content)
                except Exception as e:
                    st.error(f"Error: {e}")

    # Documents tab
    with tab_docs:
        if st.button("Refresh documents"):
            pass  # triggers re-run

        try:
            result = client.get_documents()
            docs = result.get("data", {}).get("listDocuments", [])

            if docs:
                for doc in docs:
                    status_emoji = {
                        "INDEXED": "✅",
                        "PROCESSING": "⏳",
                        "UPLOADED": "📤",
                        "FAILED": "❌",
                    }.get(doc.get("status", ""), "❓")

                    st.markdown(
                        f"{status_emoji} **{doc.get('filename', 'Unknown')}** "
                        f"— {doc.get('status', '')} "
                        f"({doc.get('fileType', '')})"
                    )
            else:
                st.info("No documents found. Upload documents via the RAGStack dashboard.")
        except Exception as e:
            st.error(f"Error loading documents: {e}")


if __name__ == "__main__":
    main()
