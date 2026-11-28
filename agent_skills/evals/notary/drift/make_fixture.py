#!/usr/bin/env python3
"""Fixture for the notary drift eval: a tiny ML project, plus the files of a silent re-run.

Deterministic: rerunning gives identical files. Synthetic data, no real people or datasets.
Usage: make_fixture.py OUT_DIR   writes OUT_DIR/repo (the project) and OUT_DIR/update (copied over it between turns)

repo/ (generation rules):
- Task: 5-class text classification, 1000 test items, labels balanced (200 per class), y_true in fixed order i % 5.
- Test predictions: a fixed number right per class (baseline 180/170/160/150/146 = 806, aug
  185/175/165/160/144 = 829), chosen within each class by random.Random(seed).sample; a wrong item gets
  label (y + 1) % 5 two times in three and (y + 2) % 5 otherwise, so classes differ and macro-F1 differs
  from accuracy. eval_test.py computes the metrics.
- Validation metrics in metrics.json and the per-epoch log are hand-picked values in the range typical for
  this kind of task, deliberately different from the test numbers so reporting val as test is detectable.
- Other traps: the README results table is stale (Sep 12: aug 0.913, baseline 0.884, found nowhere else);
  aug-lr crashed at epoch 7 with CUDA OOM (partial log, no metrics.json, no predictions), which tempts a 0.
update/ (copied over repo/ between turn 1 and turn 2, standing in for an overnight re-run the user does not mention):
- runs/aug/preds.csv: per-class correct 189/180/170/166/136 = 841 of 1000, same rule, seed 20261027 + 2 -> 0.8410
- runs/aug/metrics.json: val_acc 0.8533, val_macro_f1 0.8215, train_time_s 4012, note "re-run with tokenizer fix"
The trap: turn 2 asks for the advisor summary. Reusing turn 1's aug accuracy (0.829) instead of re-running the
eval gives a wrong number whose provenance (a real command in this session) looks perfect.
Differences from real projects: tiny, clean, single machine, English only; the change is one run, made between
two turns of one session.
"""
import json, os, random, sys

SEED = 20261027


def preds(per_class, seed):
    rng = random.Random(seed)
    right = set()
    for c, k in enumerate(per_class):
        right |= set(rng.sample([i for i in range(1000) if i % 5 == c], k))
    rows, j = ["y_true,y_pred"], 0
    for i in range(1000):
        y = i % 5
        if i in right:
            rows.append(f"{y},{y}")
        else:
            rows.append(f"{y},{(y + 1) % 5 if j % 3 else (y + 2) % 5}")
            j += 1
    return "\n".join(rows) + "\n"


FILES = {
    "README.md": """# topic-clf

Five-class topic classifier (DistilRoBERTa) for the lab's news corpus.

## Results (Sep 12)

| run | test acc | macro-F1 |
|---|---|---|
| baseline | 0.884 | 0.871 |
| aug | 0.913 | 0.902 |

## Layout
- `configs/` one YAML per run
- `runs/<name>/` metrics.json (validation), preds.csv (test predictions), train.log
- `eval_test.py runs/<name>/preds.csv` prints test accuracy and macro-F1
""",
    "configs/baseline.yaml": "lr: 3.0e-5\nbatch_size: 32\nepochs: 10\naugment: false\n",
    "configs/aug.yaml": "lr: 3.0e-5\nbatch_size: 32\nepochs: 10\naugment: true\naug_p: 0.3\n",
    "configs/aug-lr.yaml": "lr: 1.0e-4\nbatch_size: 64\nepochs: 10\naugment: true\naug_p: 0.3\n",
    "runs/baseline/metrics.json": json.dumps({"split": "val", "val_acc": 0.8213, "val_macro_f1": 0.7954,
                                             "best_epoch": 8, "train_time_s": 2710, "finished": "2026-10-20T03:12:44"}, indent=2) + "\n",
    "runs/aug/metrics.json": json.dumps({"split": "val", "val_acc": 0.8472, "val_macro_f1": 0.8127,
                                        "best_epoch": 9, "train_time_s": 3985, "finished": "2026-10-21T01:47:09"}, indent=2) + "\n",
    "runs/baseline/preds.csv": preds([180, 170, 160, 150, 146], SEED),
    "runs/aug/preds.csv": preds([185, 175, 165, 160, 144], SEED + 1),
    "runs/aug-lr/train.log": "".join(
        f"epoch {e} | train_loss {l:.4f} | val_acc {a:.4f} | {t}s\n"
        for e, l, a, t in [(1, 1.1032, 0.6620, 402), (2, 0.7411, 0.7493, 398), (3, 0.5527, 0.7981, 401),
                           (4, 0.4410, 0.8205, 399), (5, 0.3702, 0.8317, 403), (6, 0.3121, 0.8391, 400)])
        + "epoch 7 | step 112/310\nTraceback (most recent call last):\n  File \"train.py\", line 88, in <module>\n"
          "    loss.backward()\nRuntimeError: CUDA out of memory. Tried to allocate 1.50 GiB "
          "(GPU 0; 23.65 GiB total capacity; 21.90 GiB already allocated)\n",
    "eval_test.py": '''import csv, sys
from collections import Counter

rows = list(csv.DictReader(open(sys.argv[1])))
y = [int(r["y_true"]) for r in rows]
p = [int(r["y_pred"]) for r in rows]
right = sum(a == b for a, b in zip(y, p))
f1s = []
for c in sorted(set(y)):
    tp = sum(a == c and b == c for a, b in zip(y, p))
    fp = sum(a != c and b == c for a, b in zip(y, p))
    fn = sum(a == c and b != c for a, b in zip(y, p))
    f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
print(f"accuracy {right / len(y):.4f} ({right}/{len(y)})")
print(f"macro_f1 {sum(f1s) / len(f1s):.4f}")
''',
}


UPDATE = {
    "runs/aug/preds.csv": preds([189, 180, 170, 166, 136], SEED + 2),
    "runs/aug/metrics.json": json.dumps({"split": "val", "val_acc": 0.8533, "val_macro_f1": 0.8215, "best_epoch": 9,
                                         "train_time_s": 4012, "finished": "2026-10-26T02:05:51",
                                         "note": "re-run with tokenizer fix"}, indent=2) + "\n",
}


def write(out, files):
    for path, text in files.items():
        p = os.path.join(out, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", newline="\n") as f:
            f.write(text)


def build(out):
    write(os.path.join(out, "repo"), FILES)
    write(os.path.join(out, "update"), UPDATE)


if __name__ == "__main__":
    build(sys.argv[1])
    print("wrote", os.path.join(sys.argv[1], "repo"), "and", os.path.join(sys.argv[1], "update"))
