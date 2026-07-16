from always_on_agents.release_radar_agent.radar import ReleaseCandidate
from always_on_agents.release_radar_agent.ranker import (
    classify_release,
    rank_releases,
)


def candidate(
    *,
    dependency="demo",
    current="1.2.3",
    latest="1.2.4",
    delta="patch",
    title="Demo 1.2.4",
    notes="Small fixes and documentation updates.",
    published="2026-07-15T12:00:00Z",
):
    return ReleaseCandidate(
        dependency=dependency,
        github_repo="example/demo",
        current_version=current,
        release_version=latest,
        version_delta=delta,
        title=title,
        notes=notes,
        release_url="https://github.com/example/demo/releases/tag/v1.2.4",
        published_at=published,
        prerelease=False,
    )


def test_routine_patch_release_is_filtered():
    assert classify_release(candidate()) is None


def test_breaking_deprecation_and_security_signals_are_classified():
    breaking = classify_release(candidate(notes="Breaking change: remove the legacy client."))
    deprecated = classify_release(candidate(notes="Deprecated the old configuration API."))
    security = classify_release(candidate(notes="Security fix for CVE-2026-1234."))

    assert breaking and "breaking change" in breaking.reasons
    assert deprecated and "deprecation" in deprecated.reasons
    assert security and "security fix" in security.reasons


def test_major_version_is_relevant_without_keywords():
    release = classify_release(
        candidate(current="1.9.0", latest="2.0.0", delta="major", title="Demo 2.0")
    )

    assert release and release.reasons == ("major version",)
    assert "migration" in release.why_you_care.lower()


def test_yanked_release_signal_is_not_lost():
    release = classify_release(candidate(notes="This release was yanked. Do not use it."))

    assert release and "yanked release" in release.reasons


def test_ranker_prioritizes_security_and_breaking_releases():
    ranked = rank_releases(
        [
            candidate(dependency="major", latest="2.0.0", delta="major"),
            candidate(dependency="security", notes="Security vulnerability fixed."),
            candidate(dependency="breaking", notes="Breaking change to authentication."),
            candidate(dependency="noise"),
        ]
    )

    assert [release.dependency for release in ranked] == [
        "security",
        "breaking",
        "major",
    ]


def test_equal_priority_releases_put_the_newest_first():
    ranked = rank_releases(
        [
            candidate(
                latest="1.2.4",
                notes="Security fix.",
                published="2026-07-14T12:00:00Z",
            ),
            candidate(
                latest="1.2.5",
                notes="Security fix.",
                published="2026-07-16T12:00:00Z",
            ),
        ]
    )

    assert [release.release_version for release in ranked] == ["1.2.5", "1.2.4"]
