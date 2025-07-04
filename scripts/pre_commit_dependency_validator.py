#!/usr/bin/env python3
"""
Pre-commit hook for validating Python dependencies
Ensures all dependencies are properly pinned and secure
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple
import requests
from packaging import version
import json


def check_pinned_versions(filepath: str) -> List[Tuple[str, str]]:
    """Check if all dependencies have pinned versions."""
    unpinned = []
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check if version is properly pinned
            if not any(op in line for op in ['==', '~=', '<=']):
                # Extract package name
                package = re.split(r'[<>=!~]', line)[0].strip()
                unpinned.append((package, f"Line {line_num}: {line}"))
    
    return unpinned


def check_typosquatting(packages: List[str]) -> List[Tuple[str, str]]:
    """Check for potential typosquatting packages."""
    suspicious = []
    
    # Common typosquatting patterns
    typo_patterns = {
        'tensoflow': 'tensorflow',
        'beautifulsoup': 'beautifulsoup4',
        'django-rest': 'djangorestframework',
        'pillow': 'Pillow',
        'pyyaml': 'PyYAML',
        'numpy-financial': 'numpy_financial',
        'dateutil': 'python-dateutil',
        'skimage': 'scikit-image',
        'sklearn': 'scikit-learn',
    }
    
    for package in packages:
        pkg_lower = package.lower()
        for typo, correct in typo_patterns.items():
            if pkg_lower == typo:
                suspicious.append((package, f"Possible typo of '{correct}'"))
    
    return suspicious


def check_deprecated_packages(packages: List[str]) -> List[Tuple[str, str]]:
    """Check for deprecated packages."""
    deprecated = {
        'nose': 'Use pytest instead',
        'distribute': 'Use setuptools instead',
        'pycrypto': 'Use cryptography instead',
        'PIL': 'Use Pillow instead',
        'oauth': 'Use oauthlib instead',
    }
    
    found_deprecated = []
    for package in packages:
        if package in deprecated:
            found_deprecated.append((package, deprecated[package]))
    
    return found_deprecated


def validate_requirements_file(filepath: str) -> bool:
    """Main validation function."""
    print(f"\n🔍 Validating {filepath}...")
    
    # Read all packages
    packages = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                package = re.split(r'[<>=!~]', line)[0].strip()
                packages.append(package)
    
    errors = []
    warnings = []
    
    # Check for unpinned versions
    unpinned = check_pinned_versions(filepath)
    if unpinned:
        for pkg, details in unpinned:
            warnings.append(f"⚠️  Unpinned dependency: {details}")
    
    # Check for typosquatting
    typos = check_typosquatting(packages)
    if typos:
        for pkg, reason in typos:
            errors.append(f"❌ Suspicious package '{pkg}': {reason}")
    
    # Check for deprecated packages
    deprecated = check_deprecated_packages(packages)
    if deprecated:
        for pkg, suggestion in deprecated:
            warnings.append(f"⚠️  Deprecated package '{pkg}': {suggestion}")
    
    # Print results
    if errors:
        print("\n❌ ERRORS found:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\n⚠️  WARNINGS found:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("✅ All dependencies look good!")
    
    # Return True if no errors (warnings are OK)
    return len(errors) == 0


def main():
    """Pre-commit hook entry point."""
    files = sys.argv[1:]
    
    if not files:
        print("No files to validate")
        return 0
    
    all_valid = True
    for filepath in files:
        if not validate_requirements_file(filepath):
            all_valid = False
    
    if not all_valid:
        print("\n❌ Dependency validation failed!")
        print("Fix the errors above or use --no-verify to skip (not recommended)")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())