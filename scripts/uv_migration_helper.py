#!/usr/bin/env python3
"""
UV Migration Helper Script

Automates the process of migrating Python projects from pip/requirements.txt to UV.
Creates pyproject.toml, generates uv.lock, and maintains backward compatibility.

Usage:
    python uv_migration_helper.py <project_directory>
"""

import sys
import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json


class UVMigrationHelper:
    """Automates UV migration for Python projects."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.requirements_file = self.project_path / "requirements.txt"
        self.pyproject_file = self.project_path / "pyproject.toml"
        self.uv_lock_file = self.project_path / "uv.lock"
        self.readme_file = self._find_readme()
        
    def _find_readme(self) -> Optional[Path]:
        """Find README file in various formats."""
        for name in ["README.md", "README.rst", "README.txt", "readme.md"]:
            readme_path = self.project_path / name
            if readme_path.exists():
                return readme_path
        return None
        
    def parse_requirements(self) -> List[str]:
        """Parse requirements.txt and extract dependencies."""
        if not self.requirements_file.exists():
            raise FileNotFoundError(f"No requirements.txt found in {self.project_path}")
            
        dependencies = []
        with open(self.requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Handle special cases like -e, git+, etc.
                if line.startswith('-') or line.startswith('git+'):
                    print(f"Warning: Skipping unsupported requirement: {line}")
                    continue
                dependencies.append(line)
                
        return dependencies
        
    def extract_project_name(self) -> str:
        """Extract project name from directory or existing metadata."""
        # Check if pyproject.toml already exists
        if self.pyproject_file.exists():
            try:
                with open(self.pyproject_file, 'r') as f:
                    content = f.read()
                    # Simple regex to extract project name
                    match = re.search(r'name\s*=\s*"([^"]+)"', content)
                    if match:
                        return match.group(1)
            except Exception:
                pass
                    
        # Use directory name as fallback
        return self.project_path.name.replace('_', '-').lower()
        
    def create_pyproject_toml(self, dependencies: List[str]) -> str:
        """Create or update pyproject.toml configuration."""
        project_name = self.extract_project_name()
        
        # Format dependencies for TOML
        formatted_deps = []
        for dep in dependencies:
            # Ensure proper quoting
            if '=' in dep and not any(op in dep for op in ['>=', '<=', '==', '!=', '~=']):
                formatted_deps.append(f'    "{dep}",')
            else:
                formatted_deps.append(f'    "{dep}",')
        
        deps_str = '\n'.join(formatted_deps)
        
        # Create TOML content
        toml_content = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "{project_name} - Migrated to UV"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
{deps_str}
]
"""
        
        return toml_content
        
    def write_pyproject_toml(self, toml_content: str) -> None:
        """Write pyproject.toml file."""
        # Create backup if file exists
        if self.pyproject_file.exists():
            backup_path = self.pyproject_file.with_suffix('.toml.backup')
            shutil.copy2(self.pyproject_file, backup_path)
            print(f"Created backup: {backup_path}")
            
        with open(self.pyproject_file, 'w') as f:
            f.write(toml_content)
            
        print(f"Created/Updated: {self.pyproject_file}")
        
    def generate_uv_lock(self) -> bool:
        """Generate uv.lock file using UV."""
        try:
            # Check if UV is installed
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: UV is not installed. Please install UV first:")
            print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
            
        print("Generating uv.lock file...")
        try:
            # Run uv sync to generate lock file
            result = subprocess.run(
                ["uv", "sync"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("Successfully generated uv.lock")
                return True
            else:
                print(f"Error generating uv.lock: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error running UV: {e}")
            return False
            
    def update_requirements_txt(self) -> None:
        """Update requirements.txt to be UV-generated."""
        if not self.uv_lock_file.exists():
            print("Warning: uv.lock not found, skipping requirements.txt update")
            return
            
        # Backup existing requirements.txt
        backup_path = self.requirements_file.with_suffix('.txt.backup')
        shutil.copy2(self.requirements_file, backup_path)
        print(f"Created backup: {backup_path}")
        
        # Generate new requirements.txt from UV
        try:
            result = subprocess.run(
                ["uv", "pip", "compile", "pyproject.toml", "-o", "requirements.txt"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("Updated requirements.txt from UV")
            else:
                print(f"Warning: Could not update requirements.txt: {result.stderr}")
                
        except Exception as e:
            print(f"Warning: Error updating requirements.txt: {e}")
            
    def add_uv_instructions_to_readme(self) -> None:
        """Add UV installation instructions to README."""
        if not self.readme_file:
            print("No README found, skipping documentation update")
            return
            
        with open(self.readme_file, 'r') as f:
            content = f.read()
            
        # Check if UV instructions already exist
        if 'uv' in content.lower() and ('uv sync' in content or 'uv install' in content):
            print("UV instructions already present in README")
            return
            
        # Find installation section
        installation_patterns = [
            r'#{1,3}\s*Installation',
            r'#{1,3}\s*Setup',
            r'#{1,3}\s*Getting Started',
            r'#{1,3}\s*How to Run'
        ]
        
        insert_position = None
        for pattern in installation_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Find the next section or end of file
                next_section = re.search(r'\n#{1,3}\s+\w', content[match.end():])
                if next_section:
                    insert_position = match.end() + next_section.start()
                else:
                    insert_position = len(content)
                break
                
        uv_section = """
### Using UV (Recommended)

This project uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management.

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the application**:
   ```bash
   uv run python <main_script.py>
   ```

### Using pip (Traditional)

Alternatively, you can use pip:

```bash
pip install -r requirements.txt
```

"""
        
        if insert_position:
            # Insert UV instructions
            updated_content = (
                content[:insert_position] + 
                uv_section + 
                content[insert_position:]
            )
        else:
            # Append to end of file
            updated_content = content + "\n" + uv_section
            
        # Backup and update README
        backup_path = self.readme_file.with_suffix(self.readme_file.suffix + '.backup')
        shutil.copy2(self.readme_file, backup_path)
        print(f"Created backup: {backup_path}")
        
        with open(self.readme_file, 'w') as f:
            f.write(updated_content)
            
        print(f"Updated README with UV instructions: {self.readme_file}")
        
    def run_migration(self) -> bool:
        """Execute the complete migration process."""
        print(f"\n🚀 Starting UV migration for: {self.project_path}")
        print("=" * 60)
        
        try:
            # Step 1: Parse requirements
            print("\n📋 Step 1: Parsing requirements.txt")
            dependencies = self.parse_requirements()
            print(f"Found {len(dependencies)} dependencies")
            
            # Step 2: Create pyproject.toml
            print("\n📝 Step 2: Creating/updating pyproject.toml")
            toml_content = self.create_pyproject_toml(dependencies)
            self.write_pyproject_toml(toml_content)
            
            # Step 3: Generate uv.lock
            print("\n🔒 Step 3: Generating uv.lock")
            if not self.generate_uv_lock():
                print("Failed to generate uv.lock - migration incomplete")
                return False
                
            # Step 4: Update requirements.txt
            print("\n🔄 Step 4: Updating requirements.txt")
            self.update_requirements_txt()
            
            # Step 5: Update documentation
            print("\n📚 Step 5: Updating documentation")
            self.add_uv_instructions_to_readme()
            
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Review the changes in pyproject.toml")
            print("2. Test the project with: uv run python <your_script.py>")
            print("3. Commit the changes including uv.lock")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python uv_migration_helper.py <project_directory>")
        sys.exit(1)
        
    project_dir = sys.argv[1]
    
    if not os.path.isdir(project_dir):
        print(f"Error: {project_dir} is not a valid directory")
        sys.exit(1)
        
    migrator = UVMigrationHelper(project_dir)
    success = migrator.run_migration()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()