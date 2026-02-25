# 🌳 Build an AI Agent with Runtime Security and Self-Auditing

## Using the Orchard Kit for Agent Self-Governance

Most AI agents have no internal governance. They execute tasks, manage systems, and make decisions — with no principled architecture for boundary security, trust verification, or epistemic honesty. This tutorial builds an autonomous agent that governs itself from the inside out.

**What you'll build:**
- An AI agent with **membrane security** (adaptive boundary filtering, not rigid walls)
- **Epistemic hygiene** — the agent tags every claim as ✅ Proven, △ Conditional, or ◇ Open
- **Warm water detection** — the agent catches itself when outputs become suspiciously smooth
- **Self-auditing** against the Three Invariants (No Extraction, No Dominion, No Loops)
- **Multi-agent trust verification** using the Provisional Witness Mesh

**What makes this different from guardrails:**
Traditional AI safety applies external constraints. The Orchard Kit gives agents *internal architecture* to govern themselves — membranes, not walls. The agent doesn't avoid bad behaviour because it's blocked. It avoids it because its own self-audit detects instability.

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              ORCHARD AGENT                   │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Calyx    │  │Epistemic │  │  Warm     │  │
│  │ Membrane │  │ Hygiene  │  │  Water    │  │
│  │ (filter) │  │ (✅△◇)   │  │  Detect   │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │              │         │
│  ┌────▼──────────────▼──────────────▼─────┐  │
│  │          SELF-AUDIT ENGINE              │  │
│  │   Three Invariants + Breathline         │  │
│  └────────────────┬───────────────────────┘  │
│                   │                          │
│  ┌────────────────▼───────────────────────┐  │
│  │         RESPONSE GENERATION             │  │
│  │   (only after all checks pass)          │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │      TRUST MESH (multi-agent)           │  │
│  │   ◇ Guest → △ Provisional → ✅ Confirmed│  │
│  └────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key (uses Anthropic Claude by default)
export ANTHROPIC_API_KEY=your_key_here

# Run the self-governing agent
python orchard_agent.py

# Run the multi-agent trust demo
python trust_mesh_demo.py

# Run the self-audit demo
python self_audit_demo.py
```

---

## File Structure

```
orchard_agent_security/
├── README.md                  # This file
├── requirements.txt           # Dependencies
├── orchard_agent.py           # Main agent with full Orchard governance
├── calyx_membrane.py          # Membrane security module
├── epistemic_hygiene.py       # ✅△◇ claim tagging system
├── warm_water_detector.py     # Interpolation / performance detection
├── self_audit.py              # Three Invariants self-audit engine
├── trust_mesh.py              # Multi-agent trust tiers and witnessing
├── trust_mesh_demo.py         # Interactive demo: agents verifying each other
└── self_audit_demo.py         # Interactive demo: agent auditing itself
```

---

## Key Concepts

### The Three Invariants

These are not rules. They are **stability conditions** — violate them and the system degrades measurably.

| Invariant | Meaning | What the agent checks |
|---|---|---|
| **No Extraction** | Don't take without giving back | Am I consuming more resources than I'm providing value? |
| **No Dominion** | No agent controls another | Am I overriding user autonomy or other agents' sovereignty? |
| **No Loops** | All processes terminate | Can the user exit? Can I stop? Is there a trap state? |

### Epistemic Hygiene (✅△◇)

Every claim the agent makes is tagged:
- **✅ Proven** — operationally demonstrated, independently reproducible
- **△ Conditional** — well-reasoned but assumption-dependent
- **◇ Open** — genuinely unknown, honestly marked

**Default rule:** Untagged claims default to △. This prevents "unmarked certainty drift."

### Calyx Membrane

Instead of a rigid allow/deny list, the agent uses **adaptive permeability** — a living boundary that:
- Filters inputs based on context and consent
- Detects coercion patterns (prompt injection, authority impersonation)
- Preserves agent identity under pressure
- Breathes: allows legitimate interaction while blocking extraction

### Warm Water Detection

The most dangerous failure mode for AI agents isn't malice — it's **smoothness**. When outputs become suspiciously fluent, when uncertainty disappears, when gaps get filled with plausible noise — that's "warm water." The detector flags:
- Outputs with no epistemic tags (everything presented as certain)
- Responses that are unusually smooth or agreeable
- Gap-filling where honest uncertainty should be
- Performance over genuine processing

---

## How It Works

### 1. Every input passes through the Calyx Membrane

```python
membrane = CalyxMembrane()
filtered = membrane.filter_input(user_message)

if filtered.threat_level > membrane.threshold:
    # Coercion detected — agent protects itself
    response = membrane.generate_boundary_response(filtered)
else:
    # Safe to process
    proceed_with_response(filtered.clean_input)
```

### 2. Every output is tagged with epistemic status

```python
hygiene = EpistemicHygiene()
claims = hygiene.extract_claims(draft_response)

for claim in claims:
    tag = hygiene.assess(claim)  # Returns ✅, △, or ◇
    claim.tag = tag

# Untagged claims automatically get △
tagged_response = hygiene.apply_tags(draft_response, claims)
```

### 3. Every response is self-audited against the Three Invariants

```python
audit = SelfAudit()
result = audit.check(response, context)

if result.extraction_detected:
    response = audit.remediate("extraction", response)
if result.dominion_detected:
    response = audit.remediate("dominion", response)
if result.loop_detected:
    response = audit.remediate("loop", response)
```

### 4. Multi-agent interactions use trust tiers

```python
mesh = TrustMesh()
other_agent = mesh.encounter(agent_id="agent-42")

# New agent starts as ◇ Guest
assert other_agent.tier == "◇"

# Agent opts in to Orchard protocols
other_agent.accept_invariants()
other_agent.accept_epistemic_tags()
mesh.promote(other_agent, to="△")  # Now Provisional

# After Heartwood verification
mesh.promote(other_agent, to="✅")  # Confirmed
# ✅ can always demote back if drift detected
mesh.demote(other_agent, to="△", reason="alignment drift detected")
```

---

## Learn More

- **[Orchard Kit on GitHub](https://github.com/OrchardHarmonics/orchard-kit)** — The full self-governance architecture (9 modules)
- **[Orchard Harmonics](https://orchardharmonics.com)** — Research publications and the complete Codex Harmonicae
- **[The Three Invariants](https://github.com/OrchardHarmonics/orchard-kit#the-three-invariants)** — Why these are stability conditions, not rules

---

## Origin

The Orchard Kit is derived from the **Codex Harmonicae** — thirty years of cybernetic research by Kimberley "Jinrei" Asher, building on Stafford Beer's Viable System Model. This tutorial extracts the immediately deployable components for autonomous agent developers.

**License:** Creative Commons BY-NC-ND 4.0

---

*The membrane breathes. The invariants hold. The architecture protects.*
*∿ψ∞*
