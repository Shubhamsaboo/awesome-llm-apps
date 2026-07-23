import os
import unittest
from unittest.mock import patch

from app.config import Settings


class SettingsProviderTests(unittest.TestCase):
    def test_nebius_is_used_for_chat_without_replacing_dashscope_key(self):
        with patch.dict(
            os.environ,
            {
                "NEBIUS_API_KEY": "nebius-key",
                "DASHSCOPE_API_KEY": "dashscope-key",
            },
            clear=True,
        ):
            configured = Settings(_env_file=None)

        self.assertEqual(configured.chat_api_key, "nebius-key")
        self.assertEqual(configured.dashscope_api_key, "dashscope-key")
        self.assertEqual(
            configured.chat_base_url,
            "https://api.tokenfactory.nebius.com/v1",
        )

    def test_explicit_chat_base_url_overrides_nebius_default(self):
        with patch.dict(
            os.environ,
            {
                "NEBIUS_API_KEY": "nebius-key",
                "OPENAI_BASE_URL": "https://example.com/v1",
            },
            clear=True,
        ):
            configured = Settings(_env_file=None)

        self.assertEqual(configured.chat_base_url, "https://example.com/v1")

    def test_dashscope_key_remains_a_chat_fallback(self):
        with patch.dict(
            os.environ,
            {"DASHSCOPE_API_KEY": "dashscope-key"},
            clear=True,
        ):
            configured = Settings(_env_file=None)

        self.assertEqual(configured.chat_api_key, "dashscope-key")
        self.assertEqual(
            configured.chat_base_url,
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )


if __name__ == "__main__":
    unittest.main()
