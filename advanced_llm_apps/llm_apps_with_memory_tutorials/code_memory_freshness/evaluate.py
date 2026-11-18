"""Small paired demonstration, including a recheck-everything compute control.

The references grade note handling, not full code-review quality. Every mode sees
identical current source. Extra recheck calls are charged to that mode.
"""

import argparse
import hashlib
import json
import random
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from freshness_lab import HERE, Model, prepare_case, review


def run(args):
    cases = json.loads((HERE / "cases.json").read_text())
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)  # never overwrite a previous run
    protocol = {"provider": args.provider, "model": args.model, "region": args.region,
                "repeats": args.repeats, "seed": args.seed,
                "cases_sha256": hashlib.sha256((HERE / "cases.json").read_bytes()).hexdigest(),
                "source_sha256": hashlib.sha256((HERE / "freshness_lab.py").read_bytes()).hexdigest(),
                "max_output_tokens_per_call": 900, "modes": ["blind", "always", "freshness"],
                "started_at": datetime.now(UTC).isoformat(),
                "scope": "Six authored teaching examples; not a public-repository benchmark"}
    (output / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    rng, rows = random.Random(args.seed), []
    # Pair by case/repeat; independently shuffle arm order to avoid one fixed order.
    for repeat in range(args.repeats):
        for key, case in cases.items():
            with tempfile.TemporaryDirectory(prefix="freshness-eval-") as tmp:
                repo = Path(tmp) / "repo"
                note = prepare_case(case, repo)
                modes = list(protocol["modes"])
                rng.shuffle(modes)
                for mode in modes:
                    ask = Model(args.provider, args.model, region=args.region)
                    row = {"case": key, "repeat": repeat, "mode": mode,
                           "expected_action": case["expected_action"]}
                    try:
                        result = review(ask, repo, note, case["question"], mode)
                        row.update(result=result, correct=result["review"]["action"] == case["expected_action"])
                    except Exception as exc:
                        row.update(error_type=type(exc).__name__, correct=False)
                    row["calls"] = ask.calls
                    rows.append(row)
                    # Preserve every response before the next call, including failures.
                    with (output / "attempts.jsonl").open("a") as f:
                        f.write(json.dumps(row) + "\n")
                    print(key, repeat, mode, row.get("result", {}).get("review", {}).get("action", row.get("error_type")))
                    if "error_type" in row:
                        raise RuntimeError("Stopped after a failed attempt; partial results retained")
    summary = {}
    for mode in protocol["modes"]:
        arm = [r for r in rows if r["mode"] == mode]
        calls = [c for r in arm for c in r["calls"]]
        summary[mode] = {"correct": sum(r["correct"] for r in arm), "attempts": len(arm),
                         "model_calls": len(calls),
                         **{k: sum(c[k] for c in calls) for k in ["input_tokens", "output_tokens", "seconds"]}}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["OpenAI", "Anthropic", "Bedrock"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--output", required=True)
    run(parser.parse_args())
