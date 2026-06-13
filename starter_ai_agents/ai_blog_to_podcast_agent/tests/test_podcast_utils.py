import subprocess
import unittest
from unittest.mock import patch

from podcast_utils import (
    extract_text_from_html,
    fetch_url_with_curl,
    get_openai_api_key,
    synthesize_aiff_with_say,
)


class PodcastUtilsTest(unittest.TestCase):
    @patch.dict("podcast_utils.os.environ", {"OPENAI_API_KEY": "env-key"}, clear=True)
    @patch("podcast_utils.subprocess.run")
    def test_get_openai_api_key_prefers_environment(self, run):
        self.assertEqual(get_openai_api_key(), "env-key")
        run.assert_not_called()

    @patch.dict("podcast_utils.os.environ", {"USER": "xili"}, clear=True)
    @patch("podcast_utils.subprocess.run")
    def test_get_openai_api_key_falls_back_to_macos_keychain(self, run):
        run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="keychain-key\n", stderr="")

        self.assertEqual(get_openai_api_key(), "keychain-key")
        run.assert_called_once_with(
            ["security", "find-generic-password", "-s", "OPENAI_API_KEY", "-a", "xili", "-w"],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_extract_text_from_html_removes_markup_and_scripts(self):
        html = """
        <html>
            <head><title>Ignored</title><style>.x { color: red; }</style></head>
            <body>
                <h1>Launch Notes</h1>
                <script>alert("noise")</script>
                <p>This&nbsp;is a <strong>short</strong> post.</p>
            </body>
        </html>
        """

        text = extract_text_from_html(html)

        self.assertEqual(text, "Launch Notes This is a short post.")

    @patch("podcast_utils.subprocess.run")
    def test_fetch_url_with_curl_uses_safe_flags_and_returns_stdout(self, run):
        run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="<html>ok</html>", stderr="")

        html = fetch_url_with_curl("https://example.com/post")

        self.assertEqual(html, "<html>ok</html>")
        run.assert_called_once_with(
            [
                "curl",
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                "30",
                "https://example.com/post",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("podcast_utils.subprocess.run")
    def test_synthesize_aiff_with_say_writes_aiff_file(self, run):
        synthesize_aiff_with_say("Hello from the blog", "/tmp/podcast.aiff")

        run.assert_called_once_with(
            ["say", "-o", "/tmp/podcast.aiff", "Hello from the blog"],
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
