#!/usr/bin/env python3
"""
Pre-commit hook for detecting sensitive information
Prevents accidental commits of secrets, API keys, and private data
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple


# Patterns for detecting sensitive information
SENSITIVE_PATTERNS = [
    # API Keys
    (r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'API Key'),
    (r'apikey\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'API Key'),
    
    # Secret Keys
    (r'secret[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'Secret Key'),
    (r'private[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'Private Key'),
    
    # Tokens
    (r'token\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'Token'),
    (r'auth[_-]?token\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?', 'Auth Token'),
    
    # AWS
    (r'aws[_-]?access[_-]?key[_-]?id\s*[:=]\s*["\']?[A-Z0-9]{20}["\']?', 'AWS Access Key'),
    (r'aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9/+=]{40}["\']?', 'AWS Secret Key'),
    
    # OpenAI
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
    (r'openai[_-]?api[_-]?key\s*[:=]\s*["\']?sk-[a-zA-Z0-9]{48}["\']?', 'OpenAI API Key'),
    
    # Anthropic
    (r'anthropic[_-]?api[_-]?key\s*[:=]\s*["\']?sk-ant-[a-zA-Z0-9]{90,}["\']?', 'Anthropic API Key'),
    
    # GitHub
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
    (r'gho_[a-zA-Z0-9]{36}', 'GitHub OAuth Token'),
    
    # Database URLs
    (r'postgres://[^:]+:[^@]+@[^/]+/\w+', 'PostgreSQL Connection String'),
    (r'mongodb\+srv://[^:]+:[^@]+@[^/]+', 'MongoDB Connection String'),
    
    # Generic passwords
    (r'password\s*[:=]\s*["\'][^"\']{8,}["\']', 'Password'),
    (r'passwd\s*[:=]\s*["\'][^"\']{8,}["\']', 'Password'),
]

# Safe patterns to ignore
SAFE_PATTERNS = [
    r'your[_-]?api[_-]?key',
    r'<api[_-]?key>',
    r'xxx+',
    r'\.\.\.+',
    r'example',
    r'test',
    r'demo',
    r'dummy',
    r'placeholder',
    r'changeme',
    r'replace[_-]?this',
]


def is_safe_match(match_text: str) -> bool:
    """Check if a match is actually a safe placeholder."""
    match_lower = match_text.lower()
    
    for safe_pattern in SAFE_PATTERNS:
        if re.search(safe_pattern, match_lower):
            return True
    
    # Check if it's all the same character (like XXXX)
    if len(set(re.sub(r'[^a-zA-Z0-9]', '', match_text))) <= 2:
        return True
    
    return False


def check_file_for_secrets(filepath: str) -> List[Tuple[int, str, str]]:
    """Check a file for potential secrets."""
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError):
        # Skip binary files or files we can't read
        return findings
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments in common languages
        stripped = line.strip()
        if any(stripped.startswith(comment) for comment in ['#', '//', '/*', '*', '--']):
            continue
        
        for pattern, secret_type in SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                match_text = match.group(0)
                
                # Check if it's a safe placeholder
                if is_safe_match(match_text):
                    continue
                
                # Truncate the match for display (don't show the full secret)
                display_text = match_text[:20] + '...' if len(match_text) > 20 else match_text
                findings.append((line_num, secret_type, display_text))
    
    return findings


def check_filename(filepath: str) -> List[str]:
    """Check if filename suggests sensitive content."""
    sensitive_filenames = [
        '.env',
        '.env.local',
        '.env.production',
        'secrets.json',
        'credentials.json',
        'private.key',
        'id_rsa',
        'id_dsa',
        'id_ecdsa',
        'id_ed25519',
    ]
    
    filename = Path(filepath).name
    issues = []
    
    if filename in sensitive_filenames:
        issues.append(f"Sensitive filename: {filename}")
    
    return issues


def main():
    """Pre-commit hook entry point."""
    files = sys.argv[1:]
    
    if not files:
        print("No files to check")
        return 0
    
    total_findings = []
    
    for filepath in files:
        # Skip checking certain files
        if any(skip in filepath for skip in ['.git/', '__pycache__/', 'node_modules/']):
            continue
        
        # Check filename
        filename_issues = check_filename(filepath)
        if filename_issues:
            for issue in filename_issues:
                total_findings.append((filepath, 0, 'Filename', issue))
        
        # Check file content
        secrets = check_file_for_secrets(filepath)
        for line_num, secret_type, display in secrets:
            total_findings.append((filepath, line_num, secret_type, display))
    
    if total_findings:
        print("\n🚨 POTENTIAL SECRETS DETECTED!")
        print("=" * 60)
        
        for filepath, line_num, secret_type, display in total_findings:
            if line_num > 0:
                print(f"\n📄 {filepath}:{line_num}")
                print(f"   Type: {secret_type}")
                print(f"   Found: {display}")
            else:
                print(f"\n📄 {filepath}")
                print(f"   Issue: {display}")
        
        print("\n" + "=" * 60)
        print("❌ Commit blocked to prevent exposing secrets!")
        print("\nOptions:")
        print("1. Remove the sensitive data from the files")
        print("2. Move secrets to environment variables")
        print("3. Add the file to .gitignore if it contains secrets")
        print("4. Use --no-verify to skip (NOT RECOMMENDED)")
        
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())