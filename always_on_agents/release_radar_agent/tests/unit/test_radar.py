import json

from always_on_agents.release_radar_agent.radar import (
    build_release_candidates,
    parse_manifest,
    run_release_radar,
    sample_dependencies,
    sample_release_data,
    version_delta,
)


def test_parse_requirements_manifest(tmp_path):
    manifest = tmp_path / "requirements.txt"
    manifest.write_text(
        "# production dependencies\n"
        "pydantic==1.10.14\n"
        'requests[security]>=2.31.0; python_version >= "3.10"\n'
        "internal-tool @ git+https://github.com/acme/internal-tool.git@v3.2.1\n",
        encoding="utf-8",
    )

    dependencies = parse_manifest(manifest)

    assert [dependency.name for dependency in dependencies] == [
        "pydantic",
        "requests",
        "internal-tool",
    ]
    assert dependencies[0].current_version == "1.10.14"
    assert dependencies[0].github_repo == "pydantic/pydantic"
    assert dependencies[1].current_version == "2.31.0"
    assert dependencies[2].github_repo == "acme/internal-tool"


def test_parse_package_json_includes_runtime_and_dev_dependencies(tmp_path):
    manifest = tmp_path / "package.json"
    manifest.write_text(
        json.dumps(
            {
                "dependencies": {"react": "^18.2.0", "zod": "3.23.8"},
                "devDependencies": {"vite": "~5.4.0"},
            }
        ),
        encoding="utf-8",
    )

    dependencies = parse_manifest(manifest)

    assert [dependency.name for dependency in dependencies] == ["react", "zod", "vite"]
    assert [dependency.current_version for dependency in dependencies] == [
        "18.2.0",
        "3.23.8",
        "5.4.0",
    ]
    assert dependencies[0].github_repo == "facebook/react"


def test_version_delta_distinguishes_release_sizes():
    assert version_delta("1.4.2", "v2.0.0") == "major"
    assert version_delta("1.4.2", "1.5.0") == "minor"
    assert version_delta("1.4.2", "1.4.3") == "patch"
    assert version_delta("1.4.2", "1.4.2") == "same"
    assert version_delta(None, "1.4.3") == "unknown"


def test_sample_candidates_include_version_context_and_skip_prereleases():
    candidates, errors = build_release_candidates(
        sample_dependencies(), sample_release_data()
    )

    assert errors == []
    assert candidates
    assert all(candidate.current_version for candidate in candidates)
    assert all(candidate.release_url.startswith("https://github.com/") for candidate in candidates)
    assert not any(candidate.prerelease for candidate in candidates)


def test_sample_run_renders_text_and_html_without_patch_noise():
    payload = run_release_radar(live=False, top_n=10)

    assert payload["watch_mode"] == "sample"
    assert payload["releases"]
    assert "Release Radar Dependency Brief" in payload["text"]
    assert "<h2>Release Radar Dependency Brief</h2>" in payload["html"]
    assert "routine patch" not in payload["text"].lower()
    reasons = {
        reason
        for release in payload["releases"]
        for reason in release["reasons"]
    }
    assert {"breaking change", "deprecation", "security fix", "major version"} <= reasons
