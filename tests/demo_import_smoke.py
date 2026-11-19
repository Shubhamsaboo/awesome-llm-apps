"""Flag dead phi. and LangChain chat-model imports in Streamlit demo catalogs."""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

CATALOG_ROOTS = ("starter_ai_agents", "rag_tutorials", "advanced_ai_agents")
SKIP_DIR_NAMES = frozenset({"__pycache__", ".venv", "node_modules"})
DENY_EXACT = frozenset({"langchain.chat_models", "langchain.llms", "phi"})
DENY_PREFIX = "phi."
ALLOWLIST_REL = Path("tests") / "fixtures" / "import_smoke_allowlist.txt"


def is_denied(module: str) -> bool:
    if not module:
        return False
    if module in DENY_EXACT:
        return True
    return module.startswith(DENY_PREFIX)


def load_allowlist(
    repo_root: Path, allowlist_path: Optional[Path] = None
) -> Set[str]:
    path = allowlist_path if allowlist_path is not None else repo_root / ALLOWLIST_REL
    if not path.is_file():
        return set()
    out: Set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.add(stripped)
    return out


def _rel_to_root(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path, rel: str) -> List[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return [{"path": rel, "lineno": 0, "module": "<unreadable>"}]
    try:
        tree = ast.parse(source, filename=rel)
        compile(source, rel, "exec", dont_inherit=True)
    except SyntaxError as exc:
        return [{"path": rel, "lineno": int(exc.lineno or 0), "module": "<syntax>"}]
    found: List[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if is_denied(alias.name):
                    found.append(
                        {"path": rel, "lineno": node.lineno, "module": alias.name}
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module is None:
                continue
            if is_denied(module):
                found.append({"path": rel, "lineno": node.lineno, "module": module})
    return found


def walk_catalog(
    roots: Sequence[os.PathLike],
    repo_root: Path,
    allowlist: Optional[Iterable[str]] = None,
) -> List[dict]:
    allowed = (
        set(allowlist)
        if allowlist is not None
        else load_allowlist(repo_root)
    )
    findings: List[dict] = []
    for root in roots:
        root_path = Path(root)
        if not root_path.is_absolute():
            root_path = repo_root / root_path
        if not root_path.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                path = Path(dirpath) / name
                rel = _rel_to_root(path, repo_root)
                if rel in allowed:
                    continue
                findings.extend(scan_file(path, rel))
    return findings


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    repo_root = repo_root_from_here()
    roots: Sequence[os.PathLike] = args if args else list(CATALOG_ROOTS)
    findings = walk_catalog(roots, repo_root)
    for item in findings:
        print(f"{item['path']}:{item['lineno']}: {item['module']}")
    if findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
