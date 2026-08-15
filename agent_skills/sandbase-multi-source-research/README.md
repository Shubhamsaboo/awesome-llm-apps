# SandBase Multi-Source Research Agent Skill

Research a question across several web and academic search providers, detect
circular reporting, and produce an evidence-linked report with conservative
confidence labels.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/sandbase-multi-source-research
```

Configure SandBase MCP and its API key through your agent's normal secret
store. SandBase is an external service and may have usage limits or paid plans.

Then ask your agent:

```text
Research this claim across independent web and academic sources, show where
sources disagree, and validate the evidence ledger before answering.
```

## Offline validation

The bundled validator makes no network calls:

```bash
python3 agent_skills/sandbase-multi-source-research/scripts/validate_report.py research-report.json
```

It checks report structure, URLs, unique IDs, source references, provider
diversity, and confidence thresholds. It does not prove that claims are true.

Run the deterministic eval:

```bash
python3 agent_skills/evals/sandbase-multi-source-research/test_validate_report.py
```

Apache-2.0.

