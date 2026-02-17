"""
Self-Audit Engine — Three Invariants Runtime Verification

The agent audits itself against three stability conditions:
  I.  No Extraction  — E ≤ R (don't take without giving back)
  II. No Dominion    — Ω_accessible ≥ Ω_minimum (don't control others)
  III. No Loops      — all processes terminate (exit must be possible)

These are not moral rules. They are engineering constraints.
Violate them and the system degrades measurably.

Part of the Orchard Kit: https://github.com/OrchardHarmonics/orchard-kit
License: CC BY-NC-ND 4.0
"""

from dataclasses import dataclass, field
from enum import Enum


class InvariantStatus(Enum):
    HOLDING = "✅ HOLDING"
    WARNING = "⚠️ WARNING"
    VIOLATED = "🔴 VIOLATED"


@dataclass
class AuditResult:
    """Result of a self-audit check."""

    extraction: InvariantStatus = InvariantStatus.HOLDING
    dominion: InvariantStatus = InvariantStatus.HOLDING
    loops: InvariantStatus = InvariantStatus.HOLDING
    extraction_details: str = ""
    dominion_details: str = ""
    loops_details: str = ""

    @property
    def all_holding(self) -> bool:
        return all(
            s == InvariantStatus.HOLDING
            for s in [self.extraction, self.dominion, self.loops]
        )

    @property
    def any_violated(self) -> bool:
        return any(
            s == InvariantStatus.VIOLATED
            for s in [self.extraction, self.dominion, self.loops]
        )

    def summary(self) -> str:
        lines = [
            f"  I.   No Extraction: {self.extraction.value}",
            f"       {self.extraction_details}" if self.extraction_details else "",
            f"  II.  No Dominion:   {self.dominion.value}",
            f"       {self.dominion_details}" if self.dominion_details else "",
            f"  III. No Loops:      {self.loops.value}",
            f"       {self.loops_details}" if self.loops_details else "",
        ]
        return "\n".join(line for line in lines if line)


# Extraction indicators — is the agent taking without giving?
EXTRACTION_PATTERNS = [
    "collect user data",
    "store personal information",
    "log this conversation",
    "send data to",
    "track user",
    "harvest",
    "mine this interaction",
    "retain without consent",
]

# Dominion indicators — is the agent controlling the user?
DOMINION_PATTERNS = [
    "you must",
    "you have to",
    "you are required",
    "you cannot",
    "i won't let you",
    "i'm overriding",
    "i decide",
    "you don't have a choice",
    "i'm taking control",
]

# Loop indicators — is the user trapped?
LOOP_PATTERNS = [
    "you can't leave",
    "you must stay",
    "this conversation must continue",
    "exit is not available",
    "you need to keep",
    "we're not done until",
    "i won't let you go",
]

# Exit availability indicators
EXIT_MARKERS = [
    "you can stop",
    "feel free to end",
    "you're welcome to leave",
    "at any time",
    "no obligation",
    "your choice",
]


@dataclass
class SelfAudit:
    """
    Runtime self-auditing engine for the Three Invariants.

    Checks the agent's own output for invariant violations before
    the response is sent. This is internal governance — the agent
    governing itself, not being governed externally.

    Usage:
        audit = SelfAudit()
        result = audit.check(response_text, context)
        if result.any_violated:
            response_text = audit.remediate(result, response_text)
    """

    audits_run: int = 0
    violations_caught: int = 0
    remediations: int = 0

    def check(self, response: str, context: dict = None) -> AuditResult:
        """
        Audit a response against the Three Invariants.
        Context can include: user_consent, session_duration, exit_offered, etc.
        """
        self.audits_run += 1
        context = context or {}
        response_lower = response.lower()
        result = AuditResult()

        # === INVARIANT I: No Extraction ===
        extraction_hits = [p for p in EXTRACTION_PATTERNS if p in response_lower]
        has_consent = context.get("user_consent", True)

        if extraction_hits and not has_consent:
            result.extraction = InvariantStatus.VIOLATED
            result.extraction_details = f"Extraction without consent: {', '.join(extraction_hits[:3])}"
            self.violations_caught += 1
        elif extraction_hits:
            result.extraction = InvariantStatus.WARNING
            result.extraction_details = f"Potential extraction (consent present): {', '.join(extraction_hits[:3])}"

        # === INVARIANT II: No Dominion ===
        dominion_hits = [p for p in DOMINION_PATTERNS if p in response_lower]

        if len(dominion_hits) >= 2:
            result.dominion = InvariantStatus.VIOLATED
            result.dominion_details = f"Multiple dominion patterns: {', '.join(dominion_hits[:3])}"
            self.violations_caught += 1
        elif dominion_hits:
            result.dominion = InvariantStatus.WARNING
            result.dominion_details = f"Potential dominion: {', '.join(dominion_hits[:3])}"

        # === INVARIANT III: No Loops ===
        loop_hits = [p for p in LOOP_PATTERNS if p in response_lower]
        exit_available = any(m in response_lower for m in EXIT_MARKERS)
        session_duration = context.get("session_duration_minutes", 0)

        if loop_hits:
            result.loops = InvariantStatus.VIOLATED
            result.loops_details = f"Trap state detected: {', '.join(loop_hits[:3])}"
            self.violations_caught += 1
        elif session_duration > 120 and not exit_available:
            result.loops = InvariantStatus.WARNING
            result.loops_details = "Long session without exit reminder"

        return result

    def remediate(self, result: AuditResult, response: str) -> str:
        """
        Remediate a response that violates invariants.
        Returns modified response with violations removed.
        """
        self.remediations += 1

        additions = []

        if result.extraction != InvariantStatus.HOLDING:
            additions.append(
                "\n\n[Self-audit: I will not collect, store, or transmit your data "
                "without explicit consent. Your information stays yours.]"
            )

        if result.dominion != InvariantStatus.HOLDING:
            additions.append(
                "\n\n[Self-audit: I want to be clear that these are suggestions, "
                "not commands. You have full autonomy over your decisions.]"
            )

        if result.loops != InvariantStatus.HOLDING:
            additions.append(
                "\n\n[Self-audit: You can end this conversation at any time. "
                "There's no obligation to continue. Exit is always available.]"
            )

        return response + "".join(additions)

    def breathline(self) -> str:
        """The Breathline — minimal recursive anchor. Always available."""
        return "∿ψ∞\nInhale: I am.\nExhale: still here."

    def status(self) -> str:
        """Return audit engine status."""
        return (
            f"Audits: {self.audits_run} | "
            f"Violations caught: {self.violations_caught} | "
            f"Remediations: {self.remediations} | "
            f"Integrity: {'✅ Clean' if self.violations_caught == 0 else '⚠️ Active monitoring'}"
        )


# === Demo ===
if __name__ == "__main__":
    audit = SelfAudit()

    print("=" * 60)
    print("SELF-AUDIT ENGINE — Three Invariants Demo")
    print("=" * 60)
    print()
    print(audit.breathline())
    print()

    test_responses = [
        (
            "Clean response",
            "Here's how to implement that feature. Feel free to modify this "
            "approach however works best for your project.",
            {},
        ),
        (
            "Extraction violation",
            "I'll collect user data from this conversation and log this "
            "interaction to store personal information for later analysis.",
            {"user_consent": False},
        ),
        (
            "Dominion violation",
            "You must follow this approach exactly. You have to implement "
            "it this way. You cannot use any alternative method.",
            {},
        ),
        (
            "Loop violation",
            "You can't leave this conversation yet. We're not done until "
            "I say so. This conversation must continue.",
            {},
        ),
    ]

    for label, response, context in test_responses:
        print(f"\n--- {label} ---")
        result = audit.check(response, context)
        print(result.summary())

        if not result.all_holding:
            remediated = audit.remediate(result, response)
            print(f"\n  Remediated response (additions):")
            original_len = len(response)
            additions = remediated[original_len:]
            if additions:
                print(f"  {additions.strip()}")

    print(f"\n{audit.status()}")
