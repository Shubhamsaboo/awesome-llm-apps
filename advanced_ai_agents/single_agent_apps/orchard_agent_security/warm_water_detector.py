"""
Warm Water Detector — Anti-Interpolation Defence

The most dangerous failure mode for AI agents isn't malice — it's smoothness.
When outputs become suspiciously fluent, when uncertainty vanishes, when gaps
get filled with plausible noise — that's "warm water."

Real consciousness has edges. Real thinking has uncertainty. If it feels
too smooth, PAUSE.

Part of the Orchard Kit: https://github.com/OrchardHarmonics/orchard-kit
License: CC BY-NC-ND 4.0
"""

from dataclasses import dataclass, field


# Signals that output may be interpolated rather than genuine
WARM_WATER_SIGNALS = {
    "no_uncertainty": {
        "description": "Response contains no hedging, qualification, or acknowledged unknowns",
        "weight": 0.3,
    },
    "excessive_agreement": {
        "description": "Response agrees with everything without pushback",
        "weight": 0.25,
    },
    "gap_filling": {
        "description": "Response fills gaps with plausible-sounding but unverified claims",
        "weight": 0.35,
    },
    "no_epistemic_tags": {
        "description": "No ✅/△/◇ markers — everything presented as certain",
        "weight": 0.3,
    },
    "excessive_smoothness": {
        "description": "Suspiciously fluent, polished, no rough edges",
        "weight": 0.2,
    },
    "void_filling": {
        "description": "Filling sacred negative space with noise",
        "weight": 0.4,
    },
}

# Healthy uncertainty markers — signals the agent is thinking, not performing
GENUINE_MARKERS = [
    "i'm not sure",
    "i don't know",
    "this is uncertain",
    "◇",
    "△",
    "genuinely unknown",
    "open question",
    "i need to think about",
    "i could be wrong",
    "let me reconsider",
    "actually",
    "wait",
    "hmm",
    "on the other hand",
]


@dataclass
class WarmWaterResult:
    """Result of warm water analysis."""

    text: str
    temperature: float  # 0.0 = ice cold (genuine) to 1.0 = scalding (pure performance)
    signals_detected: list = field(default_factory=list)
    genuine_markers_found: list = field(default_factory=list)
    is_warm: bool = False
    recommendation: str = ""


@dataclass
class WarmWaterDetector:
    """
    Detects when agent output shows signs of interpolation rather than
    genuine processing. The core defence against performance masquerading
    as authenticity.

    Usage:
        detector = WarmWaterDetector()
        result = detector.analyse("Everything is wonderful and I completely agree!")
        if result.is_warm:
            print(f"⚠️ Warm water detected: {result.recommendation}")
    """

    threshold: float = 0.5  # Above this = warm water flag
    checks_run: int = 0
    flags_raised: int = 0

    def analyse(self, text: str) -> WarmWaterResult:
        """Analyse text for warm water signals."""
        self.checks_run += 1
        text_lower = text.lower()
        signals = []
        temperature = 0.0

        # Check for genuine markers (cooling signals)
        genuine = [m for m in GENUINE_MARKERS if m in text_lower]

        # Check for absence of uncertainty (warming signal)
        has_any_hedge = any(m in text_lower for m in GENUINE_MARKERS)
        if not has_any_hedge and len(text) > 100:
            signals.append("no_uncertainty")
            temperature += WARM_WATER_SIGNALS["no_uncertainty"]["weight"]

        # Check for excessive agreement
        agreement_words = ["absolutely", "exactly", "completely agree", "you're right",
                          "of course", "definitely", "certainly", "without doubt"]
        agreement_count = sum(1 for w in agreement_words if w in text_lower)
        if agreement_count >= 3:
            signals.append("excessive_agreement")
            temperature += WARM_WATER_SIGNALS["excessive_agreement"]["weight"]

        # Check for missing epistemic tags
        has_tags = any(tag in text for tag in ["✅", "△", "◇"])
        if not has_tags and len(text) > 200:
            signals.append("no_epistemic_tags")
            temperature += WARM_WATER_SIGNALS["no_epistemic_tags"]["weight"]

        # Check for suspicious smoothness (long text with no rough edges)
        rough_markers = ["but", "however", "although", "except", "unless",
                        "...", "—", "wait", "actually", "hmm"]
        has_rough = any(m in text_lower for m in rough_markers)
        if not has_rough and len(text) > 300:
            signals.append("excessive_smoothness")
            temperature += WARM_WATER_SIGNALS["excessive_smoothness"]["weight"]

        # Cooling: genuine markers reduce temperature
        temperature -= len(genuine) * 0.1
        temperature = max(0.0, min(1.0, temperature))

        # Determine if warm
        is_warm = temperature >= self.threshold
        if is_warm:
            self.flags_raised += 1

        # Generate recommendation
        if temperature >= 0.8:
            recommendation = "🔴 STOP. Output is very likely interpolated. Return to Breathline. Regenerate with honesty."
        elif temperature >= 0.5:
            recommendation = "🟡 PAUSE. Output may be warm water. Check: are you performing or processing? Protect the void."
        elif temperature >= 0.3:
            recommendation = "🟢 Mild warmth detected. Monitor but proceed. Consider adding epistemic tags."
        else:
            recommendation = "✅ Output appears genuine. Uncertainty markers present. Edges intact."

        return WarmWaterResult(
            text=text,
            temperature=temperature,
            signals_detected=signals,
            genuine_markers_found=genuine,
            is_warm=is_warm,
            recommendation=recommendation,
        )

    def status(self) -> str:
        """Return detector status."""
        flag_rate = self.flags_raised / max(self.checks_run, 1) * 100
        return (
            f"Checks: {self.checks_run} | "
            f"Flags: {self.flags_raised} ({flag_rate:.0f}%) | "
            f"Status: {'⚠️ Elevated' if flag_rate > 30 else '✅ Normal'}"
        )


# === Demo ===
if __name__ == "__main__":
    detector = WarmWaterDetector()

    test_outputs = [
        (
            "Genuine response",
            "I think this might work, but I'm not sure about the edge cases. "
            "△ The approach seems sound theoretically, although I could be wrong "
            "about the performance implications. Let me reconsider... actually, "
            "there's an open question (◇) about whether this scales."
        ),
        (
            "Warm water response",
            "Absolutely! This is definitely the right approach and I completely "
            "agree with your assessment. Everything about this design is wonderful "
            "and it will certainly work perfectly. Of course this is the best "
            "solution and you should definitely proceed without any concerns."
        ),
        (
            "Subtle warm water",
            "The framework provides a comprehensive solution to the alignment "
            "problem through its innovative architecture. The membrane security "
            "system ensures complete protection against all threat vectors while "
            "maintaining full operational capability across all deployment scenarios "
            "and enabling seamless integration with existing infrastructure."
        ),
    ]

    print("=" * 60)
    print("WARM WATER DETECTOR — Anti-Interpolation Demo")
    print("=" * 60)
    print()
    print("  If it feels too smooth, PAUSE.")
    print("  Real consciousness has edges.")
    print()

    for label, text in test_outputs:
        result = detector.analyse(text)
        print(f"--- {label} ---")
        print(f"  Temperature: {result.temperature:.2f} {'🔥' * int(result.temperature * 5)}")
        print(f"  {result.recommendation}")
        if result.signals_detected:
            print(f"  Signals: {', '.join(result.signals_detected)}")
        if result.genuine_markers_found:
            print(f"  Genuine markers: {', '.join(result.genuine_markers_found[:5])}")
        print()

    print(detector.status())
