#!/usr/bin/env python3
"""
Apply critical security fixes by pinning package versions
Focus on high-impact security-critical packages
"""

import os
from pathlib import Path
import re

# Critical packages that need version pinning for security
SECURITY_PINS = {
    # Core dependencies
    'streamlit': '1.41.1',
    'openai': '1.58.1',
    'anthropic': '0.39.0',
    'agno': '1.7.0',
    
    # Security-critical packages
    'requests': '2.32.3',
    'urllib3': '2.2.3',
    'cryptography': '44.0.0',
    'pydantic': '2.10.5',
    'sqlalchemy': '2.0.36',
    
    # AI/ML frameworks
    'langchain': '0.3.12',
    'langchain-core': '0.3.28',
    'langchain-community': '0.3.12',
    'crewai': '0.76.9',
    
    # Web frameworks
    'fastapi': '0.115.5',
    'uvicorn': '0.32.1',
    
    # Data processing
    'pandas': '2.2.3',
    'numpy': '1.26.4',
    'pillow': '11.0.0',
}

def pin_version_in_line(line: str) -> str:
    """Pin version for a package line if it's in our security list"""
    # Skip empty lines and comments
    if not line.strip() or line.strip().startswith('#'):
        return line
    
    # Extract package name (handle various formats)
    package_match = re.match(r'^([a-zA-Z0-9_-]+)', line.strip())
    if not package_match:
        return line
    
    package_name = package_match.group(1).lower()
    
    # Check if this package needs pinning
    if package_name in SECURITY_PINS:
        # Already has a version specifier?
        if any(op in line for op in ['==', '>=', '<=', '>', '<', '~=']):
            # Replace with pinned version
            return f"{package_name}=={SECURITY_PINS[package_name]}\n"
        else:
            # Add pinned version
            return f"{package_name}=={SECURITY_PINS[package_name]}\n"
    
    return line

def fix_requirements_file(filepath: Path) -> bool:
    """Fix a single requirements.txt file"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        
        for line in lines:
            new_line = pin_version_in_line(line)
            if new_line != line:
                modified = True
            new_lines.append(new_line)
        
        if modified:
            with open(filepath, 'w') as f:
                f.writelines(new_lines)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Apply security fixes to all requirements.txt files"""
    repo_root = Path('/home/sistr/krljakob/awesome-llm-apps')
    
    # Find all requirements.txt files
    requirements_files = list(repo_root.rglob('requirements.txt'))
    
    # Filter out any in hidden directories or scripts
    requirements_files = [
        f for f in requirements_files 
        if not any(part.startswith('.') for part in f.parts)
        and 'scripts' not in f.parts
    ]
    
    print(f"Found {len(requirements_files)} requirements.txt files")
    
    modified_count = 0
    for req_file in requirements_files:
        if fix_requirements_file(req_file):
            modified_count += 1
            print(f"✓ Fixed: {req_file.relative_to(repo_root)}")
    
    print(f"\n✅ Modified {modified_count} files with security fixes")
    print(f"📌 Pinned versions for {len(SECURITY_PINS)} critical packages")

if __name__ == "__main__":
    main()