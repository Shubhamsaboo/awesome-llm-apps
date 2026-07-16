"""Dependency manifest and GitHub release pipeline for Release Radar."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


KNOWN_GITHUB_REPOS = {
    "anthropic": "anthropics/anthropic-sdk-python",
    "fastapi": "fastapi/fastapi",
    "google-adk": "google/adk-python",
    "langchain": "langchain-ai/langchain",
    "openai": "openai/openai-python",
    "pydantic": "pydantic/pydantic",
    "react": "facebook/react",
    "requests": "psf/requests",
    "urllib3": "urllib3/urllib3",
    "vite": "vitejs/vite",
    "zod": "colinhacks/zod",
}

VERSION_PATTERN = re.compile(r"(?<!\d)(\d+(?:\.\d+){1,3})(?:[-+][0-9A-Za-z.-]+)?")
GITHUB_PATTERN = re.compile(
    r"(?:github\.com/|github:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.IGNORECASE
)


@dataclass(frozen=True)
class Dependency:
    name: str
    current_version: str | None
    github_repo: str | None
    manifest: str


@dataclass(frozen=True)
class ReleaseCandidate:
    dependency: str
    github_repo: str
    current_version: str | None
    release_version: str
    version_delta: str
    title: str
    notes: str
    release_url: str
    published_at: str
    prerelease: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _extract_version(specifier: str) -> str | None:
    matches = VERSION_PATTERN.findall(specifier)
    return matches[-1] if matches else None


def _github_repo_from_spec(specifier: str) -> str | None:
    match = GITHUB_PATTERN.search(specifier)
    if not match:
        return None
    owner, repo = match.groups()
    return f"{owner}/{repo.removesuffix('.git')}"


def _dependency(name: str, specifier: str, manifest: str) -> Dependency:
    normalized_name = _normalize_name(name)
    github_repo = _github_repo_from_spec(specifier) or KNOWN_GITHUB_REPOS.get(
        normalized_name
    )
    version_specifier = specifier.split(";", 1)[0]
    return Dependency(
        name=normalized_name,
        current_version=_extract_version(version_specifier),
        github_repo=github_repo,
        manifest=manifest,
    )


def _parse_requirements(path: Path) -> list[Dependency]:
    dependencies: list[Dependency] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(" #", 1)[0].strip()
        if not line or line.startswith(("#", "-")):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*(.*)$", line)
        if not match:
            continue
        name, specifier = match.groups()
        dependencies.append(_dependency(name, specifier, path.name))
    return dependencies


def _parse_package_json(path: Path) -> list[Dependency]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse {path}: {exc}") from exc

    declared: dict[str, str] = {}
    for group in ("dependencies", "devDependencies"):
        entries = document.get(group, {})
        if not isinstance(entries, dict):
            continue
        for name, specifier in entries.items():
            if isinstance(name, str) and isinstance(specifier, str):
                declared.setdefault(name, specifier)
    return [
        _dependency(name, specifier, path.name)
        for name, specifier in declared.items()
    ]


def parse_manifest(path: str | Path) -> list[Dependency]:
    """Parse requirements.txt or package.json into dependency records."""

    manifest_path = Path(path).expanduser()
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Dependency manifest not found: {manifest_path}")
    if manifest_path.name == "package.json":
        return _parse_package_json(manifest_path)
    if manifest_path.name.startswith("requirements") and manifest_path.suffix == ".txt":
        return _parse_requirements(manifest_path)
    raise ValueError("Release Radar supports requirements*.txt and package.json manifests.")


def _version_tuple(version: str | None) -> tuple[int, int, int] | None:
    if not version:
        return None
    extracted = _extract_version(version)
    if not extracted:
        return None
    parts = [int(part) for part in extracted.split(".")[:3]]
    parts.extend([0] * (3 - len(parts)))
    return parts[0], parts[1], parts[2]


def version_delta(current: str | None, released: str | None) -> str:
    """Return the semantic size of a dependency version change."""

    current_tuple = _version_tuple(current)
    released_tuple = _version_tuple(released)
    if current_tuple is None or released_tuple is None:
        return "unknown"
    if released_tuple == current_tuple:
        return "same"
    if released_tuple < current_tuple:
        return "older"
    if released_tuple[0] != current_tuple[0]:
        return "major"
    if released_tuple[1] != current_tuple[1]:
        return "minor"
    return "patch"


def sample_dependencies() -> list[Dependency]:
    """Return deterministic dependencies for demos and tests."""

    return [
        _dependency("pydantic", "==1.10.14", "sample/requirements.txt"),
        _dependency("requests", "==2.31.0", "sample/requirements.txt"),
        _dependency("fastapi", "==0.114.0", "sample/requirements.txt"),
        _dependency("react", "^18.2.0", "sample/package.json"),
        _dependency("urllib3", "==2.2.1", "sample/requirements.txt"),
    ]


def sample_release_data() -> dict[str, list[dict[str, Any]]]:
    """Return GitHub-shaped release fixtures with signal and routine noise."""

    return {
        "pydantic/pydantic": [
            {
                "tag_name": "v3.0.0-beta.1",
                "name": "Pydantic 3 beta",
                "body": "Preview release for early testing.",
                "html_url": "https://github.com/pydantic/pydantic/releases/tag/v3.0.0-beta.1",
                "published_at": "2026-07-15T08:00:00Z",
                "draft": False,
                "prerelease": True,
            },
            {
                "tag_name": "v2.0.0",
                "name": "Pydantic 2.0",
                "body": "Breaking change with a migration guide. Deprecated V1 validators.",
                "html_url": "https://github.com/pydantic/pydantic/releases/tag/v2.0.0",
                "published_at": "2026-07-14T08:00:00Z",
                "draft": False,
                "prerelease": False,
            },
        ],
        "psf/requests": [
            {
                "tag_name": "v2.32.3",
                "name": "Requests 2.32.3",
                "body": "Security fix for a proxy credential vulnerability.",
                "html_url": "https://github.com/psf/requests/releases/tag/v2.32.3",
                "published_at": "2026-07-16T07:00:00Z",
                "draft": False,
                "prerelease": False,
            }
        ],
        "fastapi/fastapi": [
            {
                "tag_name": "0.115.0",
                "name": "FastAPI 0.115.0",
                "body": "Breaking change: removed support for the legacy dependency hook.",
                "html_url": "https://github.com/fastapi/fastapi/releases/tag/0.115.0",
                "published_at": "2026-07-13T07:00:00Z",
                "draft": False,
                "prerelease": False,
            }
        ],
        "facebook/react": [
            {
                "tag_name": "v19.0.0",
                "name": "React 19",
                "body": "New stable release with compiler and action APIs.",
                "html_url": "https://github.com/facebook/react/releases/tag/v19.0.0",
                "published_at": "2026-07-12T07:00:00Z",
                "draft": False,
                "prerelease": False,
            }
        ],
        "urllib3/urllib3": [
            {
                "tag_name": "2.2.2",
                "name": "urllib3 2.2.2 routine patch",
                "body": "Documentation corrections and small test cleanup.",
                "html_url": "https://github.com/urllib3/urllib3/releases/tag/2.2.2",
                "published_at": "2026-07-11T07:00:00Z",
                "draft": False,
                "prerelease": False,
            }
        ],
    }


def fetch_github_releases(
    github_repo: str, *, timeout_seconds: int = 15, per_page: int = 5
) -> list[dict[str, Any]]:
    """Fetch recent releases for one owner/repository pair."""

    request = urllib.request.Request(
        f"https://api.github.com/repos/{github_repo}/releases?per_page={per_page}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "release-radar-agent",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("RELEASE_RADAR_GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch releases for {github_repo}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitHub returned invalid JSON for {github_repo}.") from exc
    if not isinstance(payload, list):
        raise RuntimeError(f"GitHub returned an unexpected response for {github_repo}.")
    return [release for release in payload if isinstance(release, dict)]


def build_release_candidates(
    dependencies: list[Dependency],
    release_data_by_repo: dict[str, list[dict[str, Any]]],
) -> tuple[list[ReleaseCandidate], list[str]]:
    """Join dependencies to GitHub releases and compute version deltas."""

    candidates: list[ReleaseCandidate] = []
    errors: list[str] = []
    for dependency in dependencies:
        if not dependency.github_repo:
            errors.append(f"No GitHub repository mapping for {dependency.name}.")
            continue
        for release in release_data_by_repo.get(dependency.github_repo, []):
            if release.get("draft") or release.get("prerelease"):
                continue
            tag_name = str(release.get("tag_name") or release.get("name") or "")
            release_version = _extract_version(tag_name)
            if not release_version:
                continue
            delta = version_delta(dependency.current_version, release_version)
            if delta in {"same", "older"}:
                continue
            candidates.append(
                ReleaseCandidate(
                    dependency=dependency.name,
                    github_repo=dependency.github_repo,
                    current_version=dependency.current_version,
                    release_version=release_version,
                    version_delta=delta,
                    title=str(release.get("name") or tag_name),
                    notes=str(release.get("body") or ""),
                    release_url=str(
                        release.get("html_url")
                        or f"https://github.com/{dependency.github_repo}/releases"
                    ),
                    published_at=str(release.get("published_at") or ""),
                    prerelease=False,
                )
            )
    return candidates, errors


def _live_release_data(
    dependencies: list[Dependency],
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    release_data: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    repositories = sorted(
        {dependency.github_repo for dependency in dependencies if dependency.github_repo}
    )
    if not repositories:
        return release_data, errors

    with ThreadPoolExecutor(max_workers=min(8, len(repositories))) as executor:
        requests = {
            executor.submit(fetch_github_releases, repository): repository
            for repository in repositories
        }
        for request in as_completed(requests):
            repository = requests[request]
            try:
                release_data[repository] = request.result()
            except RuntimeError as exc:
                errors.append(str(exc))
    return release_data, sorted(errors)


def _live_mode_enabled() -> bool:
    return os.environ.get("RELEASE_RADAR_LIVE_GITHUB", "").lower() in {
        "1",
        "true",
        "yes",
    }


def run_release_radar(
    *,
    manifest_path: str | Path | None = None,
    live: bool | None = None,
    top_n: int = 10,
) -> dict[str, Any]:
    """Run manifest parsing, GitHub release scanning, ranking, and rendering."""

    configured_manifest = manifest_path or os.environ.get("RELEASE_RADAR_MANIFEST")
    dependencies = (
        parse_manifest(configured_manifest)
        if configured_manifest
        else sample_dependencies()
    )
    live = _live_mode_enabled() if live is None else live
    release_data, fetch_errors = (
        _live_release_data(dependencies) if live else (sample_release_data(), [])
    )
    candidates, mapping_errors = build_release_candidates(dependencies, release_data)

    try:
        from .delivery import render_brief
        from .ranker import rank_releases
    except ImportError:
        from delivery import render_brief
        from ranker import rank_releases

    ranked = rank_releases(candidates)[: max(1, min(int(top_n), 25))]
    errors = [*fetch_errors, *mapping_errors]
    brief = render_brief(
        ranked,
        watch_mode="live_github" if live else "sample",
        manifest_path=str(configured_manifest or "deterministic sample data"),
        dependencies_checked=len(dependencies),
        errors=errors,
    ).to_dict()
    brief["delivery_note"] = (
        "The brief is rendered only. Scheduled delivery stays off until dry_run=false "
        "and Gmail or webhook settings are present."
    )
    return brief
