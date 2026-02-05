"""
File Search MCP Server
======================
An MCP server for searching and reading files on the local filesystem.
Demonstrates: tools with file I/O, resources for directory listings,
prompts for code analysis, and path safety validation.

The server restricts access to a configurable base directory for safety.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("File Search MCP Server")

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

# Base directory for file operations (defaults to current working directory).
# Set the MCP_BASE_DIR environment variable to override.
BASE_DIR = Path(os.environ.get("MCP_BASE_DIR", os.getcwd())).resolve()


def safe_path(user_path: str) -> Path | None:
    """Resolve a user-provided path and verify it is within BASE_DIR."""
    try:
        resolved = (BASE_DIR / user_path).resolve()
        if str(resolved).startswith(str(BASE_DIR)):
            return resolved
    except (ValueError, OSError):
        pass
    return None


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable units."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ──────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────


@mcp.tool()
def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a glob pattern within the base directory.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "**/*.md", "src/**/*.js")
        directory: Subdirectory to search in, relative to base (default: root)
    """
    search_dir = safe_path(directory)
    if not search_dir or not search_dir.is_dir():
        return json.dumps({"error": f"Directory '{directory}' not found or not accessible."})

    matches = []
    for path in sorted(search_dir.glob(pattern)):
        if path.is_file():
            rel_path = str(path.relative_to(BASE_DIR))
            stat = path.stat()
            matches.append(
                {
                    "path": rel_path,
                    "size": format_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        if len(matches) >= 50:
            break

    return json.dumps(
        {"base_directory": str(BASE_DIR), "pattern": pattern, "match_count": len(matches), "files": matches},
        indent=2,
    )


@mcp.tool()
def read_file(path: str, max_lines: int = 200) -> str:
    """Read the contents of a file.

    Args:
        path: File path relative to the base directory
        max_lines: Maximum number of lines to read (default: 200, max: 1000)
    """
    file_path = safe_path(path)
    if not file_path or not file_path.is_file():
        return json.dumps({"error": f"File '{path}' not found or not accessible."})

    max_lines = min(max_lines, 1000)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... (truncated at {max_lines} lines)")
                    break
                lines.append(line)

        content = "".join(lines)
        return json.dumps(
            {
                "path": path,
                "total_lines": len(lines),
                "content": content,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Could not read file: {e}"})


@mcp.tool()
def search_in_files(query: str, pattern: str = "**/*", directory: str = ".") -> str:
    """Search for text content within files (grep-like).

    Args:
        query: Text string to search for (case-insensitive)
        pattern: Glob pattern to filter which files to search (default: all files)
        directory: Subdirectory to search in, relative to base (default: root)
    """
    search_dir = safe_path(directory)
    if not search_dir or not search_dir.is_dir():
        return json.dumps({"error": f"Directory '{directory}' not found or not accessible."})

    query_lower = query.lower()
    results = []

    for file_path in sorted(search_dir.glob(pattern)):
        if not file_path.is_file():
            continue
        # Skip binary files
        try:
            with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                for line_num, line in enumerate(f, 1):
                    if query_lower in line.lower():
                        results.append(
                            {
                                "file": str(file_path.relative_to(BASE_DIR)),
                                "line": line_num,
                                "content": line.rstrip()[:200],
                            }
                        )
                    if len(results) >= 30:
                        break
        except (UnicodeDecodeError, PermissionError):
            continue

        if len(results) >= 30:
            break

    return json.dumps(
        {"query": query, "match_count": len(results), "results": results},
        indent=2,
    )


@mcp.tool()
def get_file_info(path: str) -> str:
    """Get detailed metadata about a file or directory.

    Args:
        path: File or directory path relative to the base directory
    """
    target = safe_path(path)
    if not target or not target.exists():
        return json.dumps({"error": f"Path '{path}' not found or not accessible."})

    stat = target.stat()
    info = {
        "path": path,
        "type": "directory" if target.is_dir() else "file",
        "size": format_size(stat.st_size),
        "size_bytes": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }

    if target.is_file():
        info["extension"] = target.suffix
        try:
            with open(target, "r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
            info["line_count"] = line_count
        except (UnicodeDecodeError, PermissionError):
            info["line_count"] = "N/A (binary file)"

    if target.is_dir():
        children = list(target.iterdir())
        info["child_count"] = len(children)
        info["subdirectories"] = sorted(
            [c.name for c in children if c.is_dir()]
        )[:20]
        info["files"] = sorted([c.name for c in children if c.is_file()])[:20]

    return json.dumps(info, indent=2)


@mcp.tool()
def list_directory(path: str = ".", show_hidden: bool = False) -> str:
    """List contents of a directory.

    Args:
        path: Directory path relative to the base directory (default: root)
        show_hidden: Whether to include hidden files/directories (default: false)
    """
    dir_path = safe_path(path)
    if not dir_path or not dir_path.is_dir():
        return json.dumps({"error": f"Directory '{path}' not found or not accessible."})

    entries = []
    for item in sorted(dir_path.iterdir()):
        if not show_hidden and item.name.startswith("."):
            continue
        stat = item.stat()
        entries.append(
            {
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": format_size(stat.st_size) if item.is_file() else "-",
            }
        )

    return json.dumps(
        {
            "directory": path,
            "base_directory": str(BASE_DIR),
            "entry_count": len(entries),
            "entries": entries,
        },
        indent=2,
    )


# ──────────────────────────────────────────────
# Resources
# ──────────────────────────────────────────────


@mcp.resource("filesystem://info")
def filesystem_info() -> str:
    """Get information about the configured base directory."""
    return json.dumps(
        {
            "base_directory": str(BASE_DIR),
            "exists": BASE_DIR.exists(),
            "is_directory": BASE_DIR.is_dir(),
        },
        indent=2,
    )


# ──────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────


@mcp.prompt()
def analyze_codebase(language: str = "python") -> str:
    """Generate a prompt to analyze the codebase structure."""
    ext_map = {
        "python": "*.py",
        "javascript": "*.js",
        "typescript": "*.ts",
        "rust": "*.rs",
        "go": "*.go",
    }
    ext = ext_map.get(language.lower(), f"*.{language}")
    return f"""Please analyze this codebase:
1. First, search for all {language} files using pattern "{ext}"
2. List the directory structure
3. Read the key files (like main entry points, configuration)
4. Provide a summary of:
   - Project structure and organization
   - Key files and their purposes
   - Technologies and patterns used"""


@mcp.prompt()
def find_in_project(search_term: str) -> str:
    """Generate a prompt to find a term across the project."""
    return f"""Search the project for "{search_term}":
1. Search in all files for this term
2. Read the relevant matching files for context
3. Summarize where and how "{search_term}" is used in the project."""


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
