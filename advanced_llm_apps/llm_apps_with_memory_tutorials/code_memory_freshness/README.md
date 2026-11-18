# 🧭 Code Memory Freshness Lab

A saved finding says something about a particular version of some code. What
happens when that function moves, its implementation changes, or a helper stops
honouring the assumption?

This Streamlit tutorial makes that question the application. It anchors a finding
to Git and Python AST fingerprints, detects changes, asks a model to recheck the
finding against current source, and records the verdict separately from the
original note. SQLite is the only store; no memory service is needed.

**A changed function does not automatically make a finding wrong. An unchanged
function does not prove it is still right.**

## What you will build

The six included scenarios cover:

| Scenario | Detection | Expected treatment of the saved finding |
| --- | --- | --- |
| Same source | `unchanged` | Reuse within its original, limited scope |
| Refactored cache return | `changed` | Recheck, then reuse: the guarantee survives |
| New callback before the cache guard | `changed` | Reject the old no-side-effects claim |
| Function moved and renamed | `moved` | Inspect the unique matching body at its new location |
| Same function, changed helper | `context_changed` | Reject: the helper no longer deduplicates |
| Removed implementation | `unresolved` | Request more evidence rather than reuse the note |

The examples concern sequential, completed requests in a toy in-memory cache.
They make no claim about real payment safety, concurrency, crashes or durable
idempotency.

## Run it

Requires Python 3.11+ and Git.

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/code_memory_freshness
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run freshness_lab.py
```

Select a scenario, choose OpenAI or Anthropic, enter your API key and model, then
click **Recheck and review**. For Bedrock, enter a model or inference-profile ID
and use your normal AWS credential chain; no key is entered in the app. Calls are
paid by your provider account. The source inspector runs without a model, so you
can explore every fingerprint state before making a call.

The app creates an isolated temporary Git repository for each scenario. The left
pane shows the original function; the right shows current source, including its
helpers. Switching scenarios starts a separate sandbox. It never executes the
inspected Python code, and it never changes your own checkout.

## How the technique works

1. **Anchor once.** Save the finding, qualified symbol, relative path, commit,
   Git blob hash, AST shape and a fingerprint of the inspected Python sources.
   `Note` is immutable, and SQLite keeps this anchor separate from check history.
2. **Inspect the present.** Prefer the exact path and qualified name. If they are
   gone, a unique matching AST body is a move/rename candidate. Several matches
   are ambiguous; the inspector does not arbitrarily choose one.
3. **Detect surrounding changes too.** A function's body can stay identical while
   a helper changes. The repository-source fingerprint triggers a recheck in this
   case, trading a coarse signal for a small, readable implementation.
4. **Recheck against evidence.** The model receives original and current code,
   then returns `supported`, `contradicted` or `unclear`. A supported or
   contradicted verdict must quote current source. The app checks the quotation,
   not the truth of the model's reasoning.
5. **Review the question.** Current source remains the authority. The reviewer
   returns `reuse`, `reject` or `recheck`, with a source quotation. It can disagree
   with the rechecker; a model verdict is not a proof or an approval gate.
6. **Keep the audit trail.** Append the checked snapshot and both responses to
   SQLite. Do not silently replace the original finding or its anchor.

Most of the application implements these steps. The provider wrapper and UI are
small boundaries around them; the technique works without any hosted memory tool.

## Try your own small Python checkout

The same functions are importable without launching Streamlit:

```python
from pathlib import Path
from freshness_lab import Model, Store, anchor, review

repo = Path("/path/to/your/checkout")
store = Store("findings.sqlite3")
try:
    note = anchor(repo, "src/cache.py", "Cache.get", "An expired entry is not returned.")
    store.save(note)
    # After changing the checkout, or in another process after loading store.notes():
    ask = Model("OpenAI", "gpt-4.1-mini")  # reads OPENAI_API_KEY
    result = review(ask, repo, note, "Does this change preserve the finding?")
    store.record(note, result)
finally:
    store.close()
```

Persist the note **before** changing the source. Loading an existing note from
`store.notes()` preserves its old anchor; calling `anchor()` after the change
would capture the new code instead. `Store.save()` does not overwrite an existing
anchor with the same ID.

The reader accepts at most 100 tracked or unignored Python files, 50 KB each and
150,000 source characters in total. It refuses source paths that escape the checkout. Use a small
checkout or purpose-built fixture; this example does not truncate hidden context
and then claim to have checked it.

## Compare review policies

`evaluate.py` runs the same question, finding and current source under three
policies, shuffling their order within every case/repeat pair:

- **`blind`:** one review call with the saved note and current source.
- **`always`:** recheck every note, then review. This is the extra-compute control.
- **`freshness`:** recheck when a fingerprint or location changes, then review.
  An unchanged snapshot uses only the review call.

The final reviewer uses the same instructions and current source in all arms. It
is never told to trust stale notes or to produce a particular reference answer.
Both rechecking arms use the same recheck prompt. Their additional calls, tokens
and time are included in their totals.

```bash
python evaluate.py --provider Bedrock --region us-east-1 \
  --model YOUR_INFERENCE_PROFILE_ID --repeats 3 --output results/my-run
```

For OpenAI or Anthropic, pass that provider and a model name, with its usual API
key environment variable. Output directories must be new. The protocol stores
source/case hashes and ordering seed; `attempts.jsonl` retains every response,
provider token usage and failure. A failed operation or cleanup stops the run after preserving the attempt and
usage, without retrying or hiding it. Cleanup errors are recorded separately from
operation errors. `summary.json` is written only for a complete run.

The reference labels grade handling of a saved note, **not general code-review
quality**. These six authored teaching cases are not a public-repository benchmark.
A correct answer can still have a weak explanation. File/AST hashes do not prove
semantic equivalence, and this experiment cannot establish a broad quality win.

### Recorded example run

The recorded run is pinned to
[commit `c85c623`](https://github.com/zlareb1/awesome-llm-apps/commit/c85c623c31391164a56f0509d8f363ec082eb48f).
Its evaluator hash is `3217140168eaddcd339d646c7e04b5820fccc7de1d0a2f815d161a109f65e241`.
The evaluator also preserves responses when client cleanup fails; that failure-path
change was checked offline after the recorded run. The application, cases and
model prompts used for the recorded result are unchanged.

The checked-in [protocol](evaluation/sample_run/protocol.json),
[all 54 responses](evaluation/sample_run/attempts.jsonl) and
[summary](evaluation/sample_run/summary.json) come from three repeats of the six
teaching cases using Sonnet 5.5 through Bedrock. There were no failed attempts or
retries. Source and case hashes identify exactly what was evaluated.

| Policy | Reference actions correct | Model calls | Reported input tokens | Output tokens | Total review seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Blind review | 18/18 | 18 | 8,892 | 3,256 | 30.50 |
| Recheck everything | 18/18 | 36 | 21,333 | 6,114 | 56.82 |
| Freshness routing | 18/18 | 33 | 19,085 | 5,280 | 50.55 |

**This run shows no accuracy improvement.** Blind review already catches the stale
claims when given these short, complete source contexts. Rechecking adds cost and
latency. Freshness routing avoids the unchanged-case rechecks compared with
rechecking everything; it remains more expensive than blind review here.

The changed-but-valid case remains `reuse`, the extra-callback and changed-helper
cases become `reject`, and the missing-target case requests another check, under
all three policies. Read the responses to compare their explanations; matching a
reference action is not a complete assessment of reasoning quality. No percentage
here estimates performance on production code or another model.

Times include provider-client initialization, inspection and every model call
within each review, but exclude shared fixture construction. Raw calls also
include native provider usage fields. Token counts are not a provider bill.

### Local checks

```bash
pip install pytest
python -m pytest test_freshness.py -q
```

The offline checks cover Git/AST states, ambiguous moves, identity of the selected
symbol, path boundaries, SQLite history, routing and a Streamlit AppTest with a
mocked provider. Mocked UI validation is separate from the real-model evaluation.

## Limits and shared storage

Only Python source is fingerprinted. Dependency versions, runtime configuration,
external services, generated files and changes outside the inspected checkout can
invalidate a finding without changing these fingerprints. Move detection is
syntactic and deliberately abstains on ambiguous matches. Every recheck is a model
judgment; sensitive workflows still need their own tests and approval policy.

For sharing anchored findings between agents, the `Note` JSON can also be stored
in [ClickHouse Loom](https://github.com/ClickHouse/loom), alongside its file path and
code links. Storage is separate from this example's change detector and recheck
policy. This tutorial uses SQLite throughout and does not claim a tested Loom
backend or a hosted service dependency.
