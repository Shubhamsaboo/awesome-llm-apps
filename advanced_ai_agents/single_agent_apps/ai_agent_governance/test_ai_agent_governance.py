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