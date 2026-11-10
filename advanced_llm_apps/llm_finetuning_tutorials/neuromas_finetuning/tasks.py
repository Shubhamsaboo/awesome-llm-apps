"""
Dataset registry. Six tasks behind one uniform interface:

  ARC, Navigate, Algebra, Physics, Medicine  -> multiple-choice
  HumanEval                                   -> code completion

Each Task exposes:
  load()           -> (train, dev, eval)  lists of Example
  input_text(ex)   -> the question / function prompt
  answer_format    -> suffix appended to a direct prompt ("" for code)
  score(text, ex)  -> bool reward (parse+check for MCQ; unit-test execution for code)
  kind             -> "mcq" | "code"  (selects generation-length profile)
"""
import os, re, subprocess, tempfile, random
from dataclasses import dataclass
from datasets import load_dataset

import config


@dataclass
class Example:
    id: str
    question: str = ""          # MCQ: question+choices ; code: function prompt
    answer: str = ""            # MCQ gold letter / yes-no
    test: str = ""              # code: unit-test block
    entry_point: str = ""       # code: function name


# Per-dataset test (eval) sizes. Actual eval = min(target, EVAL_SIZE) so SMOKE still shrinks.
TEST_SIZE = {"arc": 200, "navigate": 200, "algebra": 100,
             "physics": 102, "medicine": 200, "humaneval": 164}
# If at least this many test rows remain after eval, carve train/dev from them;
# otherwise (eval uses the whole test split) draw train/dev from a separate split.
MIN_TRAIN = 20


def _train_dev(ev, pool):
    """Return (train, dev) from a candidate pool, skipping any example whose question
    appears in eval or repeats another."""
    ev_q = {e.question for e in ev}
    seen = set(); clean = []
    for x in pool:
        if x.question in ev_q or x.question in seen:
            continue
        seen.add(x.question); clean.append(x)
    n_dev = min(config.DEV_SIZE, max(1, len(clean) // 3))
    return clean[n_dev:], clean[:n_dev]


# ======================================================================
# Multiple-choice answer handling
# ======================================================================
AF_ABCD = "Answer with A, B, C, or D.\nAnswer:"
AF_YESNO = "Answer Yes or No.\nAnswer:"


def parse_abcd(text):
    if not text:
        return None
    m = re.search(r'(?:answer|correct)[:\s]*([A-D])', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m2 = re.search(r'\b([A-D])\b', text)
    if m2:
        return m2.group(1).upper()
    return None


def parse_yesno(text):
    if not text:
        return None
    t = text.lower()
    iy, ino = t.find("yes"), t.find("no")
    cands = [(i, v) for i, v in [(iy, "yes"), (ino, "no")] if i != -1]
    return min(cands)[1] if cands else None


def _check(pred, gold):
    if pred is None:
        return False
    return pred.strip().lower() == str(gold).strip().lower()


# ======================================================================
# Code (HumanEval) answer handling - unit-test execution
# ======================================================================
def extract_code(text, prompt):
    if not text:
        return ""
    m = re.search(r'```(?:python)?\s*\n?(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).rstrip()
    out_lines = []
    for line in text.split('\n'):
        if line and not line.startswith(' ') and not line.startswith('\t'):
            stripped = line.strip()
            if stripped == '' or stripped.startswith('#'):
                out_lines.append(line); continue
            break
        out_lines.append(line)
    return '\n'.join(out_lines).rstrip()


def run_test(prompt, completion, test, entry_point, timeout=5):
    full = prompt + "\n" + completion + "\n" + test + f"\ncheck({entry_point})\n"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full); path = f.name
        result = subprocess.run(['python3', path], capture_output=True, timeout=timeout, text=True)
        os.unlink(path)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        try: os.unlink(path)
        except Exception: pass
        return False
    except Exception:
        try: os.unlink(path)
        except Exception: pass
        return False


# ======================================================================
# Loaders
# ======================================================================
def _load_arc():
    test = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test")
    train = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="train")

    def make(item, pre, i):
        ch = item['choices']
        ct = "\n".join([f"{l}. {t}" for l, t in zip(ch['label'], ch['text'])])
        return Example(f"{pre}_{i}", question=item['question'] + "\n" + ct, answer=item['answerKey'])

    pool = [make(test[i], "e", i) for i in range(len(test))]
    random.shuffle(pool)
    ev = pool[:min(TEST_SIZE["arc"], config.EVAL_SIZE)]
    tr_pool = [make(train[i], "t", i) for i in range(len(train))]
    random.shuffle(tr_pool)
    tr, dev = _train_dev(ev, tr_pool[:config.TRAIN_SIZE + config.DEV_SIZE])
    return tr, dev, ev


def _load_navigate():
    ds = load_dataset("lukaemon/bbh", "navigate", split="test", trust_remote_code=True)
    pool = [Example(f"nav_{i}", question=ds[i]['input'], answer=ds[i]['target'].strip().lower())
            for i in range(len(ds))]
    random.shuffle(pool)
    n_ev = min(TEST_SIZE["navigate"], config.EVAL_SIZE)
    ev = pool[:n_ev]
    tr, dev = _train_dev(ev, pool[n_ev:])
    return tr, dev, ev


def _mmlu_loader(subject, target):
    def _to_ex(item, i):
        choices = "\n".join([f"{chr(65 + j)}. {c}" for j, c in enumerate(item['choices'])])
        return Example(f"{subject}_{i}", question=item['question'] + "\n" + choices,
                       answer=chr(65 + item['answer']))

    def _load():
        test = load_dataset("cais/mmlu", subject, split="test")
        pool = [_to_ex(test[i], i) for i in range(len(test))]
        random.shuffle(pool)
        n_ev = min(target, config.EVAL_SIZE)
        ev = pool[:n_ev]
        rest = pool[n_ev:]
        if len(rest) >= MIN_TRAIN:
            cand = rest
        else:
            cand = []
            for sp, off in (("validation", 100000), ("dev", 200000)):
                extra = load_dataset("cais/mmlu", subject, split=sp)
                cand += [_to_ex(extra[i], off + i) for i in range(len(extra))]
            random.shuffle(cand)
        tr, dev = _train_dev(ev, cand)
        return tr, dev, ev
    return _load


def _load_humaneval_eval():
    ds = load_dataset("openai/openai_humaneval", split="test")
    return [Example(id=item['task_id'], question=item['prompt'], test=item['test'],
                    entry_point=item['entry_point']) for item in ds]


def _mbpp_to_example(item, idx):
    code = item.get('code', '') or item.get('source_code', '')
    text = item.get('text', '') or item.get('prompt', '')
    tests = item.get('test_list', [])
    if not code or not tests:
        return None
    sig = re.search(r'^def\s+\w+\s*\([^)]*\)\s*[^:]*:', code, re.MULTILINE)
    if not sig:
        return None
    signature = sig.group(0)
    nm = re.search(r'def\s+(\w+)\s*\(', signature)
    if not nm:
        return None
    ep = nm.group(1)
    examples = []
    for t in tests[:2]:
        cleaned = t.strip().replace('assert ', '').replace(ep + '(', '').rsplit(')', 1)
        if len(cleaned) == 2:
            args, expected = cleaned
            examples.append(f"    >>> {ep}({args})")
            if '==' in expected:
                examples.append(f"    {expected.split('==', 1)[1].strip()}")
    doc = f'    """\n    {text}\n'
    if examples:
        doc += '    Examples:\n' + '\n'.join(examples) + '\n'
    doc += '    """\n'
    prompt = signature + '\n' + doc
    tl = ['def check(candidate):']
    for t in tests:
        tl.append("    " + t.strip().replace(ep + '(', 'candidate('))
    return Example(id=f"mbpp_{idx}", question=prompt, test='\n'.join(tl), entry_point=ep)


def _load_code():
    """Train and dev come from MBPP-train; eval is HumanEval."""
    ds = load_dataset("google-research-datasets/mbpp", "full", split="train")
    pool = []
    for i, item in enumerate(ds):
        ex = _mbpp_to_example(item, i)
        if ex is not None:
            pool.append(ex)
        if len(pool) >= config.TRAIN_SIZE * 2 + config.DEV_SIZE:
            break
    random.shuffle(pool)
    ev = _load_humaneval_eval()[:min(TEST_SIZE["humaneval"], config.EVAL_SIZE)]
    tr, dev = _train_dev(ev, pool)
    return tr, dev, ev


# ======================================================================
# Task
# ======================================================================
class Task:
    def __init__(self, name, kind, mode, load_fn):
        self.name = name
        self.kind = kind          # "mcq" | "code"  (generation-length profile)
        self.mode = mode          # "abcd" | "yesno" | "code"
        self._load = load_fn
        self.answer_format = {"abcd": AF_ABCD, "yesno": AF_YESNO, "code": ""}[mode]

    def load(self):
        config.seed_all()
        return self._load()

    def input_text(self, ex):
        return ex.question

    def score(self, output_text, ex):
        if self.mode == "code":
            code = extract_code(output_text, ex.question)
            return run_test(ex.question, code, ex.test, ex.entry_point)
        pred = parse_abcd(output_text) if self.mode == "abcd" else parse_yesno(output_text)
        return _check(pred, ex.answer)


TASKS = {
    "arc":       Task("arc",       "mcq",  "abcd",  _load_arc),
    "navigate":  Task("navigate",  "mcq",  "yesno", _load_navigate),
    "algebra":   Task("algebra",   "mcq",  "abcd",  _mmlu_loader("abstract_algebra", TEST_SIZE["algebra"])),
    "physics":   Task("physics",   "mcq",  "abcd",  _mmlu_loader("college_physics", TEST_SIZE["physics"])),
    "medicine":  Task("medicine",  "mcq",  "abcd",  _mmlu_loader("professional_medicine", TEST_SIZE["medicine"])),
    "humaneval": Task("humaneval", "code", "code",  _load_code),
}

DATASET_ORDER = ["arc", "navigate", "algebra", "physics", "medicine", "humaneval"]
