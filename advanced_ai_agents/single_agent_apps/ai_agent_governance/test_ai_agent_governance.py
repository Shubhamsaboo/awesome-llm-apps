from unittest.mock import MagicMock, patch

from ai_agent_governance import GovernedAgent, PolicyEngine


def test_run_handles_null_llm_content():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = None

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("ai_agent_governance.OpenAI", return_value=mock_client):
        agent = GovernedAgent(PolicyEngine())
        result = agent.run("Test prompt")

    assert result == ""

def test_tool_call_keeps_arguments_that_span_lines():
    from ai_agent_governance import _tool_call_texts

    reply = 'TOOL: write_file(\n    path="/workspace/report.md",\n    content="Total, by region"\n)'

    assert _tool_call_texts(reply) == [
        'write_file(\n    path="/workspace/report.md",\n    content="Total, by region"\n)'
    ]


def test_every_tool_call_in_a_reply_is_returned():
    from ai_agent_governance import _tool_call_texts

    reply = 'First:\nTOOL: read_file(path="/a")\nSecond:\nTOOL: delete_file(path="/b")\n'

    assert _tool_call_texts(reply) == [
        'read_file(path="/a")',
        'delete_file(path="/b")',
    ]


def test_comma_in_an_argument_reaches_the_tool_intact():
    from ai_agent_governance import GovernedAgent

    agent = GovernedAgent.__new__(GovernedAgent)
    seen = {}

    def fake_write(path, content):
        seen.update(path=path, content=content)
        return "ok"

    agent.tools = {"write_file": fake_write}

    result = agent._execute_tool_call(
        'write_file(path="/workspace/report.md", content="Total, by region")'
    )

    assert result == "Tool result: ok"
    assert seen == {"path": "/workspace/report.md", "content": "Total, by region"}
