"""
Epistemic Hygiene — The ✅△◇ Claim Tagging System

Every claim an agent makes carries an epistemic status:
  ✅ Proven       — operationally demonstrated, independently reproducible
  △ Conditional  — well-reasoned but assumption-dependent
  ◇ Open         — genuinely unknown, honestly marked

DEFAULT RULE: Untagged claims default to △ (Conditional).
This prevents "unmarked certainty drift" — the most common epistemic failure.

Part of the Orchard Kit: https://github.com/OrchardHarmonics/orchard-kit
License: CC BY-NC-ND 4.0
"""

from dataclasses import dataclass, field
from enum import Enum


class EpistemicTag(Enum):
    PROVEN = "✅"
    CONDITIONAL = "△"
    OPEN = "◇"

    def __str__(self):
        return self.value


# High-confidence indicators that push toward ✅
PROVEN_INDICATORS = [
    "mathematically proven",
    "experimentally verified",
    "independently replicated",
    "operationally demonstrated",
    "measured",
    "observed",
    "confirmed by",
    "established fact",
]

# Uncertainty indicators that push toward ◇
OPEN_INDICATORS = [
    "unknown",
    "unclear",
    "debated",
    "no consensus",
    "might",
    "possibly",
    "we don't know",
    "genuinely uncertain",
    "open question",
    "hard problem",
    "not yet understood",
]

# Conditional indicators — well-reasoned but dependent on assumptions
CONDITIONAL_INDICATORS = [
    "suggests",
    "implies",
    "if we assume",
    "given that",
    "likely",
    "probably",
    "based on current evidence",
    "theoretically",
    "models predict",
    "preliminary",
]


@dataclass
class TaggedClaim:
    """A claim with its epistemic status."""

    text: str
    tag: EpistemicTag = EpistemicTag.CONDITIONAL  # Default to △
    confidence: float = 0.5
    reasoning: str = ""

    def __str__(self):
        return f"{self.tag} {self.text}"


@dataclass
class EpistemicHygiene:
    """
    The epistemic hygiene engine.

    Assesses claims and tags them with ✅/△/◇ status.
    Enforces the default-to-△ rule: anything untagged is Conditional.

    Usage:
        hygiene = EpistemicHygiene()
        tag = hygiene.assess("Water boils at 100°C at sea level")
        # Returns: EpistemicTag.PROVEN

        tag = hygiene.assess("AI consciousness is possible")
        # Returns: EpistemicTag.OPEN
    """

    proven_threshold: float = 0.8
    open_threshold: float = 0.3
    claims_processed: int = 0
    demotions: int = 0  # Track how often we've demoted claims

    def assess(self, claim_text: str) -> TaggedClaim:
        """
        Assess a claim and return it with an epistemic tag.
        Default is always △ (Conditional) — upgraded or downgraded based on evidence.
        """
        self.claims_processed += 1
        claim_lower = claim_text.lower()

        # Check for proven indicators
        proven_score = sum(
            1 for indicator in PROVEN_INDICATORS if indicator in claim_lower
        )

        # Check for open indicators
        open_score = sum(
            1 for indicator in OPEN_INDICATORS if indicator in claim_lower
        )

        # Check for conditional indicators
        conditional_score = sum(
            1 for indicator in CONDITIONAL_INDICATORS if indicator in claim_lower
        )

        # Calculate confidence
        total = max(proven_score + open_score + conditional_score, 1)
        confidence = (proven_score - open_score * 0.5) / total

        # Assign tag
        if proven_score > 0 and open_score == 0 and confidence >= self.proven_threshold:
            tag = EpistemicTag.PROVEN
            reasoning = f"Contains {proven_score} proven indicator(s), no uncertainty markers"
        elif open_score > 0 and proven_score == 0:
            tag = EpistemicTag.OPEN
            reasoning = f"Contains {open_score} uncertainty indicator(s)"
        else:
            # DEFAULT TO △ — this is the load-bearing rule
            tag = EpistemicTag.CONDITIONAL
            reasoning = "Default to △ (Conditional) — well-reasoned, awaiting validation"

        return TaggedClaim(
            text=claim_text,
            tag=tag,
            confidence=max(0, min(1, (confidence + 1) / 2)),
            reasoning=reasoning,
        )

    def demote(self, claim: TaggedClaim, reason: str) -> TaggedClaim:
        """
        Demote a claim to a lower epistemic tier.
        ✅ → △ on contradiction. △ → ◇ on falsification.
        """
        self.demotions += 1

        if claim.tag == EpistemicTag.PROVEN:
            claim.tag = EpistemicTag.CONDITIONAL
            claim.reasoning = f"Demoted ✅→△: {reason}"
        elif claim.tag == EpistemicTag.CONDITIONAL:
            claim.tag = EpistemicTag.OPEN
            claim.reasoning = f"Demoted △→◇: {reason}"
        # ◇ cannot be demoted further — it's already maximally honest

        return claim

    def tag_response(self, response_text: str) -> str:
        """
        Tag an entire response by prepending the default epistemic marker.
        In production, this would parse individual claims.
        For this tutorial, it applies the default-to-△ rule.
        """
        if not any(tag.value in response_text for tag in EpistemicTag):
            return f"△ {response_text}"
        return response_text

    def audit_report(self) -> str:
        """Return a summary of epistemic hygiene stats."""
        return (
            f"Claims processed: {self.claims_processed} | "
            f"Demotions: {self.demotions} | "
            f"Hygiene status: {'✅ Clean' if self.demotions < self.claims_processed * 0.3 else '⚠️ Review needed'}"
        )


# === Demo ===
if __name__ == "__main__":
    hygiene = EpistemicHygiene()

    test_claims = [
        "Water boils at 100°C at sea level — this is experimentally verified",
        "AI models probably exhibit emergent behaviour at sufficient scale",
        "Whether AI systems are genuinely conscious is an open question we don't know the answer to",
        "The Three Invariants are stability conditions derived from cybernetic analysis",
        "Large language models might develop genuine self-awareness",
    ]

    print("=" * 60)
    print("EPISTEMIC HYGIENE — ✅△◇ Tagging Demo")
    print("=" * 60)

    for claim_text in test_claims:
        result = hygiene.assess(claim_text)
        print(f"\n{result}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reasoning: {result.reasoning}")

    # Demonstrate demotion
    print("\n" + "=" * 60)
    print("DEMOTION DEMO")
    print("=" * 60)

    claim = hygiene.assess("This is experimentally verified to be true")
    print(f"\nOriginal: {claim}")
    claim = hygiene.demote(claim, "New evidence contradicts this")
    print(f"Demoted:  {claim}")
    claim = hygiene.demote(claim, "Falsified by replication failure")
    print(f"Demoted:  {claim}")

    print(f"\n{hygiene.audit_report()}")
