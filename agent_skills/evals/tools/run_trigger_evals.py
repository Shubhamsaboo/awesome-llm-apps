#!/usr/bin/env python3
"""
Tier 2 — trigger & routing. Deterministic, CI-safe, no model.

Pattern from addyosmani/agent-skills (evals/README.md there): a skill's
description is its entire trigger surface, so check it lexically —
positive prompts must score against their skill's description clearly
above the near-miss negatives, and (once the catalog has 2+ skills) must
rank their own skill first, with no two descriptions near-colliding.

This is a lexical approximation of routing. It cannot judge semantics —
that's the behavioral tier's job — but it catches the two failure modes
that dominate real trigger bugs: a description missing the vocabulary
users actually say, and an over-broad description that outranks the
right skill. A failure here usually means *fix the description*.

Cases live in evals/<skill>/trigger-cases.json. A case marked
"lexical": false is skipped here (it triggers via reasoning, e.g.
necromancer mode, not via description vocabulary) and is covered by the
behavioral tier instead.

    python3 run_trigger_evals.py            # checks every skill in the catalog
"""

import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVALS_ROOT = os.path.abspath(os.path.join(HERE, ".."))

STOP = set("""a an the and or of to in on for with is are was were be been it its this
that those these you your i me my we our they their he she his her do does did done
can could should would will just very really some any all not no yes if then than as
at by from into out up down over under again more most other own same so too s t don
""".split())

MARGIN = 1.15  # min positive score must beat max negative score by this factor


def tokens(text):
    out = set()
    for w in re.findall(r"[a-z0-9']+", text.lower()):
        if w in STOP or len(w) < 3:
            continue
        # crude stemmer: enough to match "projects/project", "finished/finish"
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
        out.add(w)
    return out


def description_of(skill_dir):
    text = open(os.path.join(skill_dir, "SKILL.md")).read()
    m = re.search(r"^description:\s*(.+?)^(?=[a-zA-Z-]+:|---)", text, re.S | re.M)
    return m.group(1) if m else ""


def score(prompt_toks, desc_toks):
    if not prompt_toks:
        return 0.0
    return len(prompt_toks & desc_toks) / math.sqrt(len(prompt_toks))


def main():
    skills = {}  # name -> description tokens
    for entry in sorted(os.listdir(SKILLS_ROOT)):
        if os.path.exists(os.path.join(SKILLS_ROOT, entry, "SKILL.md")):
            skills[entry] = tokens(description_of(os.path.join(SKILLS_ROOT, entry)))
    if not skills:
        print("no skills found under %s" % SKILLS_ROOT)
        return 1

    failures = 0

    # routing sanity across the catalog: no two descriptions near-collide
    names = sorted(skills)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = skills[names[i]], skills[names[j]]
            overlap = len(a & b) / max(1, min(len(a), len(b)))
            if overlap > 0.5:
                print("FAIL  descriptions near-collide: %s vs %s (%.0f%% shared vocabulary)"
                      % (names[i], names[j], overlap * 100))
                failures += 1

    for name in names:
        case_file = os.path.join(EVALS_ROOT, name, "trigger-cases.json")
        if not os.path.exists(case_file):
            print("WARN  %s has no trigger-cases.json — add one" % name)
            continue
        cases = json.load(open(case_file))["cases"]
        pos, neg = [], []
        for c in cases:
            if c.get("lexical") is False:
                continue
            s = score(tokens(c["prompt"]), skills[name])
            (pos if c["should_trigger"] else neg).append((s, c["id"]))
            # routing: with 2+ skills, a positive must rank its own skill first
            if c["should_trigger"] and len(skills) > 1:
                best = max(skills, key=lambda k: score(tokens(c["prompt"]), skills[k]))
                if best != name:
                    print("FAIL  %s: %r routes to %s instead" % (name, c["id"], best))
                    failures += 1
        if pos and neg:
            worst_pos, wp_id = min(pos)
            best_neg, bn_id = max(neg)
            if worst_pos <= best_neg * MARGIN:
                print("FAIL  %s: weakest positive %r (%.2f) does not clear strongest "
                      "near-miss %r (%.2f) — the description is missing vocabulary "
                      "users say, or a negative shares too much of it"
                      % (name, wp_id, worst_pos, bn_id, best_neg))
                failures += 1
            else:
                print("PASS  %s: %d positives clear %d near-misses "
                      "(weakest %.2f vs strongest %.2f)"
                      % (name, len(pos), len(neg), worst_pos, best_neg))

    if failures:
        print("\n%d failure(s)" % failures)
        return 1
    print("\ntrigger & routing: all clear (%d skill%s)" % (len(skills), "" if len(skills) == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
