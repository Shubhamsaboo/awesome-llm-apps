#!/usr/bin/env python3
"""notary: every number in an agent's report must come with a receipt that checks out.

  notary.py check [--message FILE] [--dir PROJECT]   verify .notary/turn.json (and coverage of FILE)
  notary.py hook-log                                  PostToolUse hook: log real tool output
  notary.py hook-stop                                 Stop hook: block a reply with unreceipted numbers

Receipt kinds (in .notary/turn.json, {"receipts": [...]}):
  file  {path, quote}       quote must be in the file now, and contain the number
  cmd   {command, quote}    quote must be in a logged real tool output (.notary/log.jsonl), and the files
                            that command read must not have changed since (receipts expire)
  calc  {expr}              arithmetic over other receipt ids, e.g. "(r2 - r1) * 100"
  user  {quote}             the user said it; checked against the transcript when available
  na    {why}               value "N/A": not measured. Never write 0 for this.
Standard library only. Hooks fail open: an exception never blocks the user.
"""
import ast, json, math, os, re, sys, time

DIRNAME = ".notary"
LOG_CAP = 20 * 1024 * 1024
FOOTER = re.compile(r"^\s*(🧾|receipts?:)", re.I | re.M)

# ---------- numbers ----------

STRIP = [
    re.compile(r"```.*?```", re.S),                 # code blocks
    re.compile(r"`[^`\n]*`"),                        # inline code
    re.compile(r"\]\([^)]*\)"),                      # markdown link targets
    re.compile(r"https?://\S+"),                     # urls
    re.compile(r"\b[\w./\\-]+\.\w+:\d+(?:-\d+)?\b"),  # file.py:42
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?\b"),  # dates
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),     # times
    re.compile(r"\bv?\d+\.\d+\.\d+[\w.-]*\b"),       # versions x.y.z
    re.compile(r"\bv\d+(?:\.\d+)?\b", re.I),         # v2, v0.1
    re.compile(r"^\s*(?:#+\s*)?\d+[.)]\s", re.M),    # list markers, numbered headings
    re.compile(r"(?:\b(?:step|phase|option|section|rule|round|part|figure|fig\.|table|line|lines|issue|pr)\s*|#)\d+\b", re.I),
]
NUM = re.compile(r"(?<![\w.])([-+−]?)(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?:[eE]([-+]?\d+))?(\s?%)?(?:\s*/\s*(\d+)(?![\d.]))?(?![\w])")


def numbers(text, strong_only=False):
    """Claim-like numbers in prose: [(raw, value, is_pct, decimals)]."""
    text = FOOTER.sub("", "\n".join(l for l in text.splitlines() if not FOOTER.match(l)))
    for rx in STRIP:
        text = rx.sub(" ", text)
    out = []
    for m in NUM.finditer(text):
        sign, whole, frac, exp, pct, denom = m.groups()
        raw = m.group(0).strip()
        if denom:  # 47/50 counts as one number
            out.append((raw, None, False, 0))
            continue
        v = float(whole.replace(",", "") + (frac or "") + (f"e{exp}" if exp else ""))
        if sign in "-−" and sign:
            v = -v
        if 1900 <= v <= 2100 and not frac and not pct and not exp:
            continue  # bare years
        strong = bool(frac or exp or pct or "," in whole or abs(v) >= 100 or v == 0)
        if strong_only and not strong:
            continue
        out.append((raw, v, bool(pct), (len(frac) - 1 if frac else 0) - (int(exp) if exp else 0)))
    return out


def parse_value(s):
    """'84.7%' -> (84.7, True, 1); '47/50' -> (0.94, False, None); 'N/A' -> None."""
    s = str(s).strip().replace("−", "-")
    if s.upper() in ("N/A", "NA", "UNKNOWN"):
        return None
    m = re.fullmatch(r"([-+]?[\d,]+)\s*/\s*(\d+)", s)
    if m:
        return (int(m.group(1).replace(",", "")) / int(m.group(2)), False, None)
    m = re.fullmatch(r"([-+]?[\d,]*\.?\d+)(?:[eE]([-+]?\d+))?\s*(%)?", s)
    if not m:
        raise ValueError(f"not a number: {s!r}")
    num, exp = m.group(1).replace(",", ""), int(m.group(2) or 0)
    return (float(num) * 10 ** exp, bool(m.group(3)), (len(num.split(".")[1]) if "." in num else 0) - exp)


def consistent(value, source, pct=False, decimals=0):
    """Is the reported value an honest rounding of source (or of source as a percentage)?"""
    tol = 0.5 * 10 ** -decimals + 1e-9
    cands = [source, source * 100] if abs(source) <= 1 else [source]
    return any(abs(c - value) <= tol for c in cands)


def same(raw, value_str):
    a, b = [str(x).replace(",", "").replace(" ", "").replace("−", "-") for x in (raw, value_str)]
    return a.lstrip("+") == b.lstrip("+")

# ---------- verification ----------


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def logged_outputs(d):
    """[{output, ts, command}] for every logged tool call, oldest first."""
    out = []
    for name in ("log.1.jsonl", "log.jsonl"):
        p = os.path.join(d, DIRNAME, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    inp = row.get("input")
                    cmd = inp.get("command", "") if isinstance(inp, dict) else ""
                    out.append({"output": norm(row.get("output", "")), "ts": row.get("ts", 0), "command": cmd or ""})
    return out


def changed_since(d, command, ts):
    """Files the command names (as arguments) that were modified after its output was logged."""
    changed = []
    for tok in re.findall(r"""[^\s'"|;&<>]+""", command):
        p = tok if os.path.isabs(tok) else os.path.join(d, tok)
        if not os.path.exists(p) or os.path.abspath(p) == os.path.abspath(d):
            continue
        files = [p] if os.path.isfile(p) else [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs][:500]
        if any(os.path.getmtime(f) > ts for f in files if DIRNAME not in f):
            changed.append(tok)
    return changed


def user_text(transcript):
    if not transcript or not os.path.exists(transcript):
        return None
    chunks = []
    with open(transcript, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "user":
                c = (e.get("message") or {}).get("content")
                chunks.append(c if isinstance(c, str) else " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict)))
    return norm(" ".join(chunks))


def quote_supports(quote, value, raw):
    v, pct, dec = value
    if dec is None:  # fraction: numerator and denominator must both appear
        a, b = [x.strip().replace(",", "") for x in str(raw).split("/")]
        toks = re.findall(r"\d+", quote.replace(",", ""))
        return a.lstrip("+-") in toks and b in toks
    return any(n[1] is not None and consistent(v, n[1], pct, dec) for n in numbers(quote))


def safe_eval(expr, env):
    node = ast.parse(expr, mode="eval")
    ok = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
          ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd)
    for n in ast.walk(node):
        if not isinstance(n, ok):
            raise ValueError(f"not allowed in calc: {type(n).__name__}")
    return eval(compile(node, "<calc>", "eval"), {"__builtins__": {}}, env)


def verify(receipts, d, transcript=None):
    """Returns {id: (ok, reason)}."""
    res, logs, utext = {}, None, None
    byid = {r.get("id"): r for r in receipts}
    for r in receipts:
        rid, kind = r.get("id", "?"), r.get("kind")
        try:
            val = parse_value(r.get("value", ""))
            if kind == "na":
                res[rid] = (val is None and bool(r.get("why")), "" if val is None else "na receipt must have value N/A")
                if val is None and not r.get("why"):
                    res[rid] = (False, "na receipt needs a why")
                continue
            if val is None:
                res[rid] = (False, "value N/A needs kind na")
                continue
            if kind == "file":
                p = os.path.join(d, r["path"])
                if not os.path.exists(p):
                    res[rid] = (False, f"file not found: {r['path']}")
                    continue
                body = norm(open(p, encoding="utf-8", errors="replace").read())
                if norm(r["quote"]) not in body:
                    res[rid] = (False, f"quote not in {r['path']} (changed, or never there)")
                elif not quote_supports(r["quote"], val, r["value"]):
                    res[rid] = (False, f"{r['value']} is not a rounding of any number in the quote")
                else:
                    res[rid] = (True, "")
            elif kind == "cmd":
                logs = logs if logs is not None else logged_outputs(d)
                hits = [row for row in logs if norm(r["quote"]) in row["output"]]
                stale = changed_since(d, hits[-1]["command"], hits[-1]["ts"]) if hits else []
                if not hits:
                    res[rid] = (False, "quote not found in any logged tool output")
                elif not quote_supports(r["quote"], val, r["value"]):
                    res[rid] = (False, f"{r['value']} is not a rounding of any number in the quote")
                elif stale:
                    res[rid] = (False, f"expired: {', '.join(stale)} changed after this output was produced; re-run it")
                else:
                    res[rid] = (True, "")
            elif kind == "calc":
                env = {}
                for name in re.findall(r"[A-Za-z_]\w*", r["expr"]):
                    ref = byid.get(name)
                    if not ref:
                        raise ValueError(f"unknown receipt {name}")
                    pv = parse_value(ref.get("value"))
                    if pv is None:
                        raise ValueError(f"{name} is N/A; a calc on an unmeasured value is N/A too")
                    env[name] = pv[0]
                got = safe_eval(r["expr"], env)
                dec = val[2] if val[2] is not None else 6
                ok = abs(got - val[0]) <= 0.5 * 10 ** -dec + 1e-9
                res[rid] = (ok, "" if ok else f"{r['expr']} = {got:.6g}, not {r['value']}")
            elif kind == "user":
                utext = utext if utext is not None else user_text(transcript)
                if utext is None:
                    res[rid] = (True, "unchecked: no transcript")
                else:
                    ok = norm(r["quote"]) in utext
                    res[rid] = (ok, "" if ok else "quote not in any user message")
            else:
                res[rid] = (False, f"unknown kind {kind!r}")
        except (KeyError, ValueError, ZeroDivisionError, SyntaxError) as e:
            res[rid] = (False, f"{type(e).__name__}: {e}")
    # a receipt that relies on a failed receipt fails too
    for r in receipts:
        if r.get("kind") == "calc" and res.get(r.get("id"), (False,))[0]:
            for name in re.findall(r"[A-Za-z_]\w*", r["expr"]):
                if not res.get(name, (True,))[0]:
                    res[r["id"]] = (False, f"depends on failed {name}")
    return res


def coverage(message, receipts, strong_only=False):
    """Numbers in the message with no receipt carrying that exact value."""
    vals = [str(r.get("value", "")) for r in receipts]
    return [raw for raw, *_ in numbers(message, strong_only) if not any(same(raw, v) for v in vals)]


def load(d):
    p = os.path.join(d, DIRNAME, "turn.json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f).get("receipts", [])


def report(message, d, transcript=None, strong_only=False):
    rs = load(d)
    res = verify(rs, d, transcript)
    bad = {k: v[1] for k, v in res.items() if not v[0]}
    uncovered = coverage(message, rs, strong_only) if message else []
    return rs, res, bad, uncovered


def explain(bad, uncovered, rs):
    lines = []
    if uncovered:
        zeros = [u for u in uncovered if re.fullmatch(r"[-+]?0+(\.0+)?%?", u)]
        lines.append("Numbers with no receipt: " + ", ".join(dict.fromkeys(uncovered)))
        if zeros:
            lines.append("A bare 0 is a measurement. If it was not measured, write N/A and add an `na` receipt.")
    byid = {r.get("id"): r for r in rs}
    for rid, why in bad.items():
        lines.append(f"Receipt {rid} ({byid.get(rid, {}).get('value', '?')}): {why}")
    return "\n".join(lines)

# ---------- entry points ----------


def project_dir(inp=None):
    return (inp or {}).get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def hook_log():
    inp = json.load(sys.stdin)
    resp = inp.get("tool_response")
    if isinstance(resp, dict) and ("stdout" in resp or "stderr" in resp):
        text = (resp.get("stdout") or "") + "\n" + (resp.get("stderr") or "")
    else:
        text = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
    append_log(project_dir(inp), inp.get("tool_name"), inp.get("tool_input"), text, inp.get("tool_use_id"))


def append_log(project, tool, tool_input, text, tool_use_id=None):
    d = os.path.join(project, DIRNAME)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "log.jsonl")
    if os.path.exists(p) and os.path.getsize(p) > LOG_CAP:
        os.replace(p, os.path.join(d, "log.1.jsonl"))
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "id": tool_use_id, "tool": tool,
                            "input": tool_input, "output": text[:200_000]}, ensure_ascii=False) + "\n")


def cli_run(argv):
    """notary.py run -- <command>: run it, show its output, log it. For installs without the hooks."""
    import subprocess
    argv = argv[1:] if argv[:1] == ["--"] else argv
    if not argv:
        print("usage: notary.py run -- <command>", file=sys.stderr)
        return 2
    cmd = argv[0] if len(argv) == 1 else subprocess.list2cmdline(argv) if os.name == "nt" else __import__("shlex").join(argv)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    append_log(os.getcwd(), "notary-run", {"command": cmd}, p.stdout + "\n" + p.stderr)
    return p.returncode


def last_reply(transcript):
    """Older Claude Code versions send no last_assistant_message: take the last assistant text."""
    text = ""
    if transcript and os.path.exists(transcript):
        with open(transcript, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") == "assistant":
                    c = (e.get("message") or {}).get("content") or []
                    t = c if isinstance(c, str) else "".join(x.get("text", "") for x in c if isinstance(x, dict))
                    if t.strip():
                        text = t
    return text


def hook_stop():
    inp = json.load(sys.stdin)
    d = project_dir(inp)
    if os.environ.get("NOTARY", "").lower() == "off" or os.path.exists(os.path.join(d, DIRNAME, "off")):
        return
    if inp.get("stop_hook_active"):
        return  # one push per turn; never loop
    msg = inp.get("last_assistant_message") or last_reply(inp.get("transcript_path"))
    if not numbers(msg, strong_only=True):
        return
    rs, res, bad, uncovered = report(msg, d, inp.get("transcript_path"), strong_only=True)
    if bad or uncovered:
        print(json.dumps({"decision": "block", "reason":
              "notary: this reply states numbers that are not backed by a checked receipt.\n"
              + explain(bad, uncovered, rs)
              + "\nFix: add receipts to .notary/turn.json (see the notary skill), replace unmeasured values "
                "with N/A, or drop the number. Then restate the reply."}))


def cli_check(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="notary.py check")
    ap.add_argument("--message")
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--transcript")
    a = ap.parse_args(argv)
    msg = open(a.message, encoding="utf-8").read() if a.message else ""
    rs, res, bad, uncovered = report(msg, a.dir, a.transcript, strong_only=True)
    for r in rs:
        ok, why = res.get(r.get("id"), (False, "?"))
        src = r.get("path") or r.get("command") or r.get("expr") or r.get("why") or r.get("quote", "")
        print(f"{'ok ' if ok else 'BAD'} {r.get('id', '?'):>4} {str(r.get('value')):>10}  {r.get('kind', '?'):<4} {str(src)[:60]}"
              + (f"  <- {why}" if why else ""))
    if uncovered:
        print("no receipt: " + ", ".join(dict.fromkeys(uncovered)))
    n = len(rs)
    print(f"🧾 {n - len(bad)}/{n} receipts check out" + (f"; {len(uncovered)} numbers uncovered" if msg else ""))
    return 1 if bad or uncovered else 0


def main():
    cmd, rest = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("check", [])
    if cmd in ("hook-log", "hook-stop"):
        try:
            (hook_log if cmd == "hook-log" else hook_stop)()
        except Exception as e:  # fail open
            print(f"notary hook error: {e}", file=sys.stderr)
        return 0
    if cmd == "run":
        return cli_run(rest)
    return cli_check(rest)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
