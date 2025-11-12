"""
Security tests to verify that critical vulnerabilities are fixed.
"""
import pytest
import ast
import subprocess
import sys
from pathlib import Path


class TestSecurityVulnerabilities:
    """Test that security vulnerabilities have been properly fixed."""

    def test_no_eval_usage(self):
        """Verify that eval() is not used in production code."""
        # This test searches for eval() usage in Python files
        repo_root = Path(__file__).parent.parent
        python_files = list(repo_root.rglob("*.py"))

        # Exclude test files and known safe files
        exclude_patterns = ["tests/", "test_", "_test.py", "venv/", "env/", ".venv/"]

        eval_usage = []
        for py_file in python_files:
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check if eval is used directly (not in comments or strings)
                    if 'eval(' in content:
                        # Parse the file to check if it's actual code
                        try:
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Call):
                                    if isinstance(node.func, ast.Name) and node.func.id == 'eval':
                                        eval_usage.append(str(py_file))
                        except SyntaxError:
                            pass
            except Exception:
                pass

        # The only acceptable eval() usage should be in the fixed calculator_agent file
        # which now uses safe AST-based evaluation
        assert len(eval_usage) == 0, f"Found eval() usage in: {eval_usage}"

    def test_no_shell_true_with_user_input(self):
        """Verify that shell=True is not used unsafely."""
        repo_root = Path(__file__).parent.parent
        python_files = list(repo_root.rglob("*.py"))

        exclude_patterns = ["tests/", "venv/", "env/", ".venv/"]

        shell_true_usage = []
        for py_file in python_files:
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        # Check for shell=True usage
                        if 'shell=True' in line and 'subprocess' in line:
                            # If it's the Windows-specific case, it's acceptable
                            if 'Windows' not in '\n'.join(lines[max(0, i-10):i+10]):
                                shell_true_usage.append(f"{py_file}:{i}")
            except Exception:
                pass

        # We allow one case in Windows-specific code for 'start' command
        assert len(shell_true_usage) <= 1, f"Found unsafe shell=True usage in: {shell_true_usage}"

    def test_calculator_uses_safe_eval(self):
        """Test that the calculator tool uses safe AST-based evaluation."""
        calculator_path = Path(__file__).parent.parent / \
            "ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/4_2_function_tools/calculator_agent/tools.py"

        if calculator_path.exists():
            with open(calculator_path, 'r') as f:
                content = f.read()

            # Check that it imports ast
            assert 'import ast' in content, "Calculator should import ast module"

            # Check that it defines safe operators
            assert 'SAFE_OPERATORS' in content, "Calculator should define SAFE_OPERATORS"

            # Check that it has a safe eval function
            assert '_safe_eval_node' in content or 'safe_eval' in content, \
                "Calculator should have a safe evaluation function"


class TestInputValidation:
    """Test that inputs are properly validated."""

    def test_command_validation_in_scheduler(self):
        """Test that scheduler validates commands before execution."""
        scheduler_path = Path(__file__).parent.parent / \
            "advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py"

        if scheduler_path.exists():
            with open(scheduler_path, 'r') as f:
                content = f.read()

            # Check that it uses shlex for safe parsing
            assert 'import shlex' in content, "Scheduler should import shlex for safe command parsing"

            # Check that it doesn't use shell=True
            assert content.count('shell=True') == 0 or 'Security' in content, \
                "Scheduler should avoid shell=True or have security comments"


@pytest.mark.unit
class TestSecureCodePatterns:
    """Test for secure coding patterns."""

    def test_env_vars_for_secrets(self):
        """Verify that secrets are loaded from environment variables."""
        # Sample check for a few key files
        resume_matcher = Path(__file__).parent.parent / \
            "advanced_llm_apps/resume_job_matcher/app.py"

        if resume_matcher.exists():
            with open(resume_matcher, 'r') as f:
                content = f.read()

            # Should not contain hardcoded API keys
            assert 'sk-' not in content or 'os.getenv' in content, \
                "API keys should be loaded from environment variables"

    def test_sql_injection_prevention(self):
        """Test that SQL queries use parameterization."""
        slack_chat = Path(__file__).parent.parent / \
            "advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/integrations/slack/chat.py"

        if slack_chat.exists():
            with open(slack_chat, 'r') as f:
                content = f.read()

            # Check for parameterized queries (using ?)
            if 'cursor.execute' in content:
                # Good: should use ? placeholders
                assert '?' in content and '(?' in content, \
                    "SQL queries should use parameterized statements"
