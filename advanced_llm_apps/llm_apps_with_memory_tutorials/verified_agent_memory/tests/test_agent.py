"""Unit tests for CodingAgent reasoning, code extraction, and memory integration."""

import os
from pathlib import Path
import tempfile
from unittest.mock import MagicMock
import pytest

from agent import CodingAgent
from memory import ExperienceMemory
from models import ExperienceStatus
from verifier import ExecutionVerifier


def test_missing_api_key_raises_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is not set"):
        CodingAgent(client=None)


def test_extract_code_from_markdown():
    agent = CodingAgent(client=MagicMock())

    markdown_response = (
        "Here is the solution:\n\n"
        "```python\n"
        "def solve():\n"
        "    return 42\n"
        "```\n"
        "Hope this helps!"
    )
    code = agent.extract_code(markdown_response)
    assert code == "def solve():\n    return 42"

    raw_response = "def add(x, y): return x + y"
    assert agent.extract_code(raw_response) == "def add(x, y): return x + y"


def test_agent_run_session_iteration_and_learning_loop():
    """Verify that agent iterates on real pytest failures, captures DO NOT REPEAT constraints,

    and promotes to VERIFIED upon test success.
    """
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        work_dir = Path(td)
        task_dir = work_dir / "task"
        task_dir.mkdir()

        # Write problem and test files
        (task_dir / "README.md").write_text("Implement get_val() returning 100", encoding="utf-8")
        (task_dir / "problem.py").write_text("def get_val(): raise NotImplementedError", encoding="utf-8")
        (task_dir / "test_rate_limiter.py").write_text(
            "from problem import get_val\n"
            "def test_get_val():\n"
            "    assert get_val() == 100\n",
            encoding="utf-8",
        )

        db_path = work_dir / "test_mem.db"
        memory = ExperienceMemory(db_path=db_path)
        verifier = ExecutionVerifier(timeout=10)

        # Mock OpenAI responses:
        # Call 1: returns buggy code (get_val returns 50)
        # Call 2: returns fixed code (get_val returns 100)
        mock_client = MagicMock()
        mock_choice_1 = MagicMock()
        mock_choice_1.message.content = "```python\ndef get_val():\n    return 50\n```"
        mock_choice_2 = MagicMock()
        mock_choice_2.message.content = "```python\ndef get_val():\n    return 100\n```"

        mock_resp_1 = MagicMock(choices=[mock_choice_1])
        mock_resp_2 = MagicMock(choices=[mock_choice_2])
        mock_client.chat.completions.create.side_effect = [mock_resp_1, mock_resp_2]

        agent = CodingAgent(
            client=mock_client,
            memory=memory,
            verifier=verifier,
        )

        result = agent.run_session(
            task_id="get_val_task",
            task_dir=task_dir,
            problem_filename="problem.py",
            test_filename="test_rate_limiter.py",
            use_memory=False,
            max_attempts=3,
            session_label="Test Session 1",
        )

        assert result["solved"] is True
        assert result["attempts_count"] == 2

        # Check memory
        saved_exp = memory.get_experience_by_task("get_val_task")
        assert saved_exp is not None
        assert saved_exp.status == ExperienceStatus.VERIFIED
        assert saved_exp.is_verified() is True
        assert len(saved_exp.failed_approaches) == 1
        assert "AssertionError" in saved_exp.failed_approaches[0].error_message or "FAILED" in saved_exp.failed_approaches[0].error_message

        # Session 2: Fresh agent with memory
        mock_client_s2 = MagicMock()
        mock_choice_s2 = MagicMock()
        mock_choice_s2.message.content = "```python\ndef get_val():\n    return 100\n```"
        mock_client_s2.chat.completions.create.return_value = MagicMock(choices=[mock_choice_s2])

        agent_s2 = CodingAgent(
            client=mock_client_s2,
            memory=memory,
            verifier=verifier,
        )

        result_s2 = agent_s2.run_session(
            task_id="get_val_task",
            task_dir=task_dir,
            problem_filename="problem.py",
            test_filename="test_rate_limiter.py",
            use_memory=True,
            max_attempts=3,
            session_label="Test Session 2",
        )

        assert result_s2["solved"] is True
        assert result_s2["attempts_count"] == 1
        # Verify retrieved experience was sent in prompt to LLM
        prompt_call = mock_client_s2.chat.completions.create.call_args
        prompt_messages = prompt_call.kwargs["messages"]
        user_msg = [m["content"] for m in prompt_messages if m["role"] == "user"][0]
        assert "RETRIEVED CROSS-SESSION EXPERIENCE & CONSTRAINTS" in user_msg
        assert "DO NOT REPEAT" in user_msg
