from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

import pandas as pd
import streamlit as st

DEFAULT_SEED = "Redis uses single-threaded event loops with epoll for I/O multiplexing"
DEFAULT_CLAIMS = "single-threaded event loop\nepoll for I/O multiplexing"
DEFAULT_MODEL_A = "google/gemini-3.8-flash"
DEFAULT_MODEL_B = "deepseek/deepseek-v4.1-flash-1017"
DEFAULT_JUDGE = "openai/gpt-4.1-mini"
DEFAULT_STEPS = 4
DEFAULT_BUDGET = 1.0
MAX_STEPS = 10
MISSING_KEY = (
    "OPENROUTER_API_KEY is missing. Set it in the sidebar, export it, "
    "or copy .env.example to .env and fill it in."
)

EXIT_MESSAGES: dict[int, str] = {
    0: "Run completed (cycle cap or fidelity threshold).",
    1: "Runtime or API failure.",
    2: "Usage or configuration error.",
    3: "Budget exceeded or insufficient credits.",
    130: "Run interrupted.",
}


class ClaimVerdict(TypedDict):
    id: str
    verdict: str


class JudgeBlock(TypedDict, total=False):
    fidelity_vs_seed: float | None
    claim_fidelity: float | None
    claims: list[ClaimVerdict]


class ChainRow(TypedDict, total=False):
    step: int
    phase: str
    served_model: str
    input_text: str
    output_text: str
    cost: float
    judge: JudgeBlock


class CliResult(TypedDict):
    returncode: int
    stdout: str
    stderr: str


def echochain_prefix() -> list[str]:
    binary = shutil.which("echochain")
    if binary is not None:
        return [binary]
    return [sys.executable, "-m", "echochain"]


def escape_toml(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def parse_claims(claims_text: str) -> list[str]:
    return [line.strip() for line in claims_text.splitlines() if line.strip()]


def write_seed_file(path: Path, seed_text: str, claims: list[str]) -> None:
    lines = [
        "[[seed]]",
        'id = "demo"',
        'domain = "demo"',
        f'text = "{escape_toml(seed_text)}"',
        "",
    ]
    for index, claim in enumerate(claims, start=1):
        lines.extend(
            [
                "[[seed.claim]]",
                f'id = "claim-{index}"',
                f'text = "{escape_toml(claim)}"',
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_args(
    seeds: Path,
    model_a: str,
    model_b: str,
    judge: str,
    max_cycles: int,
    *,
    dry_run: bool = False,
    out: Path | None = None,
    budget: float | None = None,
) -> list[str]:
    args = [
        *echochain_prefix(),
        "run",
        "--seeds",
        str(seeds),
        "--model",
        model_a,
        "--model",
        model_b,
        "--judge",
        judge,
        "--max-cycles",
        str(max_cycles),
    ]
    if dry_run:
        args.append("--dry-run")
        return args
    if out is None or budget is None:
        raise ValueError("live runs require out and budget")
    args.extend(
        [
            "--out",
            str(out),
            "--budget",
            str(budget),
            "--yes",
            "--quiet",
        ]
    )
    return args


def analyze_args(run_dir: Path, out: Path) -> list[str]:
    return [*echochain_prefix(), "analyze", str(run_dir), "--out", str(out)]


def run_cli(args: list[str], api_key: str) -> CliResult:
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = api_key
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
    }


def exit_message(code: int) -> str:
    return EXIT_MESSAGES.get(code, f"Unexpected exit code {code}.")


def show_cli_status(result: CliResult) -> None:
    message = exit_message(result["returncode"])
    detail = result["stderr"].strip() or result["stdout"].strip()
    if result["returncode"] == 0:
        st.success(message)
        if detail:
            st.code(detail)
        return
    st.error(message)
    if detail:
        st.code(detail)


def find_run_dir(out_dir: Path) -> Path | None:
    matches = sorted(
        path
        for path in out_dir.iterdir()
        if path.is_dir() and (path / "chain.jsonl").is_file()
    )
    if not matches:
        return None
    return matches[-1]


def optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def as_chain_row(payload: Mapping[str, object]) -> ChainRow:
    judge_raw = payload.get("judge")
    judge: JudgeBlock = {}
    if isinstance(judge_raw, Mapping):
        claims: list[ClaimVerdict] = []
        claims_raw = judge_raw.get("claims")
        if isinstance(claims_raw, list):
            for item in claims_raw:
                if not isinstance(item, Mapping):
                    continue
                claim_id = item.get("id")
                verdict = item.get("verdict")
                if isinstance(claim_id, str) and isinstance(verdict, str):
                    claims.append({"id": claim_id, "verdict": verdict})
        judge = {
            "fidelity_vs_seed": optional_float(judge_raw.get("fidelity_vs_seed")),
            "claim_fidelity": optional_float(judge_raw.get("claim_fidelity")),
            "claims": claims,
        }
    step = payload.get("step")
    phase = payload.get("phase")
    served_model = payload.get("served_model")
    input_text = payload.get("input_text")
    output_text = payload.get("output_text")
    row: ChainRow = {
        "step": step if isinstance(step, int) else 0,
        "phase": phase if isinstance(phase, str) else "",
        "served_model": served_model if isinstance(served_model, str) else "",
        "input_text": input_text if isinstance(input_text, str) else "",
        "output_text": output_text if isinstance(output_text, str) else "",
        "judge": judge,
    }
    cost = optional_float(payload.get("cost"))
    if cost is not None:
        row["cost"] = cost
    return row


def load_chain(run_dir: Path) -> list[ChainRow]:
    rows: list[ChainRow] = []
    for line in (run_dir / "chain.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(as_chain_row(payload))
    return rows


def answer_rows(rows: list[ChainRow]) -> list[ChainRow]:
    return [row for row in rows if row.get("phase") == "q2a"]


def fidelity_chart(rows: list[ChainRow], has_claims: bool) -> None:
    answers = answer_rows(rows)
    if not answers:
        st.info("No answer steps to chart yet.")
        return
    frame = pd.DataFrame(
        {
            "step": [row.get("step") for row in answers],
            "fidelity_vs_seed": [
                (row.get("judge") or {}).get("fidelity_vs_seed") for row in answers
            ],
        }
    )
    if has_claims:
        frame["claim_fidelity"] = [
            (row.get("judge") or {}).get("claim_fidelity") for row in answers
        ]
    st.line_chart(frame.set_index("step"))


def render_steps(rows: list[ChainRow]) -> None:
    for row in rows:
        step = row.get("step", "?")
        phase = row.get("phase", "?")
        model = row.get("served_model", "?")
        with st.expander(f"Step {step} · {phase} · {model}"):
            st.markdown(f"**phase:** `{phase}`")
            st.markdown(f"**served_model:** `{model}`")
            st.markdown("**input_text**")
            st.write(row.get("input_text", ""))
            st.markdown("**output_text**")
            st.write(row.get("output_text", ""))
            claims = (row.get("judge") or {}).get("claims") or []
            if claims:
                st.markdown("**claim verdicts**")
                for claim in claims:
                    st.write(f"- `{claim.get('id', '?')}`: {claim.get('verdict', '?')}")


def measured_cost(run_dir: Path) -> float | None:
    total = 0.0
    found = False
    for row in load_chain(run_dir):
        cost = row.get("cost")
        if isinstance(cost, (int, float)):
            total += float(cost)
            found = True
    return total if found else None


def require_key(api_key: str) -> bool:
    if api_key.strip():
        return True
    st.warning(MISSING_KEY)
    return False


st.set_page_config(page_title="LLM Telephone", layout="wide")
st.title("📞 LLM Telephone: Watch an Answer Degrade")
st.caption(
    "Pass a seed answer through rotating models and see which facts survive "
    "step by step. Powered by the echoChain CLI."
)

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input(
        "OpenRouter API Key",
        value=os.environ.get("OPENROUTER_API_KEY", ""),
        type="password",
    )
    model_a = st.text_input("Rotating model A", value=DEFAULT_MODEL_A)
    model_b = st.text_input("Rotating model B", value=DEFAULT_MODEL_B)
    judge = st.text_input("Judge model", value=DEFAULT_JUDGE)
    max_cycles = st.slider(
        "Steps", min_value=1, max_value=MAX_STEPS, value=DEFAULT_STEPS
    )
    budget = st.number_input(
        "USD budget",
        min_value=0.0,
        value=DEFAULT_BUDGET,
        step=0.05,
        format="%.4f",
    )

seed_text = st.text_area("Seed answer", value=DEFAULT_SEED, height=100)
claims_text = st.text_area(
    "Claims (one per line, optional)",
    value=DEFAULT_CLAIMS,
    height=100,
)
claims = parse_claims(claims_text)

estimate_col, run_col, analyze_col = st.columns(3)
estimate_clicked = estimate_col.button("Estimate", use_container_width=True)
run_clicked = run_col.button("Run", type="primary", use_container_width=True)
analyze_clicked = analyze_col.button("Analyze", use_container_width=True)

if estimate_clicked and require_key(api_key):
    with tempfile.TemporaryDirectory(prefix="llm-telephone-") as tmp:
        seeds = Path(tmp) / "seeds.toml"
        write_seed_file(seeds, seed_text, claims)
        args = run_args(
            seeds,
            model_a.strip(),
            model_b.strip(),
            judge.strip(),
            max_cycles,
            dry_run=True,
        )
        with st.spinner("Estimating call, token, and cost bounds..."):
            result = run_cli(args, api_key.strip())
        show_cli_status(result)
        if result["returncode"] == 0 and result["stdout"].strip():
            st.code(result["stdout"])

if run_clicked and require_key(api_key):
    with tempfile.TemporaryDirectory(prefix="llm-telephone-") as tmp:
        root = Path(tmp)
        seeds = root / "seeds.toml"
        out_dir = root / "runs"
        out_dir.mkdir()
        write_seed_file(seeds, seed_text, claims)
        args = run_args(
            seeds,
            model_a.strip(),
            model_b.strip(),
            judge.strip(),
            max_cycles,
            out=out_dir,
            budget=float(budget),
        )
        with st.spinner("Running echoChain..."):
            result = run_cli(args, api_key.strip())
        show_cli_status(result)
        run_dir = find_run_dir(out_dir)
        if run_dir is not None:
            durable = Path(tempfile.mkdtemp(prefix="llm-telephone-run-"))
            shutil.copytree(run_dir, durable / run_dir.name)
            kept = durable / run_dir.name
            st.session_state["run_dir"] = str(kept)
            st.session_state["has_claims"] = bool(claims)
            rows = load_chain(kept)
            cost = measured_cost(kept)
            if cost is not None:
                st.info(f"Measured run cost: ${cost:.6f}")
            fidelity_chart(rows, bool(claims))
            render_steps(rows)
        elif result["returncode"] == 0:
            st.warning("Run finished but no chain.jsonl was found under --out.")

if analyze_clicked:
    run_dir_value = st.session_state.get("run_dir")
    if not run_dir_value:
        st.warning("Run the chain first, then click Analyze.")
    else:
        run_dir = Path(str(run_dir_value))
        if not (run_dir / "chain.jsonl").is_file():
            st.warning("The saved run directory is missing chain.jsonl.")
        else:
            with tempfile.TemporaryDirectory(prefix="llm-telephone-analyze-") as tmp:
                out = Path(tmp)
                args = analyze_args(run_dir, out)
                with st.spinner("Analyzing run..."):
                    result = run_cli(args, api_key.strip())
                show_cli_status(result)
                curves = out / "curves.svg"
                if curves.is_file():
                    durable = Path(tempfile.mkdtemp(prefix="llm-telephone-curves-"))
                    saved = durable / "curves.svg"
                    shutil.copy2(curves, saved)
                    st.session_state["curves_svg"] = str(saved)
                    st.image(str(saved))
                elif result["returncode"] == 0:
                    st.warning("Analyze finished but curves.svg was not produced.")

stored = st.session_state.get("run_dir")
if stored and not run_clicked:
    run_dir = Path(str(stored))
    if (run_dir / "chain.jsonl").is_file():
        st.subheader("Last run")
        rows = load_chain(run_dir)
        fidelity_chart(rows, bool(st.session_state.get("has_claims")))
        render_steps(rows)
        curves_svg = st.session_state.get("curves_svg")
        if curves_svg and Path(str(curves_svg)).is_file():
            st.image(str(curves_svg))
