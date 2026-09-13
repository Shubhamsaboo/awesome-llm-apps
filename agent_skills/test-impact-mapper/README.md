# 🎯 Test Impact Mapper

Reads a working, staged, saved, or branch git diff and returns a ranked
shortlist of likely tests to run. Each recommendation cites evidence:
conventional test-path pairing, reverse imports, mentioned symbols, or git
co-change history. Local and offline; the script never touches the working
tree.

![Test Impact Mapper demo](https://github.com/mvanhorn/awesome-llm-apps/releases/download/demo-assets/test-impact-mapper.gif)

The demo changes `billing/invoice.py` in a sample repo. The mapper lists
`tests/test_invoice.py` (conventional pair plus import) and skips an unrelated
docs file.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/test-impact-mapper
```

## Run

Ask the agent:

> Which tests should I run after this change?

Or run the deterministic core directly:

```bash
python3 scripts/impact_map.py --repo /path/to/repo --json
```

Use `--staged` for the index, `--base main` for a branch diff, or `--diff -`
for unified diff input on stdin. The script uses only the Python standard
library, makes no network calls, and does not modify the repository.
