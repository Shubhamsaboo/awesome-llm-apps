import asyncio
import os
import subprocess
import sys

import pytest

import main


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    monkeypatch.setenv("ADSCRAWL_API_KEY", "offline-adscrawl-key")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-openai-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


class FakeReader:
    def __init__(self, values=None, error=None):
        self.calls = []
        self.values = values or {}
        self.error = error

    async def ainvoke(self, payload):
        self.calls.append(payload)
        if self.error:
            raise self.error
        return self.values.get(payload["url"], "content")


def test_dedup_and_max_urls():
    assert main.dedupe_urls(["a", "a", "b"]) == ["a", "b"]
    with pytest.raises(SystemExit):
        main.parse_args(
            [
                "--url",
                "a",
                "--url",
                "b",
                "--url",
                "c",
                "--url",
                "d",
                "--url",
                "e",
                "--url",
                "f",
                "--fetch-only",
            ]
        )


def test_fetches_each_unique_url_once_sequentially():
    reader = FakeReader({"https://a.test": "A", "https://b.test": "B"})
    result = asyncio.run(
        main.fetch_sources(
            ["https://a.test", "https://a.test", "https://b.test"], "markdown", reader=reader
        )
    )
    assert list(result) == ["https://a.test", "https://b.test"]
    assert [call["url"] for call in reader.calls] == ["https://a.test", "https://b.test"]


def test_unknown_citation_rejected():
    answer = main.EvidenceAnswer(
        answer="x",
        sufficient_evidence=True,
        citations=[{"url": "https://evil.test", "quote": "x"}],
    )
    with pytest.raises(ValueError):
        main.validate_answer(answer, {"https://ok.test"})


def test_sufficient_answer_requires_citation():
    with pytest.raises(ValueError):
        main.validate_answer(main.EvidenceAnswer(answer="x", sufficient_evidence=True), set())


def test_help_works_without_keys():
    env = os.environ.copy()
    env.pop("ADSCRAWL_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    proc = subprocess.run(
        [sys.executable, "main.py", "--help"], capture_output=True, text=True, env=env
    )
    assert proc.returncode == 0
    assert "--fetch-only" in proc.stdout


def test_fetch_only_requires_no_model(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setattr(
        main,
        "fetch_sources",
        lambda *a, **k: asyncio.sleep(0, result={"https://a.test": "article"}),
    )
    args = main.parse_args(["--url", "https://a.test", "--fetch-only"])
    assert asyncio.run(main.run(args)) == 0
    assert "article" in capsys.readouterr().out


def test_failure_is_not_retried_and_error_does_not_expose_secret(monkeypatch, capsys):
    secret = "test-secret-value"
    reader = FakeReader(error=RuntimeError(secret))
    original_fetch = main.fetch_sources

    async def fake_fetch(*args, **kwargs):
        return await original_fetch(["https://a.test"], "markdown", reader=reader)

    monkeypatch.setenv("ADSCRAWL_API_KEY", secret)
    monkeypatch.setattr(main, "fetch_sources", fake_fetch)
    args = main.parse_args(["--url", "https://a.test", "--fetch-only"])
    assert asyncio.run(main.run(args)) == 1
    assert len(reader.calls) == 1
    assert secret not in capsys.readouterr().err


def test_truncation_marker():
    assert "[TRUNCATED" in main.bounded_text("abcdef", 3)
    assert main.bounded_text("abc", 3) == "abc"
    with pytest.raises(SystemExit):
        main.parse_args(["--url", "https://a.test", "--fetch-only", "--max-chars", "100001"])


def test_success_mock_pipeline(monkeypatch, capsys):
    monkeypatch.setattr(
        main,
        "fetch_sources",
        lambda *a, **k: asyncio.sleep(0, result={"https://a.test": "evidence"}),
    )

    class FakeChain:
        async def ainvoke(self, payload):
            assert payload["question"] == "What?"
            assert "evidence" in payload["evidence"]
            return {
                "answer": "Yes",
                "sufficient_evidence": True,
                "citations": [{"url": "https://a.test", "quote": "evidence"}],
            }

    monkeypatch.setattr(main, "build_chain", lambda model: FakeChain())
    args = main.parse_args(
        ["--url", "https://a.test", "--question", "What?", "--model", "test-model"]
    )
    assert asyncio.run(main.run(args)) == 0
    assert '"answer": "Yes"' in capsys.readouterr().out


@pytest.mark.parametrize("name", ["OPENAI_API_KEY", "ADSCRAWL_API_KEY"])
def test_missing_key_rejected_before_fetch(monkeypatch, name):
    monkeypatch.delenv(name)
    calls = []
    monkeypatch.setattr(main, "fetch_sources", lambda *a, **k: calls.append(1))
    args = main.parse_args(
        ["--url", "https://a.test", "--question", "What?", "--model", "test-model"]
    )
    assert asyncio.run(main.run(args)) == 2
    assert calls == []


def test_invalid_second_url_rejected_before_any_fetch(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "fetch_sources", lambda *a, **k: calls.append(1))
    args = main.parse_args(
        ["--url", "https://a.test", "--url", "ftp://invalid.test", "--fetch-only"]
    )
    assert asyncio.run(main.run(args)) == 2
    assert calls == []


@pytest.mark.parametrize("name", ["OPENAI_API_KEY", "ADSCRAWL_API_KEY"])
def test_placeholder_key_rejected_before_fetch(monkeypatch, name):
    monkeypatch.setenv(name, "YOUR_" + name)
    calls = []
    monkeypatch.setattr(main, "fetch_sources", lambda *a, **k: calls.append(1))
    args = main.parse_args(
        ["--url", "https://a.test", "--question", "What?", "--model", "test-model"]
    )
    assert asyncio.run(main.run(args)) == 2
    assert calls == []


def test_model_has_no_automatic_retries(monkeypatch):
    import langchain_openai
    from langchain_core.runnables import RunnableLambda

    seen = {}

    class DummyModel:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def with_structured_output(self, schema):
            assert schema is main.EvidenceAnswer
            return RunnableLambda(lambda value: {"answer": "none", "sufficient_evidence": False})

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", DummyModel)
    main.build_chain("test-model")
    assert seen["max_retries"] == 0
    assert seen["timeout"] == 120
