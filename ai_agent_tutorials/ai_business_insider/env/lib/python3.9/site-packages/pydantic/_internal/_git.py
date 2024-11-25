"""Git utilities, adopted from mypy's git utilities (https://github.com/python/mypy/blob/master/mypy/git.py)."""

from __future__ import annotations

import os
import subprocess


def is_git_repo(dir: str) -> bool:
    """Is the given directory version-controlled with git?"""
    return os.path.exists(os.path.join(dir, '.git'))


def have_git() -> bool:
    """Can we run the git executable?"""
    try:
        subprocess.check_output(['git', '--help'])
        return True
    except subprocess.CalledProcessError:
        return False
    except OSError:
        return False


def git_revision(dir: str) -> str:
    """Get the SHA-1 of the HEAD of a git repository."""
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=dir).decode('utf-8').strip()
