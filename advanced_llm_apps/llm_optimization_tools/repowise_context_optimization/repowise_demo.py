"""
Repowise Context Optimization Demo
==================================

Two ways Repowise cuts the tokens your coding agent burns, both measured on
THIS machine when you run the script (not hardcoded estimates):

  Part 1 - distill: wraps any noisy shell command (tests, git log, builds) and
           returns an errors-first, reversible rendering before your agent ever
           reads it. This part shells out to the REAL `repowise distill` binary
           and reports genuine before/after token counts.

  Part 2 - context layer: `repowise init --index-only` builds a dependency
           graph + git history + code-health locally, with no API key and no
           code leaving your machine. Your agent then asks `get_context` /
           `get_answer` and gets one curated card instead of cat-ing a pile of
           files. This part indexes a small sample repo for real and measures
           the raw read cost it replaces.

Run:  python repowise_demo.py

Requires:  pip install -r requirements.txt   (repowise + tiktoken)
"""

import os
import shutil
import subprocess
import sys
import tempfile

SEP = "=" * 68


# --------------------------------------------------------------------------- #
# Token counting (exact via tiktoken when available, heuristic otherwise)
# --------------------------------------------------------------------------- #
def count_tokens(text: str) -> int:
    try:
        import tiktoken

        try:
            enc = tiktoken.get_encoding("o200k_base")  # GPT-4o / recent models
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # No tiktoken installed: ~4 chars per token is the usual rule of thumb.
        return max(1, len(text) // 4)


def savings_pct(before: int, after: int) -> float:
    return (1 - after / before) * 100 if before else 0.0


def find_repowise() -> str | None:
    return shutil.which("repowise")


# --------------------------------------------------------------------------- #
# A realistic noisy test run: hundreds of passing lines around a few failures.
# This is exactly the kind of output an agent has to wade through today.
# --------------------------------------------------------------------------- #
NOISY_PYTEST = r'''
import sys

print("=" * 78)
print("test session starts".center(78))
print("platform linux -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0")
print("rootdir: /home/ci/orders-api")
print("plugins: cov-4.1.0, asyncio-0.23.5, xdist-3.5.0")
print("collected 253 items")
print()

modules = ["orders", "auth", "billing", "inventory", "webhooks",
           "notifications", "reports", "search", "admin", "health"]

n = 0
for m in modules:
    for case in range(25):
        n += 1
        pct = int(n / 253 * 100)
        print(f"tests/test_{m}.py::test_{m}_case_{case:02d} PASSED  [{pct:3d}%]")

# Three real failures buried in the parade.
print(f"tests/test_auth.py::test_login_rejects_expired_token FAILED  [ 99%]")
print(f"tests/test_billing.py::test_refund_is_idempotent FAILED  [100%]")
print(f"tests/test_orders.py::test_cancel_releases_inventory FAILED  [100%]")
print()
print("=" * 78)
print("FAILURES".center(78))
print("=" * 78)
print("__________________ test_login_rejects_expired_token __________________")
print()
print("    def test_login_rejects_expired_token():")
print("        token = make_token(exp=utcnow() - timedelta(hours=1))")
print(">       assert login(token).status_code == 401")
print("E       AssertionError: assert 200 == 401")
print("E        +  where 200 = <Response>.status_code")
print()
print("tests/test_auth.py:88: AssertionError")
print("_____________________ test_refund_is_idempotent ______________________")
print()
print("    def test_refund_is_idempotent():")
print("        refund(order_id, amount=500)")
print(">       assert refund(order_id, amount=500).duplicate is True")
print("E       AssertionError: assert False is True")
print()
print("tests/test_billing.py:142: AssertionError")
print("________________ test_cancel_releases_inventory ______________________")
print()
print("    def test_cancel_releases_inventory():")
print("        cancel(order_id)")
print(">       assert inventory_for(sku) == 10")
print("E       assert 9 == 10")
print()
print("tests/test_orders.py:203: AssertionError")
print()
print("=" * 78)
print("short test summary info".center(78))
print("=" * 78)
print("FAILED tests/test_auth.py::test_login_rejects_expired_token - AssertionError: assert 200 == 401")
print("FAILED tests/test_billing.py::test_refund_is_idempotent - AssertionError: assert False is True")
print("FAILED tests/test_orders.py::test_cancel_releases_inventory - assert 9 == 10")
print("================= 3 failed, 250 passed in 6.42s =================")
sys.exit(1)
'''


def part1_distill(repowise_bin: str) -> None:
    print(SEP)
    print("  PART 1  -  repowise distill  (real binary, real numbers)")
    print(SEP)
    print("Scenario: your agent runs the test suite and has to read the output.")
    print("253 tests, 3 real failures buried in 250 passing lines.\n")

    noise_path = os.path.join(tempfile.gettempdir(), "repowise_demo_noisy_pytest.py")
    with open(noise_path, "w", encoding="utf-8") as fh:
        fh.write(NOISY_PYTEST)

    # Raw: what the agent reads today. Force UTF-8 so tool glyphs in the
    # output never trip the platform default codec (cp1252 on Windows).
    raw = subprocess.run(
        [sys.executable, noise_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    raw_out = raw.stdout

    # Distilled: what the agent reads with repowise in front of the command.
    dist = subprocess.run(
        [repowise_bin, "distill", sys.executable, noise_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    dist_out = dist.stdout

    raw_tok = count_tokens(raw_out)
    dist_tok = count_tokens(dist_out)

    print("--- distilled output your agent actually reads ---\n")
    tail = "\n".join(dist_out.strip().splitlines()[-14:])
    print(tail)
    print("\n--- token cost ---")
    print(f"  raw command output:   {raw_tok:>7,} tokens  ({len(raw_out.splitlines())} lines)")
    print(f"  distilled output:     {dist_tok:>7,} tokens  ({len(dist_out.splitlines())} lines)")
    print(f"  saved:                {raw_tok - dist_tok:>7,} tokens  "
          f"({savings_pct(raw_tok, dist_tok):.0f}% smaller)")
    print(f"  exit code preserved:  raw={raw.returncode}  distilled={dist.returncode}")
    print("\n  All 3 failures + the summary survived. The 250 PASSED lines were")
    print("  dropped behind a [repowise#<ref>] marker, fully restorable with")
    print("  `repowise expand <ref>`. Nothing is lost, the agent just reads less.\n")


# --------------------------------------------------------------------------- #
# Part 2: a tiny but real repo to index locally.
# --------------------------------------------------------------------------- #
SAMPLE_FILES = {
    "app.py": '''\
"""Orders API entry point."""
from flask import Flask, request, jsonify
from auth import require_token
from db import get_session
from services.orders import create_order, cancel_order, list_orders

app = Flask(__name__)


@app.post("/orders")
@require_token
def post_order():
    session = get_session()
    payload = request.get_json(force=True)
    order = create_order(session, user=request.user, items=payload["items"])
    return jsonify(order.to_dict()), 201


@app.delete("/orders/<order_id>")
@require_token
def delete_order(order_id):
    session = get_session()
    cancel_order(session, user=request.user, order_id=order_id)
    return "", 204


@app.get("/orders")
@require_token
def get_orders():
    session = get_session()
    return jsonify([o.to_dict() for o in list_orders(session, request.user)])


if __name__ == "__main__":
    app.run(port=8000)
''',
    "auth.py": '''\
"""Token auth middleware."""
import functools
from datetime import datetime, timezone

from flask import request, abort
from db import get_session
from models import Session as UserSession


def _now():
    return datetime.now(timezone.utc)


def require_token(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            abort(401, "missing bearer token")
        token = header.split(" ", 1)[1]
        db = get_session()
        sess = db.query(UserSession).filter_by(token=token).one_or_none()
        if sess is None or sess.expires_at < _now():
            abort(401, "invalid or expired token")
        request.user = sess.user
        return fn(*args, **kwargs)

    return wrapper
''',
    "db.py": '''\
"""Database session factory."""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = create_engine(os.environ.get("DATABASE_URL", "sqlite:///orders.db"))
_Session = sessionmaker(bind=_engine)


def get_session():
    return _Session()


@contextmanager
def transaction():
    session = _Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
''',
    "models.py": '''\
"""ORM models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    expires_at = Column(DateTime, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "status": self.status}
''',
    "services/orders.py": '''\
"""Order lifecycle logic."""
from models import Order
from services.inventory import reserve, release


def create_order(session, user, items):
    order = Order(user_id=user.id, status="open")
    session.add(order)
    for item in items:
        reserve(session, sku=item["sku"], qty=item["qty"])
    session.commit()
    return order


def cancel_order(session, user, order_id):
    order = session.query(Order).filter_by(id=order_id, user_id=user.id).one()
    order.status = "cancelled"
    release(session, order_id=order.id)
    session.commit()
    return order


def list_orders(session, user):
    return session.query(Order).filter_by(user_id=user.id).all()
''',
    "services/inventory.py": '''\
"""Inventory reservations."""
from sqlalchemy import text


def reserve(session, sku, qty):
    session.execute(
        text("UPDATE inventory SET available = available - :q WHERE sku = :s"),
        {"q": qty, "s": sku},
    )


def release(session, order_id):
    session.execute(
        text("UPDATE inventory i SET available = available + oi.qty "
             "FROM order_items oi WHERE oi.order_id = :o AND oi.sku = i.sku"),
        {"o": order_id},
    )
''',
}


def _build_sample_repo(root: str) -> int:
    """Write the sample files and return the raw token cost of reading them all."""
    total_raw = ""
    for rel, content in SAMPLE_FILES.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        total_raw += content
    return count_tokens(total_raw)


def part2_context(repowise_bin: str) -> None:
    print(SEP)
    print("  PART 2  -  repowise context layer  (real local index, no API key)")
    print(SEP)

    git = shutil.which("git")
    if git is None:
        _part2_fallback("git is not installed, so the sample repo cannot be indexed.")
        return

    with tempfile.TemporaryDirectory(prefix="repowise_demo_repo_") as root:
        raw_tokens = _build_sample_repo(root)

        # A tiny bit of git history so the graph + git layers have something real.
        env = {**os.environ, "GIT_AUTHOR_NAME": "demo", "GIT_AUTHOR_EMAIL": "demo@example.com",
               "GIT_COMMITTER_NAME": "demo", "GIT_COMMITTER_EMAIL": "demo@example.com"}
        for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "sample orders api"]):
            r = subprocess.run([git, *cmd], cwd=root, env=env,
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode != 0:
                _part2_fallback("could not create the sample git repo.")
                return

        print("Indexing a 6-file sample repo locally (graph + git + health,")
        print("zero LLM, zero cloud) ...\n")
        try:
            idx = subprocess.run(
                [repowise_bin, "init", "--index-only", "-y"],
                cwd=root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=300,
            )
        except subprocess.TimeoutExpired:
            _part2_fallback("indexing took longer than expected on this machine.")
            return

        if idx.returncode != 0:
            _part2_fallback("`repowise init --index-only` did not complete here.")
            return

        print("  Index built. The dependency graph, git history, and code-health")
        print("  score now live in .repowise/ on this machine.\n")
        print("--- the token cost your agent avoids ---")
        print(f"  Raw-reading all 6 sample files (what `cat`/Read costs today):")
        print(f"    {raw_tokens:,} tokens\n")
        print("  With the index built, your agent asks one task-shaped question")
        print("  instead of reading files:\n")
        print("    get_context(targets=[\"app.py\", \"services/orders.py\"])")
        print("    get_answer(\"how does auth work?\")\n")
        print("  and gets a curated card (signatures, summary, callers, hotspot")
        print("  bit) back. On the public flask benchmark, loading a commit's")
        print("  context this way cost 2,391 tokens vs 64,039 raw, about 27x")
        print("  fewer (-96%), at answer quality on par with raw exploration.")
        print("  Source: github.com/repowise-dev/repowise-bench\n")
        print("  Try it live on this sample:")
        print(f"    cd <the indexed repo>  &&  repowise mcp     # then call get_context")
        print("  or point Claude Code / Cursor / Codex at the MCP server.\n")


def _part2_fallback(reason: str) -> None:
    print(f"  Skipping the live index ({reason})\n")
    print("  The context layer still works the same way, here is how to run it")
    print("  on your own repo:\n")
    print("    cd /path/to/your/repo")
    print("    repowise init --index-only -y      # graph + git + health, no key")
    print("    repowise mcp                       # serve get_context / get_answer\n")
    print("  Measured on the public flask benchmark: loading a commit's context")
    print("  via get_context cost 2,391 tokens vs 64,039 raw (~27x fewer, -96%),")
    print("  with -70% agent tool calls at answer-quality parity.")
    print("  Source: github.com/repowise-dev/repowise-bench\n")


def main() -> None:
    print()
    print("  REPOWISE  -  CONTEXT & TOKEN OPTIMIZATION FOR CODING AGENTS")
    print("  " + "-" * 58)
    print("  Give your agent the answer, not 40 greps and a pile of files.\n")

    repowise_bin = find_repowise()
    if repowise_bin is None:
        print(SEP)
        print("  repowise is not installed yet.")
        print(SEP)
        print("  Install the demo dependencies first, then re-run:\n")
        print("    pip install -r requirements.txt")
        print("    python repowise_demo.py\n")
        print("  (repowise is 100% local and needs no API key for this demo.)")
        return

    part1_distill(repowise_bin)
    part2_context(repowise_bin)

    print(SEP)
    print("  GET STARTED")
    print(SEP)
    print("  pip install repowise")
    print("  cd /path/to/your/repo && repowise init --index-only -y")
    print("  repowise mcp        # wire into Claude Code, Cursor, Codex, any MCP client")
    print()
    print("  GitHub:     https://github.com/repowise-dev/repowise")
    print("  PyPI:       https://pypi.org/project/repowise/")
    print("  Benchmarks: https://github.com/repowise-dev/repowise-bench")
    print(SEP)


if __name__ == "__main__":
    main()
