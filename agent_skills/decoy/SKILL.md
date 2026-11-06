---
name: decoy
description: >
  Makes synthetic, fake, mock, seed or test data safe and reproducible. Every
  generated value that looks like personal data comes from a published reserved
  range (RFC 2606 email domains, NANP 555-0100 to 0199 phones, processor test
  card numbers, SSNs the SSA never issues, RFC 5737 IPs), the generator is a
  seeded script, and a data card states the generation rules, the standards,
  what counts as the target, and how the data differs from real data. A linter
  checks the output. Use when generating fake users or customers, test fixtures,
  seed data, demo datasets, synthetic benchmarks or planted test cases, and when
  the user says "fake data", "mock data", "dummy data", "synthetic dataset",
  "test fixtures", "seed the database", "造数据", "合成数据", "测试数据", "自造数据".
license: MIT
metadata:
  author: ruijiezh67
  version: "0.1.0"
  source: https://github.com/Shubhamsaboo/awesome-llm-apps
---

# Decoy

Fake data must never be mistaken for real, and must be possible to make again.
A plausible gmail address, a working phone number or a Luhn-valid card in a
fixture will eventually leak into a screenshot, an email or a production
database. A dataset nobody can regenerate is not evidence.

## Rules (always)

1. **Reserved values only.** Use `python <skill-dir>/scripts/decoy.py safe` for
   the ranges. Do not use realistic-looking values, real company domains or
   famous people's names.
   - Email domains: example.com, example.net, example.org, `*.example`, `*.test`.
   - Phones: 555-0100 to 555-0199 (NANP), or Ofcom drama ranges for the UK.
   - Cards: only the listed processor test numbers, copied whole. A test
     *prefix* plus random Luhn-valid digits (`411111…`, `424242…`) is a
     plausible real card number, not a test card.
   - SSN: area 900-999, 000 or 666.
   - IPs: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 and 2001:db8::/32.
2. **A seeded script, not hand-typed rows.** Write the generator as a file
   (`gen_<name>.py` or similar). Seed it explicitly, and print the seed in the card.
   Running it twice gives byte-identical output.
3. **A data card beside the data**: `<file>.decoy.md`, or `DECOY.md` for a
   folder. It must state:
   - **Generator**: the script, the library and its version, and `seed = <number>`.
   - **Rules per field**: how each field is produced and from what distribution or
     range, plus the size of the dataset.
   - **Standard**: which published rule each sensitive field follows, or why none applies.
   - **Target**: for test cases or benchmarks, what counts as the thing to be found
     (e.g. what counts as PII and what does not). It must match how real data
     would be labelled.
   - **Differences from real data**: for example, only US-style names, perfectly
     clean formatting, no typos, uniform distributions.
4. **Lint before handing over.** Run `decoy.py lint <files>` and
   `decoy.py card <files>`. Fix every `BAD` line. Then say in your reply that both
   pass, and give the regenerate command.

## When the user wants realism

Realistic *structure* is fine: plausible name mixes, address formats and value
distributions. Realistic *identifiers* are not. If a test truly needs values
outside the reserved ranges, for example a validator that must accept real
domains, say so in the card. Generate as few as the test needs, and mark them
in the data itself (`# NON-RESERVED: needed for X`).

## Card template

```markdown
# customers.csv: data card
- Generator: gen_customers.py (Python 3.12 stdlib `random`), seed = 20261027, 200 rows
- Fields:
  - name: first and last name drawn uniformly from 40 + 40 invented names (list in script)
  - email: `<first>.<last><n>@example.com`. Standard: RFC 2606
  - phone: `+1-<area>-555-01<00-99>`, area from 10 fixed codes. Standard: NANP fiction range
  - card: cycled from the processor test list. Standard: Stripe/Braintree/Adyen test numbers
  - signup: uniform over 2025-01-01..2026-09-30
- Target: name, email, phone, card count as PII; signup date does not
- Differs from real data: names are invented and ASCII-only, no duplicates, no missing values, formats perfectly consistent
- Regenerate: `python gen_customers.py --seed 20261027 > customers.csv`
```
