"""
LLM Panel Agent Team: several models review the same thing independently, then argue.

Round 1  Every model on the panel gets the identical prompt at the same time. None of
         them can see the others. Each answer is printed in full as it lands.
Round 2  (--rebut) Each model is shown the OTHER answers, anonymised as "Reviewer A",
         "Reviewer B", ... in a per-model shuffled order, and asked to UPHOLD, REJECT,
         CONCEDE or MISSED on every finding that touches its own. Positions that cite a
         finding are then grouped by the finding under dispute.

The point is not a vote. A panel generates candidate defects; a human still checks each
one against the code. What the panel adds over one reviewer is independence (no anchoring
on the first answer) and a second round where a wrong finding has to survive being argued.

Every model is called through OpenRouter with the OpenAI SDK, so one key covers vendors.

    export OPENROUTER_API_KEY=sk-or-...
    python llm_panel_agent_team.py --file sample_diff.patch --rebut

Model ids come from https://openrouter.ai/models; --models takes any of them.
"""

import argparse
import os
import random
import re
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from openai import OpenAI

# One cheap model per vendor, named by OpenRouter's rolling aliases rather than by a
# version. A pinned id (`openai/gpt-5.4-mini`) is the version that was current the day this
# was written, and providers retire versions: the pin would fail for whoever clones this
# months from now, before they ever saw the panel work. Each `-latest` alias "always
# redirects to the latest model in the family", so a default roster keeps resolving. Pin a
# version with --models when you want a run to be reproducible instead of current.
DEFAULT_MODELS = [
    "~openai/gpt-mini-latest",
    "~anthropic/claude-haiku-latest",
    "~google/gemini-flash-latest",
]

MODEL_CATALOG = "https://openrouter.ai/models"

REVIEW_TASK = (
    "Review the following change. Report defects only, as a numbered list, each with the "
    "file and line it is in and one sentence on why it is wrong. If the change needs no "
    "comment at all, say so.\n\n"
)

# The four labels are the contract the grouping step parses. The two rules at the end are
# what stop round two from collapsing into polite agreement.
REBUT_INSTRUCTIONS = (
    "You already reviewed this material independently. Below are the findings of the OTHER "
    "reviewers. They did not see your review, and their identities are withheld from you on "
    "purpose.\n\n"
    "Refer to a finding as <Letter><number>: B7 is Reviewer B's finding 7. Take a position "
    "on each finding that touches yours:\n"
    "  UPHOLD:  B7 -- you stand by your own claim despite theirs; say what proves it.\n"
    "  REJECT:  B7 -- theirs is wrong or overstated; point at the specific code or logic "
    "that makes it wrong.\n"
    "  CONCEDE: B7 -- you were wrong; say exactly what changed your mind.\n"
    "  MISSED:  B7 -- they caught something real that you did not; confirm it against the "
    "code rather than taking their word.\n\n"
    "Start each point with one of those four labels verbatim, then the reference, then your "
    "argument.\n\n"
    "Two rules that matter more than agreeing:\n"
    "1. Do NOT concede merely because someone disagreed with you. Concede only when you can "
    "point at what proves you wrong. A correct finding stays correct when it is unpopular.\n"
    "2. Do NOT invent agreement. If a finding is unverifiable from what you have, say so "
    "instead of endorsing it.\n\n"
    "Reviews from the other reviewers follow.\n\n"
)

# A position is a line that OPENS with one of the four labels; the findings it argues
# about are every reference on that line. Models write the label in whatever markdown they
# favour ("* **UPHOLD: A1**", "1. UPHOLD: Reviewer A1 / Reviewer B3"), so the label match
# tolerates bullets and bold, and the references are collected from the rest of the line
# instead of having to sit immediately after the colon. One line may cite two findings.
POSITION = re.compile(r"^[\s>*\-\d.)]*\**\s*(UPHOLD|REJECT|CONCEDE|MISSED)\b\**\s*:?(.*)$", re.M)
REFERENCE = re.compile(r"\b([A-Z]\d+)\b")


def parse_positions(text: str) -> list:
    """(label, reference) for every finding each position line argues about."""
    out = []
    for label, rest in POSITION.findall(text):
        out += [(label, ref) for ref in REFERENCE.findall(rest)]
    return out


@dataclass
class Answer:
    model: str
    status: str = "ok"          # ok | error
    text: str = ""
    seconds: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    rebuttal: "Answer | None" = None
    positions: list = field(default_factory=list)   # (label, ref) pairs from the rebuttal
    letters: dict = field(default_factory=dict)      # letter -> model, as this judge saw them


def ask(client: OpenAI, model: str, prompt: str, timeout: float) -> Answer:
    """One model, one prompt. A failure is reported in the row, never raised: one judge's
    outage must not take the panel down after the others have been paid for."""
    t0 = time.time()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            extra_body={"usage": {"include": True}},   # OpenRouter returns the billed cost
        )
        text = (r.choices[0].message.content or "").strip()
        if not text:
            return Answer(model, "error", f"empty answer (finish_reason={r.choices[0].finish_reason})",
                          time.time() - t0)
        u = r.usage
        return Answer(model, "ok", text, time.time() - t0,
                      getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0,
                      float(getattr(u, "cost", 0.0) or 0.0))
    except Exception as e:  # reported, not swallowed: the row says what happened
        msg = f"{type(e).__name__}: {e}"
        if getattr(e, "status_code", None) in (400, 404) and "model" in str(e).lower():
            # The one failure a reader hits before they have seen the tool work at all:
            # say where the current ids live rather than leaving them with a raw 404.
            msg += f"\n  -> `{model}` is not a model id OpenRouter serves. Pick a current one from {MODEL_CATALOG}."
        return Answer(model, "error", msg, time.time() - t0)


def round_one(client, models, prompt, timeout) -> list[Answer]:
    print(f"round 1: asking {len(models)} models in parallel\n", flush=True)
    answers = {}
    with ThreadPoolExecutor(len(models)) as ex:
        futures = {ex.submit(ask, client, m, prompt, timeout): m for m in models}
        for f in as_completed(futures):
            a = f.result()
            answers[a.model] = a
            print(f"## {a.model}  ({a.status}, {a.seconds:.1f}s)\n\n{a.text}\n", flush=True)
    return [answers[m] for m in models]


def round_two(client, answers, prompt, timeout) -> None:
    ok = [a for a in answers if a.status == "ok"]
    if len(ok) < 2:
        print("rebuttal round skipped: it needs at least two answers to argue about\n")
        return
    print(f"round 2: {len(ok)} models read each other's findings, anonymised\n", flush=True)

    def one(me: Answer):
        # A fresh shuffle per model: if the letters or their order were fixed, position
        # alone would tell a model which rival wrote which review.
        others = [o for o in ok if o is not me]
        random.shuffle(others)
        letters = {o.model: L for o, L in zip(others, string.ascii_uppercase)}
        me.letters = {L: m for m, L in letters.items()}   # letter -> model, for grouping
        blocks = "\n\n".join(f"### Reviewer {letters[o.model]}\n{o.text}" for o in others)
        p = f"{prompt}\n\n---\n\nYour own review was:\n\n{me.text}\n\n---\n\n{REBUT_INSTRUCTIONS}{blocks}"
        me.rebuttal = ask(client, me.model, p, timeout)
        if me.rebuttal.status == "ok":
            me.positions = parse_positions(me.rebuttal.text)

    with ThreadPoolExecutor(len(ok)) as ex:
        list(ex.map(one, ok))
    for a in ok:
        r = a.rebuttal
        print(f"## {a.model} rebuts  ({r.status}, {r.seconds:.1f}s)\n\n{r.text}\n", flush=True)


def grouped_positions(answers) -> list[str]:
    """Round two, regrouped by the finding argued about instead of by who spoke."""
    rows = {}   # (author model, finding number) -> [(label, by model)]
    for a in answers:
        for lab, ref in a.positions:
            author = a.letters.get(ref[0])
            if author is None:
                continue          # a letter that was not in this model's packet
            row = rows.setdefault((author, int(ref[1:])), [])
            if (lab, a.model) not in row:   # one model arguing a finding twice is one position
                row.append((lab, a.model))
    # A rebuttal that arrived but parsed to nothing is reported, not dropped: otherwise a
    # model whose formatting the parser missed looks exactly like a model that stayed quiet.
    unparsed = [a.model for a in answers if a.rebuttal and a.rebuttal.status == "ok" and not a.positions]
    note = ([f"_No position could be read from the rebuttal of: {', '.join(unparsed)}. "
             "Their round-two text is still in full above._"] if unparsed else [])
    if not rows:
        return ["_No position cited a finding reference, so there is nothing to group._", *note]
    out = ["| finding | positions | contested |", "|---|---|---|"]
    for (author, n), ps in sorted(rows.items()):
        labels = {lab for lab, _ in ps}
        contested = "CONTESTED" if labels & {"REJECT"} and labels & {"UPHOLD", "MISSED"} else ""
        out.append(f"| {author} #{n} | " + "; ".join(f"{lab} ({by})" for lab, by in ps) + f" | {contested} |")
    return out + ([""] + note if note else [])


def scoreboard(answers) -> list[str]:
    out = ["| model | status | time | tokens in/out | cost |", "|---|---|---|---|---|"]
    for a in answers:
        ti, to, c = a.tokens_in, a.tokens_out, a.cost
        if a.rebuttal:
            ti += a.rebuttal.tokens_in; to += a.rebuttal.tokens_out; c += a.rebuttal.cost
        out.append(f"| {a.model} | {a.status} | {a.seconds:.1f}s | {ti:,}/{to:,} | ${c:.4f} |")
    out.append(f"| **total** | | | | **${sum(a.cost + (a.rebuttal.cost if a.rebuttal else 0) for a in answers):.4f}** |")
    return out


def write_panel(path, answers, question, rebut):
    lines = ["# Panel", "", *scoreboard(answers), ""]
    if rebut:
        lines += ["## Positions by finding", "", *grouped_positions(answers), ""]
    lines += ["## Question", "", question, ""]
    for a in answers:
        lines += ["---", "", f"## {a.model}  ({a.status}, {a.seconds:.1f}s)", "", a.text, ""]
        if a.rebuttal:
            lines += [f"### {a.model} in the rebuttal round  ({a.rebuttal.status})", "", a.rebuttal.text, ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--question", help="ask the panel this")
    src.add_argument("--file", help="review this file (a diff, a design doc, a function...)")
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS),
                    help=f"comma-separated model ids from {MODEL_CATALOG} "
                         "(default: one rolling `-latest` alias per vendor)")
    ap.add_argument("--rebut", action="store_true", help="add the anonymised rebuttal round")
    ap.add_argument("--timeout", type=float, default=300, help="seconds per model per round")
    ap.add_argument("--out", default="panel.md", help="where the full panel is written")
    a = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("set OPENROUTER_API_KEY (https://openrouter.ai/keys)")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

    if a.file:
        with open(a.file) as f:
            material = f.read()
        prompt = REVIEW_TASK + f"```\n{material}\n```"
        question = f"Review `{a.file}`"
    else:
        prompt = question = a.question

    models = [m.strip() for m in a.models.split(",") if m.strip()]
    answers = round_one(client, models, prompt, a.timeout)
    if a.rebut:
        round_two(client, answers, prompt, a.timeout)
        print("## Positions by finding\n\n" + "\n".join(grouped_positions(answers)) + "\n")
    print("\n".join(scoreboard(answers)))
    write_panel(a.out, answers, question, a.rebut)
    print(f"\nfull panel written to {a.out}")
    failed = [x.model for x in answers if x.status != "ok"]
    if failed:
        sys.exit(f"{len(failed)} of {len(answers)} models did not answer: {', '.join(failed)}")


if __name__ == "__main__":
    main()
