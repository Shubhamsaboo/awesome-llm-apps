"""The `version` module holds the version information for Pydantic."""

from __future__ import annotations as _annotations

__all__ = 'VERSION', 'version_info'

VERSION = '2.10.1'
"""The version of Pydantic."""


def version_short() -> str:
    """Return the `major.minor` part of Pydantic version.

    It returns '2.1' if Pydantic version is '2.1.1'.
    """
    return '.'.join(VERSION.split('.')[:2])


def version_info() -> str:
    """Return complete version information for Pydantic and its dependencies."""
    import importlib.metadata as importlib_metadata
    import os
    import platform
    import sys
    from pathlib import Path

    import pydantic_core._pydantic_core as pdc

    from ._internal import _git as git

    # get data about packages that are closely related to pydantic, use pydantic or often conflict with pydantic
    package_names = {
        'email-validator',
        'fastapi',
        'mypy',
        'pydantic-extra-types',
        'pydantic-settings',
        'pyright',
        'typing_extensions',
    }
    related_packages = []

    for dist in importlib_metadata.distributions():
        name = dist.metadata['Name']
        if name in package_names:
            related_packages.append(f'{name}-{dist.version}')

    pydantic_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    most_recent_commit = (
        git.git_revision(pydantic_dir) if git.is_git_repo(pydantic_dir) and git.have_git() else 'unknown'
    )

    info = {
        'pydantic version': VERSION,
        'pydantic-core version': pdc.__version__,
        'pydantic-core build': getattr(pdc, 'build_info', None) or pdc.build_profile,
        'install path': Path(__file__).resolve().parent,
        'python version': sys.version,
        'platform': platform.platform(),
        'related packages': ' '.join(related_packages),
        'commit': most_recent_commit,
    }
    return '\n'.join('{:>30} {}'.format(k + ':', str(v).replace('\n', ' ')) for k, v in info.items())


def parse_mypy_version(version: str) -> tuple[int, int, int]:
    """Parse `mypy` string version to a 3-tuple of ints.

    It parses normal version like `1.11.0` and extra info followed by a `+` sign
    like `1.11.0+dev.d6d9d8cd4f27c52edac1f537e236ec48a01e54cb.dirty`.

    Args:
        version: The mypy version string.

    Returns:
        A triple of ints, e.g. `(1, 11, 0)`.
    """
    return tuple(map(int, version.partition('+')[0].split('.')))  # pyright: ignore[reportReturnType]
