"""Tests for model backend wiring and the temperature fix.

    python -m unittest discover -s tests -v

No network and no credentials.
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "optimizer"))

import litellm  # noqa: E402
from skill_optimizer import SkillOptimizer  # noqa: E402


class TemperatureFix(unittest.TestCase):
    def test_unsupported_params_are_dropped_not_raised(self):
        # Newer Claude models accept only temperature=1; without this the first
        # call raised UnsupportedParamsError.
        self.assertTrue(litellm.drop_params)


class KeyHandling(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("ANTHROPIC_API_KEY", None)

    def tearDown(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        if self._saved is not None:
            os.environ["ANTHROPIC_API_KEY"] = self._saved

    def test_key_stays_on_the_client_not_in_the_environment(self):
        opt = SkillOptimizer(model="anthropic/claude-sonnet-5", api_key="k")
        self.assertEqual(opt.api_key, "k")
        self.assertNotIn("ANTHROPIC_API_KEY", os.environ)

class AppImports(unittest.TestCase):
    def test_streamlit_app_runs_without_exception(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(os.path.join(ROOT, "optimizer", "app.py"), default_timeout=60).run()
        self.assertFalse(at.exception, [e.value for e in at.exception])


if __name__ == "__main__":
    unittest.main()
