"""Pytest configuration ensuring verified_agent_memory modules are on sys.path."""

from pathlib import Path
import sys

# Add parent directory of tests (verified_agent_memory) to sys.path
package_dir = Path(__file__).resolve().parent.parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))
