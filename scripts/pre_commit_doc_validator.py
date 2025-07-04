#!/usr/bin/env python3
"""
Pre-commit hook for validating documentation standards
Ensures README files follow the repository standards
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple


def check_required_sections(content: str) -> List[str]:
    """Check if README has all required sections."""
    required_sections = [
        'Overview',
        'Features', 
        'Requirements',
        'Installation',
        'Usage'
    ]
    
    missing_sections = []
    content_lower = content.lower()
    
    for section in required_sections:
        # Check for both # and ## headings
        pattern1 = f"# {section.lower()}"
        pattern2 = f"## {section.lower()}"
        
        if pattern1 not in content_lower and pattern2 not in content_lower:
            missing_sections.append(section)
    
    return missing_sections


def check_installation_instructions(content: str) -> List[str]:
    """Validate installation instructions."""
    issues = []
    
    # Check if installation section exists
    install_match = re.search(r'##?\s*Installation.*?\n(.*?)(?=\n##?\s|\Z)', 
                             content, re.IGNORECASE | re.DOTALL)
    
    if install_match:
        install_content = install_match.group(1)
        
        # Check for clear installation steps
        if 'pip install' not in install_content and 'npm install' not in install_content:
            if 'requirements.txt' not in install_content:
                issues.append("Installation section should include clear install commands")
        
        # Check for virtual environment mention (for Python projects)
        if 'pip install' in install_content:
            if not any(term in install_content.lower() for term in ['venv', 'virtualenv', 'conda']):
                issues.append("Consider mentioning virtual environment setup for Python projects")
    
    return issues


def check_code_blocks(content: str) -> List[str]:
    """Check if code blocks are properly formatted."""
    issues = []
    
    # Find all code blocks
    code_blocks = re.findall(r'```([^\n]*)\n(.*?)\n```', content, re.DOTALL)
    
    for i, (lang, code) in enumerate(code_blocks):
        if not lang.strip():
            issues.append(f"Code block {i+1} missing language specifier")
        
        # Check for common issues in code blocks
        if lang in ['bash', 'sh', 'shell']:
            if '$ ' in code:
                issues.append(f"Code block {i+1}: Remove '$ ' prefix from shell commands")
    
    return issues


def check_links(content: str) -> List[str]:
    """Check for broken or malformed links."""
    issues = []
    
    # Find all markdown links
    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
    
    for text, url in links:
        if not url.strip():
            issues.append(f"Empty URL for link '{text}'")
        elif url.startswith('#'):
            # Internal link - check if section exists
            section = url[1:].lower().replace('-', ' ')
            if section not in content.lower():
                issues.append(f"Internal link '{url}' points to non-existent section")
    
    return issues


def check_api_keys(content: str) -> List[str]:
    """Check for exposed API keys or secrets."""
    issues = []
    
    # Common API key patterns
    patterns = [
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'API key'),
        (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'Secret key'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'Token'),
    ]
    
    for pattern, key_type in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if not any(safe in match.lower() for safe in ['your_', 'xxx', '...', '<', 'example']):
                issues.append(f"Possible exposed {key_type}: {match[:30]}...")
    
    return issues


def validate_readme(filepath: str) -> Tuple[bool, List[str], List[str]]:
    """Main validation function."""
    errors = []
    warnings = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required sections
    missing_sections = check_required_sections(content)
    if missing_sections:
        errors.append(f"Missing required sections: {', '.join(missing_sections)}")
    
    # Check installation instructions
    install_issues = check_installation_instructions(content)
    warnings.extend(install_issues)
    
    # Check code blocks
    code_issues = check_code_blocks(content)
    warnings.extend(code_issues)
    
    # Check links
    link_issues = check_links(content)
    warnings.extend(link_issues)
    
    # Check for API keys
    api_issues = check_api_keys(content)
    errors.extend(api_issues)
    
    return len(errors) == 0, errors, warnings


def main():
    """Pre-commit hook entry point."""
    files = sys.argv[1:]
    
    if not files:
        print("No files to validate")
        return 0
    
    all_valid = True
    
    for filepath in files:
        print(f"\n📝 Validating {filepath}...")
        
        is_valid, errors, warnings = validate_readme(filepath)
        
        if errors:
            print("\n❌ ERRORS found:")
            for error in errors:
                print(f"  - {error}")
            all_valid = False
        
        if warnings:
            print("\n⚠️  WARNINGS found:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if not errors and not warnings:
            print("✅ Documentation looks good!")
    
    if not all_valid:
        print("\n❌ Documentation validation failed!")
        print("Fix the errors above or use --no-verify to skip")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())