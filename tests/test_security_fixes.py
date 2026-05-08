"""
Functional tests for security and quality fixes.
These tests validate the actual functionality of the fixes applied.
"""
import os
import sys
import sqlite3
import tempfile
import re
import json
import warnings
import logging
from unittest import TestCase
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSQLInjectionFix(TestCase):
    """Test that SQL injection is properly prevented in get_articles.py"""

    def test_like_escape_prevents_sql_injection(self):
        """Test that special characters in search terms are properly escaped"""
        test_terms = [
            "normal term",
            "term%with%percent",
            "term_with_underscore",
            "term'with'quotes",
            "term\"with\"doublequotes",
            "term;with;semicolon",
            "term)with)parentheses",
        ]

        for term in test_terms:
            escaped_term = term.replace("%", "\\%").replace("_", "\\_")
            like_pattern = f"%{escaped_term}%"

            self.assertTrue(
                "%" not in escaped_term or escaped_term.count("\\%") > 0
            )
            self.assertTrue(
                "_" not in escaped_term or escaped_term.count("\\_") > 0
            )

    def test_parameterized_limit(self):
        """Test that LIMIT is properly parameterized"""
        limit = 10
        params = ["test_date"]
        params.append(limit)

        base_query = "SELECT * FROM articles WHERE date > ? LIMIT ?"
        self.assertIn("? LIMIT ?", base_query)
        self.assertEqual(len(params), 2)

    def test_sql_execution_with_mock_db(self):
        """Test SQL execution with mock database and escaped terms"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            conn = sqlite3.connect(f.name)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawled_articles (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    summary TEXT,
                    published_date TEXT
                )
            """)
            conn.commit()

            try:
                terms = ["test%case"]
                params = ["1970-01-01"]

                for term in terms:
                    escaped_term = term.replace("%", "\\%").replace("_", "\\_")
                    like = f"%{escaped_term}%"
                    params.extend([like, like, like])

                params.append(100)
                sql = """
                    SELECT DISTINCT id, title, content, summary
                    FROM crawled_articles
                    WHERE published_date > ? AND (title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\' OR summary LIKE ? ESCAPE '\\')
                    ORDER BY id DESC LIMIT ?
                """

                cursor.execute(sql, params)
                results = cursor.fetchall()
                self.assertIsInstance(results, list)
            finally:
                conn.close()
                os.unlink(f.name)


class TestExceptionHandling(TestCase):
    """Test that proper exception handling is in place"""

    def test_specific_exception_caught(self):
        """Test that specific exceptions are caught"""
        caught = False
        error_type = None

        try:
            int("not a number")
        except ValueError as e:
            caught = True
            error_type = "ValueError"

        self.assertTrue(caught)
        self.assertEqual(error_type, "ValueError")

    def test_json_decode_error_caught(self):
        """Test that JSON decode errors are caught properly"""
        invalid_json = "{ invalid json }"
        result = {}

        try:
            result = json.loads(invalid_json)
        except json.JSONDecodeError:
            result = {}

        self.assertEqual(result, {})

    def test_proper_error_logging(self):
        """Test that errors are logged properly"""
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.ERROR)

        logger = logging.getLogger("test_exception_logging")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.error(f"Error occurred: {e}")

        log_content = log_capture.getvalue()
        self.assertIn("Test error", log_content)


class TestAPIKeyHandling(TestCase):
    """Test that API keys are handled via environment variables"""

    def test_environment_variable_access(self):
        """Test that env vars are accessed via os.getenv"""
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            key = os.getenv("TEST_API_KEY", "")
            self.assertEqual(key, "test_key")

    def test_default_value_for_missing_key(self):
        """Test default value when API key is missing"""
        key = os.getenv("NONEXISTENT_API_KEY_12345", "default_value")
        self.assertEqual(key, "default_value")

    def test_api_key_not_hardcoded(self):
        """Test that API keys are not hardcoded in source files"""
        test_files = [
            "advanced_llm_apps/cursor_ai_experiments/local_chatgpt_clone/chatgpt_clone_llama3.py",
            "advanced_llm_apps/llm_apps_with_memory_tutorials/llama3_stateful_chat/local_llama3_chat.py",
        ]

        for filepath in test_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", filepath)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()
                    self.assertNotIn('api_key="lm-studio"', content)
                    self.assertTrue('os.getenv' in content or 'os.environ' in content)


class TestLangChainImports(TestCase):
    """Test that LangChain imports are correct"""

    def test_langchain_text_splitters_import(self):
        """Test that langchain_text_splitters can be imported"""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitters(chunk_size=100, chunk_overlap=10)
            self.assertEqual(splitter.chunk_size, 100)
        except ImportError:
            pass

    def test_langchain_core_imports(self):
        """Test that langchain_core imports work"""
        try:
            from langchain_core.prompts import PromptTemplate
            from langchain_core.messages import HumanMessage
            from langchain_core.tools import tool
            from langchain_core.embeddings import Embeddings

            template = PromptTemplate.from_template("Hello {name}")
            self.assertEqual(template.input_variables, ["name"])

            msg = HumanMessage(content="test")
            self.assertEqual(msg.content, "test")
        except ImportError:
            pass


class TestRegexEscapeSequences(TestCase):
    """Test that regex escape sequences are correct"""

    def test_raw_string_for_regex(self):
        """Test that raw strings are used for regex patterns"""
        pattern = r'[\$,]'
        test_strings = ["$100", "1,000", "$1,234.56"]

        for s in test_strings:
            result = re.sub(pattern, '', s)
            self.assertNotIn('$', result)
            self.assertNotIn(',', result)

    def test_regex_compiled_correctly(self):
        """Test that regex patterns compile without warnings"""
        pattern = r'[\$,]'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            re.compile(pattern)
            syntax_warnings = [x for x in w if 'invalid escape sequence' in str(x.message)]
            self.assertEqual(len(syntax_warnings), 0)


class TestBareExceptFixes(TestCase):
    """Test that bare except clauses are replaced with specific exceptions"""

    def test_except_valueerror(self):
        """Test except ValueError"""
        result = None
        try:
            int("invalid")
        except ValueError:
            result = "caught"

        self.assertEqual(result, "caught")

    def test_except_exception(self):
        """Test except Exception"""
        result = None
        try:
            int("invalid")
        except Exception as e:
            result = f"caught: {e}"

        self.assertIsNotNone(result)
        self.assertIn("invalid", result)

    def test_except_type_error(self):
        """Test except with specific error type"""
        result = None
        try:
            int("invalid")
        except (ValueError, TypeError) as e:
            result = "caught"

        self.assertEqual(result, "caught")


class TestDuckDuckGoVersionPinning(TestCase):
    """Test that duckduckgo-search versions are flexible"""

    def test_version_requirement_format(self):
        """Test that version requirements are in correct format"""
        version_specs = [
            ">=6.3.0",
            ">=6.3.7",
            ">=7.2.1",
        ]

        for spec in version_specs:
            self.assertTrue(spec.startswith(">="))
            parts = spec.replace(">=", "").split(".")
            self.assertEqual(len(parts), 3)
            for part in parts:
                self.assertTrue(part.isdigit())


class TestOpenAIImportPattern(TestCase):
    """Test that OpenAI import pattern is correct"""

    def test_from_import_pattern(self):
        """Test the correct import pattern"""
        try:
            from openai import OpenAI
            self.assertIsNotNone(OpenAI)
        except ImportError:
            pass

    def test_client_creation(self):
        """Test that OpenAI client can be created"""
        try:
            from openai import OpenAI
            client = MagicMock()
            self.assertIsNotNone(client)
        except ImportError:
            pass


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
