#!/usr/bin/env python3
"""Deterministic tests for decoy.py. No model, no network.

Every "unsafe" value below is constructed to *look* real under the rule it breaks (a
gmail.com address, a 212-xxx phone, a Luhn-valid non-test card, an SSN in an issued
area, a public IP); none was copied from a real record. Every "safe" value comes from the
published reserved range named in decoy.py. Run: python3 agent_skills/evals/decoy/test_decoy.py
"""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "decoy", "scripts", "decoy.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import decoy as D  # noqa: E402

_made = []
_mkdtemp = tempfile.mkdtemp
tempfile.mkdtemp = lambda *a, **k: _made.append(_mkdtemp(*a, **k)) or _made[-1]
__import__("atexit").register(lambda: [__import__("shutil").rmtree(d, ignore_errors=True) for d in _made])  # leave no test dirs behind

CASES = []
case = lambda f: CASES.append(f) or f
kinds = lambda text: sorted(k for k, *_ in D.scan(text))


@case
def safe_values_pass():
    text = "\n".join([
        "id,name,email,phone,ssn,card,ip",
        "1,Ana Reyes,ana.reyes@example.com,(212) 555-0142,912-34-5678,4242 4242 4242 4242,192.0.2.17",
        "2,Bo Lin,bo@shop.test,+1 415-555-0199,000-12-3456,5555555555554444,2001:db8::42",
        "3,Cy Ola,cy@corp.example,555-0100,123-00-4567,378282246310005,10.0.0.8",
        "4,Di Park,di@mail.example.org,07700 900123,666-01-2345,4111-1111-1111-1111,198.51.100.4",
    ])
    assert D.scan(text) == [], D.scan(text)


@case
def real_looking_values_flagged():
    assert kinds("contact: john.smith@gmail.com") == ["email"]
    assert kinds("call (212) 867-5309 today") == ["phone"]
    assert kinds("ssn 123-45-6789") == ["ssn"]
    assert kinds("card 4539 1488 0343 6467") == ["card"]          # Luhn-valid, not a test number
    assert kinds("from 8.8.4.4") == ["ip"]
    assert kinds("v6 2a00:1450:4001:82a::200e") == ["ip"]
    assert kinds("mobile 07911 123456") == ["phone"]


@case
def non_luhn_long_numbers_are_not_cards():
    assert kinds("order 4539148803436468") == []                   # fails Luhn: an order id, not a card


@case
def versions_and_dates_are_not_ips_or_phones():
    assert kinds("python 3.11.4, released 2026-10-27, build 1.2.3.4567") == []


@case
def card_check_requires_fields_and_seed():
    d = tempfile.mkdtemp()
    data = os.path.join(d, "customers.csv")
    open(data, "w").write("id,email\n1,a@example.com\n")
    c, problems = D.check_card(data)
    assert c is None and problems
    open(data + ".decoy.md", "w").write(
        "Generator: gen.py (stdlib random), seed = 20261027. Rules per field: email uses example.com (RFC 2606). "
        "Target: emails count as PII. Differs from real data: only ASCII names.")
    c, problems = D.check_card(data)
    assert c and problems == [], problems
    open(data + ".decoy.md", "w").write("Generator: faker. Seed: random. Fields: names and emails.")
    c, problems = D.check_card(data)
    assert any("seed value" in p for p in problems) and any("standard" in p for p in problems), problems


@case
def cli_exit_codes():
    d = tempfile.mkdtemp()
    good, bad = os.path.join(d, "good.csv"), os.path.join(d, "bad.csv")
    open(good, "w").write("a@example.com,555-0123\n")
    open(bad, "w").write("a@gmail.com,212-867-5309\n")
    run = lambda *a: subprocess.run([sys.executable, SCRIPT, *a], capture_output=True, text=True)
    assert run("lint", good).returncode == 0
    r = run("lint", bad)
    assert r.returncode == 1 and "1 email" in r.stdout and "1 phone" in r.stdout, r.stdout


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
