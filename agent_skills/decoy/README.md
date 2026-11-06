# 🪤 decoy

**Fake data that can't be mistaken for real, and can be made again.** When your agent generates fake, mock, seed or synthetic data, decoy requires three things:

- every sensitive value comes from a published reserved range;
- the data comes from a seeded generator script;
- a data card states the rules, the standards, what counts as the target, and how the data differs from real data.

`scripts/decoy.py` lints all three.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/decoy
```

## What it caught

Request: "I need 200 fake customer records to test our CRM import." Claude Code 2.1.310, Opus 5.5, 3 runs per arm, deterministic scoring.

| Condition | card numbers that could belong to someone | complete data card |
|---|---|---|
| no skill | **600/600** | 0/3 |
| the rules in one sentence | 0/600 | 0/3 (no target definition) |
| decoy | **0/600** | 3/3 |

Every arm already used example.com emails, 555-01xx phones, 9xx SSNs and documentation IPs. The failure was cards. Without the skill, the agent took a real test-card *prefix*, added random digits and fixed the Luhn checksum, then called the result "test prefixes". Such numbers are plausible real cards.

## Safe ranges (each from a published rule)

| field | safe values | rule |
|---|---|---|
| email | `example.com/.net/.org`, `*.example`, `*.test`, `*.invalid` | RFC 2606, RFC 6761 |
| phone | 555-0100 to 555-0199 (US); Ofcom drama ranges (UK) | NANPA; Ofcom |
| card | 24 processor test numbers, each checked against Stripe, Braintree or Adyen docs | Luhn-valid numbers outside the list are flagged |
| SSN | area 900-999, 000 or 666; group 00; serial 0000 | never issued by the SSA |
| IP | 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32 | RFC 5737, RFC 3849 |

```bash
python3 scripts/decoy.py lint data/customers.csv     # flags possibly-real values (cards and SSNs masked in output)
python3 scripts/decoy.py card data/customers.csv     # checks the data card
python3 scripts/decoy.py safe                         # prints the ranges for a generator
```

It cannot vet names: no rule reserves names, so the card must say how they were invented.

## Privacy

Local only, no network, never echoes a possibly-real card or SSN in full.
