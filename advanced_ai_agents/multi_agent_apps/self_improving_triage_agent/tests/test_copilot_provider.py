"""Tests for the Copilot provider wiring and the temperature fix.

    python -m unittest discover -s tests -v

No network and no credentials: token files point at a temp dir.
"""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import litellm  # noqa: E402
from triage_optimizer import TriageOptimizer  # noqa: E402


class TemperatureFix(unittest.TestCase):
    def test_unsupported_params_are_dropped_not_raised(self):
        # Newer Claude models accept only temperature=1; without this the first
        # call raised UnsupportedParamsError.
        self.assertTrue(litellm.drop_params)


class KeyRouting(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("ANTHROPIC_API_KEY", None)

    def tearDown(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        if self._saved is not None:
            os.environ["ANTHROPIC_API_KEY"] = self._saved

    def test_anthropic_model_sets_anthropic_key(self):
        TriageOptimizer(model="anthropic/claude-sonnet-5", api_key="k")
        self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"), "k")

    def test_copilot_claude_model_does_not_touch_anthropic_key(self):
        # "github_copilot/claude-…" contains "claude"; it must not match that needle.
        TriageOptimizer(model="github_copilot/claude-sonnet-5", api_key="k")
        self.assertNotIn("ANTHROPIC_API_KEY", os.environ)


class CopilotHelper(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._saved = os.environ.get("GITHUB_COPILOT_TOKEN_DIR")
        os.environ["GITHUB_COPILOT_TOKEN_DIR"] = self._tmp.name
        import copilot

        self.copilot = copilot

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("GITHUB_COPILOT_TOKEN_DIR", None)
        else:
            os.environ["GITHUB_COPILOT_TOKEN_DIR"] = self._saved
        self._tmp.cleanup()

    def test_not_signed_in_without_token(self):
        self.assertFalse(self.copilot.is_signed_in())

    def test_list_models_empty_when_not_signed_in(self):
        self.assertEqual(self.copilot.list_models(), [])

    def test_signed_in_once_token_cached(self):
        with open(os.path.join(self._tmp.name, "access-token"), "w") as f:
            f.write("gho_fake")
        self.assertTrue(self.copilot.is_signed_in())

    def test_empty_token_file_is_not_signed_in(self):
        open(os.path.join(self._tmp.name, "access-token"), "w").close()
        self.assertFalse(self.copilot.is_signed_in())


class AppImports(unittest.TestCase):
    def test_streamlit_app_runs_without_exception(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(os.path.join(ROOT, "optimizer", "app.py"), default_timeout=60).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])


if __name__ == "__main__":
    unittest.main()
