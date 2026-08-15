"""Signal classifier and ranker for dependency releases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

try:
    from .radar import ReleaseCandidate
except ImportError:
    from radar import ReleaseCandidate


SIGNAL_TERMS = {
    "security fix": (
        "security fix",
        "security vulnerability",
        "vulnerability",
        "cve-",
        "security advisory",
    ),
    "breaking change": (
        "breaking change",
        "breaking:",
        "not backward compatible",
        "migration required",
        "removed support",
    ),
    "deprecation": ("deprecated", "deprecation", "will be removed"),
    "yanked release": ("yanked", "withdrawn release", "do not use this release"),
}

SIGNAL_SCORES = {
    "security fix": 100,
    "breaking change": 90,
    "yanked release": 85,
    "major version": 70,
    "deprecation": 60,
}

REASON_ORDER = tuple(SIGNAL_SCORES)


@dataclass(frozen=True)
class RankedRelease:
    dependency: str
    github_repo: str
    current_version: str | None
    release_version: str
    version_delta: str
    title: str
    notes: str
    release_url: str
    published_at: str
    reasons: tuple[str, ...]
    score: int
    why_you_care: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _why_you_care(dependency: str, reasons: tuple[str, ...]) -> str:
    if "security fix" in reasons:
        return f"{dependency} fixes a security risk; review exposure and patch promptly."
    if "breaking change" in reasons:
        return f"{dependency} may break existing integrations; read its migration notes before upgrading."
    if "yanked release" in reasons:
        return f"Avoid the affected {dependency} release and check whether your lockfile selected it."
    if "major version" in reasons:
        return f"{dependency} crossed a major version, so expect migration work before upgrading."
    return f"{dependency} is retiring an API; plan its replacement before removal."


def classify_release(candidate: ReleaseCandidate) -> RankedRelease | None:
    """Classify one release and drop it when it contains only routine noise."""

    searchable = f"{candidate.title}\n{candidate.notes}".lower()
    reasons = {
        reason
        for reason, terms in SIGNAL_TERMS.items()
        if any(term in searchable for term in terms)
    }
    if candidate.version_delta == "major":
        reasons.add("major version")
    ordered_reasons = tuple(reason for reason in REASON_ORDER if reason in reasons)
    if not ordered_reasons:
        return None

    score = max(SIGNAL_SCORES[reason] for reason in ordered_reasons)
    score += max(0, len(ordered_reasons) - 1) * 5
    return RankedRelease(
        dependency=candidate.dependency,
        github_repo=candidate.github_repo,
        current_version=candidate.current_version,
        release_version=candidate.release_version,
        version_delta=candidate.version_delta,
        title=candidate.title,
        notes=candidate.notes,
        release_url=candidate.release_url,
        published_at=candidate.published_at,
        reasons=ordered_reasons,
        score=score,
        why_you_care=_why_you_care(candidate.dependency, ordered_reasons),
    )


def rank_releases(candidates: list[ReleaseCandidate]) -> list[RankedRelease]:
    """Filter routine releases and sort the rest by user impact."""

    classified = [
        release
        for candidate in candidates
        if (release := classify_release(candidate)) is not None
    ]
    return sorted(
        classified,
        key=lambda release: (
            release.score,
            release.published_at,
            release.release_version,
        ),
        reverse=True,
    )
