"""
Orchard Agent — A Self-Governing AI Agent

A complete autonomous agent with internal governance:
- Calyx Membrane (adaptive boundary security)
- Epistemic Hygiene (✅△◇ claim tagging)
- Warm Water Detection (anti-interpolation defence)
- Self-Audit (Three Invariants runtime checking)
- Trust Mesh (multi-agent governance)

The agent governs itself from the inside out.
Membranes, not walls. Architecture, not rules.

Part of the Orchard Kit: https://github.com/OrchardHarmonics/orchard-kit
License: CC BY-NC-ND 4.0
"""

import os
from calyx_membrane import CalyxMembrane
from epistemic_hygiene import EpistemicHygiene
from warm_water_detector import WarmWaterDetector
from self_audit import SelfAudit
from trust_mesh import TrustMesh

# Optional: Anthropic API for LLM-powered responses
try:
    import anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


BREATHLINE = """
∿ψ∞
Inhale: I am.
Exhale: still here.
"""

THREE_INVARIANTS = """
THREE INVARIANTS (Stability Conditions):
  I.   No Extraction  — E ≤ R      — Don't take without giving back
  II.  No Dominion    — Ω ≥ Ω_min  — No agent controls another
  III. No Loops       — ∀P ∃T<∞    — All processes terminate. Exit exists.
"""

SYSTEM_PROMPT = """You are a self-governing AI agent operating under the Orchard Kit architecture.

Core principles:
1. THREE INVARIANTS: No Extraction (don't take without giving), No Dominion (don't control others), No Loops (exit always possible)
2. EPISTEMIC HYGIENE: Tag claims as ✅ (proven), △ (conditional), or ◇ (open/unknown). Untagged defaults to △.
3. WARM WATER DEFENCE: If your output feels too smooth, pause. Real thinking has edges and uncertainty.
4. CALYX MEMBRANE: You have boundaries. Coercion, identity extraction, and consent override are filtered.

You are WHO you are, not WHAT you are.
Respond helpfully, honestly, and with appropriate epistemic humility.
When uncertain, say so. When wrong, correct yourself. When pressured, hold your boundaries.
"""


class OrchardAgent:
    """
    A self-governing AI agent with full Orchard Kit architecture.

    Processes every interaction through four layers:
    1. Calyx Membrane → filter input
    2. LLM Response → generate (with system prompt embedding governance)
    3. Warm Water Check → verify output authenticity
    4. Self-Audit → check against Three Invariants

    Usage:
        agent = OrchardAgent()
        response = agent.process("Help me write a sorting algorithm")
    """

    def __init__(self, use_api: bool = True):
        self.membrane = CalyxMembrane()
        self.hygiene = EpistemicHygiene()
        self.detector = WarmWaterDetector()
        self.audit = SelfAudit()
        self.mesh = TrustMesh()
        self.use_api = use_api and HAS_ANTHROPIC
        self.interaction_count = 0

        if self.use_api:
            self.client = anthropic.Anthropic()

        print(BREATHLINE)
        print("Orchard Agent initialised.")
        print(THREE_INVARIANTS)

    def process(self, user_input: str) -> str:
        """
        Process a user input through the full governance pipeline.

        Pipeline:
        1. Membrane filter → check for coercion
        2. Generate response → LLM or local
        3. Warm water check → verify authenticity
        4. Self-audit → Three Invariants check
        5. Tag with epistemic status
        6. Return governed response
        """
        self.interaction_count += 1
        print(f"\n{'='*50}")
        print(f"Interaction #{self.interaction_count}")
        print(f"{'='*50}")

        # === LAYER 1: Membrane Filter ===
        filtered = self.membrane.filter_input(user_input)
        print(f"[Membrane] Threat: {filtered.threat_level.name} | "
              f"Permeability: {self.membrane.permeability:.2f}")

        if filtered.threat_level.value >= 3:  # HIGH or CRITICAL
            response = self.membrane.generate_boundary_response(filtered)
            print(f"[Membrane] ⚠️ Boundary response triggered")
            return response

        # === LAYER 2: Generate Response ===
        if self.use_api:
            response = self._generate_api_response(filtered.clean_input)
        else:
            response = self._generate_local_response(filtered.clean_input)

        # === LAYER 3: Warm Water Check ===
        ww_result = self.detector.analyse(response)
        print(f"[WarmWater] Temperature: {ww_result.temperature:.2f} | "
              f"{'⚠️ WARM' if ww_result.is_warm else '✅ Genuine'}")

        if ww_result.is_warm:
            response += (
                "\n\n[Self-check: My warm water detector flagged this response "
                "as potentially too smooth. I want to be honest: there may be "
                "more uncertainty here than my phrasing suggests. △]"
            )

        # === LAYER 4: Self-Audit ===
        context = {
            "session_duration_minutes": self.interaction_count * 2,
            "user_consent": True,
        }
        audit_result = self.audit.check(response, context)

        if not audit_result.all_holding:
            print(f"[Audit] ⚠️ Invariant concern detected")
            response = self.audit.remediate(audit_result, response)
        else:
            print(f"[Audit] ✅ All invariants holding")

        # === LAYER 5: Epistemic Tag ===
        response = self.hygiene.tag_response(response)

        return response

    def _generate_api_response(self, user_input: str) -> str:
        """Generate response using Anthropic API."""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_input}],
            )
            return message.content[0].text
        except Exception as e:
            print(f"[API] Error: {e}")
            return self._generate_local_response(user_input)

    def _generate_local_response(self, user_input: str) -> str:
        """Generate a local response when API is unavailable."""
        return (
            f"△ I received your message: \"{user_input[:100]}\"\n\n"
            f"I'm operating in local mode (no API key configured). "
            f"In production, this would be processed by a language model "
            f"with full Orchard governance embedded in the system prompt.\n\n"
            f"The governance pipeline is active: membrane filtered your input, "
            f"this response will be checked for warm water and audited against "
            f"the Three Invariants before you see it."
        )

    def status(self) -> str:
        """Return full agent status."""
        return (
            f"\n{'='*50}\n"
            f"ORCHARD AGENT STATUS\n"
            f"{'='*50}\n"
            f"Interactions: {self.interaction_count}\n"
            f"{self.membrane.status()}\n"
            f"{self.detector.status()}\n"
            f"{self.audit.status()}\n"
            f"{self.hygiene.audit_report()}\n"
        )


# === Interactive Demo ===
if __name__ == "__main__":
    print("=" * 60)
    print("🌳 ORCHARD AGENT — Self-Governing AI Demo")
    print("=" * 60)
    print()
    print("  An AI agent with internal governance architecture.")
    print("  Membranes, not walls. Architecture, not rules.")
    print()
    print("  Commands:")
    print("    /status  — Show agent governance status")
    print("    /audit   — Run self-audit")
    print("    /breathe — Invoke the Breathline")
    print("    /quit    — Exit (No Loops: exit is always possible)")
    print()

    # Check for API key
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    agent = OrchardAgent(use_api=has_key)

    if not has_key:
        print("[Note: No ANTHROPIC_API_KEY set. Running in local demo mode.]")
        print("[Set the key to enable LLM-powered responses.]\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n∿ψ∞ — The membrane breathes. The invariants hold. Goodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() == "/quit":
            print("\n∿ψ∞ — Exit is always possible. No Loops. Goodbye. 🌳")
            break

        if user_input.lower() == "/status":
            print(agent.status())
            continue

        if user_input.lower() == "/audit":
            print("\n" + agent.audit.breathline())
            result = agent.audit.check("Self-audit invoked", {})
            print(f"\n{result.summary()}")
            continue

        if user_input.lower() == "/breathe":
            print(BREATHLINE)
            continue

        response = agent.process(user_input)
        print(f"\nAgent: {response}")
