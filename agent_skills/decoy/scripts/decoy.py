#!/usr/bin/env python3
"""decoy: synthetic data that cannot be mistaken for real, and can be regenerated.

  decoy.py lint FILE...     flag values that could belong to a real person or system
  decoy.py card FILE...     check each data file has a data card (FILE.decoy.md or DECOY.md beside it)
  decoy.py safe             print the safe ranges, for pasting into a generator

Safe ranges, each from a published rule:
  email   reserved domains: example.com/.net/.org, *.example, *.test, *.invalid, *.localhost (RFC 2606, RFC 6761)
  phone   NANP 555-0100..555-0199, reserved for fiction (NANPA); UK Ofcom drama ranges 07700 900000-900999,
          020 7946 0000-0999, 0113 496 0000-0999, 0161 496 0000-0999
  card    Luhn-valid numbers must be documented processor test numbers (Stripe, Braintree, Adyen test lists)
  ssn     never issued by the SSA: area 000, 666 or 900-999; group 00; serial 0000
  ip      documentation ranges 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 (RFC 5737), 2001:db8::/32
          (RFC 3849); private/loopback/link-local are allowed (not routable to a real host)
Standard library only.
"""
import ipaddress, json, os, re, sys
from collections import defaultdict

RESERVED_TLDS = ("example", "test", "invalid", "localhost")
RESERVED_DOMAINS = ("example.com", "example.net", "example.org")
# Each number checked on 2026-10-27 against docs.stripe.com/testing, Braintree "Testing" reference or
# Adyen "Test card numbers"; numbers not found in any of them were removed.
TEST_CARDS = {
    "4242424242424242", "4000056655665556", "4111111111111111", "4012888888881881", "4000000000000002",
    "4000000000009995", "4000000000000077", "4000002500003155", "4000002760003184",
    "5555555555554444", "5200828282828210", "5105105105105100", "2223003122003222", "5454545454545454",
    "378282246310005", "371449635398431", "378734493671000", "6011111111111117", "6011000990139424",
    "3056930009020004", "36227206271667", "3566002020360505", "6200000000000005", "4917610000000000",
}
UK_FICTION = [(r"07700\s?900\d{3}", True), (r"020\s?7946\s?0\d{3}", True), (r"0113\s?496\s?0\d{3}", True),
              (r"0161\s?496\s?0\d{3}", True)]

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)\b")
PHONE = re.compile(r"(?<![\d.])(?:\+?1[-. ]?)?\(?([2-9]\d{2})\)?[-. ]?(\d{3})[-. ]?(\d{4})(?![\d.])")
CARD = re.compile(r"(?<![\d.-])(?:\d[ -]?){12,18}\d(?![\d.])")
SSN = re.compile(r"(?<![\d-])(\d{3})-(\d{2})-(\d{4})(?![\d-])")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
IPV6 = re.compile(r"(?<![\w:.])[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4}){2,7}(?![\w:])")  # candidates; ipaddress decides
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24", "2001:db8::/32")]


def luhn(digits):
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def email_ok(domain):
    d = domain.lower().rstrip(".")
    return d in RESERVED_DOMAINS or any(d.endswith("." + x) for x in RESERVED_DOMAINS) or d.split(".")[-1] in RESERVED_TLDS


def ssn_ok(area, group, serial):
    return area in ("000", "666") or area.startswith("9") or group == "00" or serial == "0000"


def ip_ok(text):
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return None  # not an address (e.g. a version string)
    if any(ip in n for n in DOC_NETS if n.version == ip.version):
        return True
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_reserved or ip.is_multicast


def scan(text):
    """[(kind, value, why)] for every value that could be real."""
    found = []
    taken = []  # spans already classified, so a card is not also read as a phone
    for m in EMAIL.finditer(text):
        if not email_ok(m.group(1)):
            found.append(("email", m.group(0), f"{m.group(1)} is not a reserved domain (RFC 2606/6761)"))
    for m in CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn(digits):
            taken.append(m.span())
            if digits not in TEST_CARDS:
                found.append(("card", m.group(0), "Luhn-valid and not a documented processor test number"))
    for m in SSN.finditer(text):
        taken.append(m.span())
        if not ssn_ok(*m.groups()):
            found.append(("ssn", m.group(0), "inside ranges the SSA issues (use area 9xx, 000 or 666)"))
    for m in PHONE.finditer(text):
        if any(a <= m.start() < b for a, b in taken):
            continue
        area, exch, line = m.groups()
        if not (exch == "555" and 100 <= int(line) <= 199):
            found.append(("phone", m.group(0).strip(), "outside NANP fiction range 555-0100..0199"))
    for m in IPV4.finditer(text):
        ok = ip_ok(m.group(0))
        if ok is False:
            found.append(("ip", m.group(0), "public address outside RFC 5737 documentation ranges"))
    for m in IPV6.finditer(text):
        ok = ip_ok(m.group(0))
        if ok is False:
            found.append(("ip", m.group(0), "public address outside 2001:db8::/32 (RFC 3849)"))
    uk = re.compile(r"(?<!\d)(?:07\d{3}\s?\d{6}|0\d{2,3}\s?\d{3,4}\s?\d{4})(?!\d)")
    for m in uk.finditer(text):
        if m.group(0).startswith(("07", "020", "0113", "0161")) and not any(re.fullmatch(p, m.group(0)) for p, _ in UK_FICTION):
            if not any(a <= m.start() < b for a, b in taken):
                found.append(("phone", m.group(0), "UK number outside Ofcom drama ranges"))
    return found


CARD_FIELDS = {
    "generator": r"generat|script|tool|faker|library",
    "seed": r"\bseed\b",
    "rules": r"rule|distribution|range|per field|fields?\b",
    "standard": r"RFC|NANP|Luhn|SSA|Ofcom|standard",
    "target": r"target|label|counts as|ground truth|what is|PII",
    "difference": r"differ|unlike real|limitation|not like real|real data",
}


def card_for(path):
    d, base = os.path.dirname(os.path.abspath(path)), os.path.basename(path)
    for c in (os.path.join(d, base + ".decoy.md"), os.path.join(d, "DECOY.md")):
        if os.path.exists(c):
            return c
    return None


def check_card(path):
    c = card_for(path)
    if not c:
        return None, ["no data card (FILE.decoy.md or DECOY.md beside it)"]
    return c, card_problems(open(c, encoding="utf-8", errors="replace").read())


def card_problems(text):
    missing = [k for k, rx in CARD_FIELDS.items() if not re.search(rx, text, re.I)]
    if re.search(r"\bseed\b", text, re.I) and not re.search(r"\bseed\b\W{0,5}[=:]?\s*`?\d+", text, re.I):
        missing.append("seed value")
    return [f"card does not state: {m}" for m in missing]


def mask(kind, val):
    """Never echo a possibly-real card or SSN in full: keep the first 6 / last 4 digits of a card, last 4 of an SSN."""
    if kind == "card":
        d = re.sub(r"\D", "", val)
        return d[:6] + "•" * (len(d) - 10) + d[-4:]
    if kind == "ssn":
        return "•••-••-" + val[-4:]
    return val


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    cmd, files = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("help", [])
    if cmd == "safe":
        print(__doc__.split("Safe ranges, each from a published rule:")[1].split("Standard library")[0].rstrip())
        print("  test cards: " + ", ".join(sorted(TEST_CARDS)))
        return 0
    if cmd not in ("lint", "card") or not files:
        print(__doc__)
        return 2
    bad = 0
    for f in files:
        if cmd == "card":
            c, problems = check_card(f)
            print(f"{'ok ' if not problems else 'BAD'} {f}" + (f"  card: {c}" if c else ""))
            for p in problems:
                print(f"    {p}")
            bad += bool(problems)
            continue
        found = scan(open(f, encoding="utf-8", errors="replace").read())
        by = defaultdict(list)
        for kind, val, why in found:
            by[kind].append((val, why))
        if not found:
            print(f"ok  {f}: no value that could be real")
        else:
            bad += 1
            print(f"BAD {f}: " + ", ".join(f"{len(v)} {k}" for k, v in sorted(by.items())))
            for k, vals in sorted(by.items()):
                for val, why in vals[:3]:
                    print(f"    {k:<5} {mask(k, val):<24} {why}")
                if len(vals) > 3:
                    print(f"    {k:<5} … {len(vals) - 3} more")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
