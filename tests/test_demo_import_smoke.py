"""Unit tests for the catalog import smoke walker."""
from pathlib import Path

from tests.demo_import_smoke import is_denied, walk_catalog

REPO_ROOT = Path(__file__).resolve().parents[1]
BROKEN = REPO_ROOT / "tests" / "fixtures" / "broken_demo"
GOOD = REPO_ROOT / "tests" / "fixtures" / "good_demo"


def test_broken_demo_flags_phi_and_langchain_chat_models():
    findings = walk_catalog([BROKEN], REPO_ROOT)
    modules = {item["module"] for item in findings}
    assert "phi.agent" in modules
    assert "langchain.chat_models" in modules


def test_good_demo_has_zero_findings():
    findings = walk_catalog([GOOD], REPO_ROOT)
    assert findings == []


def test_phi_prefix_is_aware_and_phillips_is_not(tmp_path):
    (tmp_path / "hit.py").write_text(
        "from phi.tools.zoom import ZoomTool\n", encoding="utf-8"
    )
    (tmp_path / "miss.py").write_text("import phillips\n", encoding="utf-8")
    findings = walk_catalog([tmp_path], tmp_path)
    modules = {item["module"] for item in findings}
    assert "phi.tools.zoom" in modules
    assert "phillips" not in modules
    assert is_denied("phi.tools.zoom")
    assert not is_denied("phillips")
    assert is_denied("phi")
    assert is_denied("langchain.llms")
    assert not is_denied("langchain.chat_models.openai")


def test_live_starter_ai_agents_returns_a_list():
    findings = walk_catalog(["starter_ai_agents"], REPO_ROOT)
    assert isinstance(findings, list)
    if findings:
        first = findings[0]
        raise AssertionError(
            "live catalog denylist hit: "
            f"{first['path']}:{first['lineno']}: {first['module']}"
        )
