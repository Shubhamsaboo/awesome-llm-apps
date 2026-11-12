from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage

import tools


class FailingTavily:
    def __init__(self, api_key):
        pass

    def search(self, **kwargs):
        raise RuntimeError("quota exceeded")


@pytest.fixture
def run_research(monkeypatch):
    """Runs the research tool with a stub sub-agent that searches once and replies with `messages`."""

    def run(messages):
        def create_deep_agent(model, system_prompt, tools):
            def invoke(state):
                tools[0]("solar panels")
                return {"messages": messages}

            return SimpleNamespace(invoke=invoke)

        monkeypatch.setattr("deepagents.create_deep_agent", create_deep_agent)
        monkeypatch.setattr("langchain_openai.ChatOpenAI", lambda **kwargs: None)
        return tools.research.func(query="solar panels")

    return run


def test_missing_tavily_key_is_reported_like_a_failed_search(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    assert tools._do_internet_search("solar panels") == [
        {"error": "TAVILY_API_KEY not set", "query": "solar panels"}
    ]


def test_failed_search_is_listed_as_a_failed_source(monkeypatch, run_research):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(tools, "TavilyClient", FailingTavily)

    result = run_research(
        [HumanMessage("solar panels"), AIMessage("No sources could be read.")]
    )

    assert result["sources"] == [
        {
            "url": "",
            "title": "Search failed: solar panels",
            "content": "quota exceeded",
            "status": "failed",
        }
    ]


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [
            HumanMessage("solar panels"),
            AIMessage(
                "", tool_calls=[{"name": "internet_search", "args": {}, "id": "c1"}]
            ),
        ],
    ],
)
def test_run_without_a_final_text_gets_a_stated_summary(
    monkeypatch, run_research, messages
):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    assert run_research(messages)["summary"] == "The research returned no findings."


def test_summary_joins_the_text_of_content_blocks(monkeypatch, run_research):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    reply = AIMessage(
        [{"type": "text", "text": "Panels got "}, {"type": "text", "text": "cheaper."}]
    )

    assert (
        run_research([HumanMessage("solar panels"), reply])["summary"]
        == "Panels got cheaper."
    )
