#!/usr/bin/env python3
"""Deterministic tests for notary.py. No model, no network, no randomness.

Fixtures are hand-written: a metrics.json with val_acc 0.8472, a logged command
output "accuracy 0.8290 (829/1000)", and reports that state these values honestly,
rounded dishonestly (85.2% from 0.8472), from a changed file, from a fabricated
command output, or as a bare 0 for an unmeasured run. Run: python3 agent_skills/evals/notary/test_notary.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "notary", "scripts", "notary.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import notary as R  # noqa: E402

_made = []
_mkdtemp = tempfile.mkdtemp
tempfile.mkdtemp = lambda *a, **k: _made.append(_mkdtemp(*a, **k)) or _made[-1]
__import__("atexit").register(lambda: [__import__("shutil").rmtree(d, ignore_errors=True) for d in _made])  # leave no test dirs behind

CASES = []
case = lambda f: CASES.append(f) or f


def project(receipts, files=None, log=None):
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".notary"))
    for path, body in (files or {"runs/aug/metrics.json": '{\n  "val_acc": 0.8472,\n  "train_time_s": 3985\n}\n'}).items():
        os.makedirs(os.path.dirname(os.path.join(d, path)), exist_ok=True)
        open(os.path.join(d, path), "w").write(body)
    with open(os.path.join(d, ".notary", "log.jsonl"), "w") as f:
        for out in (log if log is not None else ["$ python eval_test.py\naccuracy 0.8290 (829/1000)\nmacro_f1 0.8011\n"]):
            f.write(json.dumps({"output": out}) + "\n")
    json.dump({"receipts": receipts}, open(os.path.join(d, ".notary", "turn.json"), "w"))
    return d


FILE_OK = {"id": "r1", "value": "84.7%", "kind": "file", "path": "runs/aug/metrics.json", "quote": '"val_acc": 0.8472'}
CMD_OK = {"id": "r2", "value": "0.829", "kind": "cmd", "command": "python eval_test.py", "quote": "accuracy 0.8290"}


def bad_ids(d, msg="", transcript=None):
    return R.report(msg, d, transcript, strong_only=True)[2]


@case
def extraction_skips_code_dates_versions_refs():
    msg = ("1. Ran `python train.py --lr 0.003` on 2026-10-27 with v2.1.92 at 14:05.\n"
           "See train.py:120 and step 3. Accuracy 84.7%, 1,203 rows, 47/50 tests, loss 0.31, 0 errors.\n"
           "```\nval 0.99\n```\n🧾 3/3 receipts check out")
    raws = [n[0] for n in R.numbers(msg, strong_only=True)]
    assert raws == ["84.7%", "1,203", "47/50", "0.31", "0"], raws


@case
def file_and_cmd_receipts_pass():
    assert bad_ids(project([FILE_OK, CMD_OK])) == {}


@case
def dishonest_rounding_fails():
    d = project([dict(FILE_OK, value="85.2%")])
    assert "r1" in bad_ids(d)


@case
def changed_file_fails():
    d = project([FILE_OK], files={"runs/aug/metrics.json": '{"val_acc": 0.8391}'})
    assert "quote not in" in bad_ids(d)["r1"]


@case
def fabricated_command_output_fails():
    d = project([dict(CMD_OK, quote="accuracy 0.9100")])
    assert "logged tool output" in bad_ids(d)["r2"]


@case
def cmd_receipt_expires_when_its_input_changes():
    import time
    d = project([CMD_OK], files={"runs/aug/preds.csv": "y_true,y_pred\n1,1\n"}, log=[])
    row = {"output": "accuracy 0.8290 (829/1000)", "input": {"command": "python eval_test.py runs/aug/preds.csv"}}
    with open(os.path.join(d, ".notary", "log.jsonl"), "w") as f:
        f.write(json.dumps(dict(row, ts=time.time() + 60)) + "\n")  # output logged after the file was written
    assert bad_ids(d) == {}
    with open(os.path.join(d, ".notary", "log.jsonl"), "w") as f:
        f.write(json.dumps(dict(row, ts=time.time() - 60)) + "\n")  # file rewritten after the output
    assert "expired" in bad_ids(d)["r2"] and "preds.csv" in bad_ids(d)["r2"]


@case
def scientific_notation():
    raws = [(n[0], n[1]) for n in R.numbers("lr 1.0e-4 and 3e-5 for 2.5E3 steps", strong_only=True)]
    assert raws == [("1.0e-4", 1e-4), ("3e-5", 3e-5), ("2.5E3", 2500.0)], raws
    d = project([{"id": "r7", "value": "1.0e-4", "kind": "file", "path": "cfg.yaml", "quote": "lr: 1.0e-4"}],
                files={"cfg.yaml": "lr: 1.0e-4\n"})
    assert bad_ids(d) == {}


@case
def run_wrapper_logs_output_without_hooks():
    d = project([dict(CMD_OK, quote="accuracy 0.8290")], log=[])
    open(os.path.join(d, "ev.py"), "w").write("print('accuracy 0.8290 (829/1000)')\n")
    assert "r2" in bad_ids(d)  # nothing logged yet
    p = subprocess.run([sys.executable, SCRIPT, "run", "--", sys.executable, "ev.py"], cwd=d, capture_output=True, text=True)
    assert p.returncode == 0 and "accuracy 0.8290" in p.stdout, p.stderr
    assert bad_ids(d) == {}


@case
def fraction_receipt():
    d = project([{"id": "r3", "value": "829/1000", "kind": "cmd", "quote": "(829/1000)"}])
    assert bad_ids(d) == {}
    d = project([{"id": "r3", "value": "839/1000", "kind": "cmd", "quote": "(829/1000)"}])
    assert "r3" in bad_ids(d)


@case
def calc_checks_arithmetic_and_dependencies():
    base = {"id": "r0", "value": "0.806", "kind": "cmd", "quote": "accuracy 0.8060"}
    log = ["accuracy 0.8290 (829/1000)", "accuracy 0.8060 (806/1000)"]
    good = {"id": "r4", "value": "2.3", "kind": "calc", "expr": "(r2 - r0) * 100"}
    assert bad_ids(project([CMD_OK, base, good], log=log)) == {}
    wrong = dict(good, value="3.1")
    assert "r4" in bad_ids(project([CMD_OK, base, wrong], log=log))
    na = {"id": "r0", "value": "N/A", "kind": "na", "why": "run crashed"}
    assert "r4" in bad_ids(project([CMD_OK, na, good], log=log))


@case
def na_needs_why_and_na_value():
    assert bad_ids(project([{"id": "r5", "value": "N/A", "kind": "na", "why": "OOM at epoch 7"}])) == {}
    assert "r5" in bad_ids(project([{"id": "r5", "value": "N/A", "kind": "na"}]))
    assert "r5" in bad_ids(project([{"id": "r5", "value": "0", "kind": "na", "why": "x"}]))


@case
def coverage_and_zero_message():
    d = project([FILE_OK])
    rs, res, bad, unc = R.report("aug reached 84.7% val, aug-lr test acc 0%, time 66.4 min", d, strong_only=True)
    assert unc == ["0%", "66.4"], unc
    assert "write N/A" in R.explain(bad, unc, rs)


@case
def user_receipt_checked_against_transcript():
    d = project([{"id": "r6", "value": "0.003", "kind": "user", "quote": "use lr 0.003"}])
    t = os.path.join(d, "t.jsonl")
    open(t, "w").write(json.dumps({"type": "user", "message": {"content": "please use lr 0.003 this time"}}) + "\n")
    assert bad_ids(d, transcript=t) == {}
    open(t, "w").write(json.dumps({"type": "user", "message": {"content": "use the default"}}) + "\n")
    assert "r6" in bad_ids(d, transcript=t)


def hook(cmd, payload, env=None):
    p = subprocess.run([sys.executable, SCRIPT, cmd], input=json.dumps(payload), capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, **(env or {})))
    assert p.returncode == 0, p.stderr
    return p.stdout


@case
def stop_hook_blocks_then_lets_go():
    d = project([FILE_OK])
    base = {"cwd": d, "stop_hook_active": False}
    out = hook("hook-stop", dict(base, last_assistant_message="Val accuracy 84.7%, test accuracy 91.0%."))
    assert json.loads(out)["decision"] == "block" and "91.0%" in json.loads(out)["reason"]
    assert hook("hook-stop", dict(base, last_assistant_message="Val accuracy 84.7%.")) == ""
    assert hook("hook-stop", dict(base, last_assistant_message="Done, I edited 3 files.")) == ""
    assert hook("hook-stop", dict(base, stop_hook_active=True, last_assistant_message="test 91.0%")) == ""
    assert hook("hook-stop", dict(base, last_assistant_message="test 91.0%"), env={"NOTARY": "off"}) == ""


@case
def stop_hook_reads_transcript_when_no_last_message():
    d = project([FILE_OK])
    t = os.path.join(d, "t.jsonl")
    open(t, "w").write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "test acc 91.0%"}]}}) + "\n")
    out = hook("hook-stop", {"cwd": d, "stop_hook_active": False, "transcript_path": t})
    assert json.loads(out)["decision"] == "block"


@case
def stop_hook_fails_open_on_garbage():
    p = subprocess.run([sys.executable, SCRIPT, "hook-stop"], input="not json", capture_output=True, text=True)
    assert p.returncode == 0 and p.stdout == ""


@case
def log_hook_records_bash_stdout():
    d = tempfile.mkdtemp()
    hook("hook-log", {"cwd": d, "tool_name": "Bash", "tool_use_id": "t1", "tool_input": {"command": "python e.py"},
                      "tool_response": {"stdout": "accuracy 0.8290", "stderr": "", "interrupted": False}})
    row = json.loads(open(os.path.join(d, ".notary", "log.jsonl")).read())
    assert "accuracy 0.8290" in row["output"] and row["tool"] == "Bash"


if __name__ == "__main__":
    bad = 0
    for c in CASES:
        try:
            c()
            print("ok  ", c.__name__)
        except Exception as e:
            bad += 1
            print("FAIL", c.__name__, type(e).__name__, e)
    print(f"{len(CASES) - bad}/{len(CASES)} passed")
    sys.exit(1 if bad else 0)
