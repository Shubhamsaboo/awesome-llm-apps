"""
Notes MCP Server
================
A notes and todo management MCP server with persistent JSON storage.
Demonstrates: full CRUD operations, persistent state via file storage,
dynamic resources, and multiple tool categories.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Notes MCP Server")

# ──────────────────────────────────────────────
# Storage
# ──────────────────────────────────────────────

STORAGE_DIR = Path(os.environ.get("NOTES_STORAGE_DIR", "./notes_data"))
NOTES_FILE = STORAGE_DIR / "notes.json"
TODOS_FILE = STORAGE_DIR / "todos.json"


def ensure_storage():
    """Create storage directory and files if they don't exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text("[]")
    if not TODOS_FILE.exists():
        TODOS_FILE.write_text("[]")


def load_notes() -> list[dict]:
    """Load notes from JSON file."""
    ensure_storage()
    return json.loads(NOTES_FILE.read_text())


def save_notes(notes: list[dict]) -> None:
    """Save notes to JSON file."""
    ensure_storage()
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


def load_todos() -> list[dict]:
    """Load todos from JSON file."""
    ensure_storage()
    return json.loads(TODOS_FILE.read_text())


def save_todos(todos: list[dict]) -> None:
    """Save todos to JSON file."""
    ensure_storage()
    TODOS_FILE.write_text(json.dumps(todos, indent=2))


# ──────────────────────────────────────────────
# Note Tools
# ──────────────────────────────────────────────


@mcp.tool()
def create_note(title: str, content: str, tags: str = "") -> str:
    """Create a new note.

    Args:
        title: Title of the note
        content: Body content of the note
        tags: Comma-separated tags (e.g., "work, ideas, urgent")
    """
    notes = load_notes()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    note = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "content": content,
        "tags": tag_list,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    notes.append(note)
    save_notes(notes)

    return json.dumps({"message": f"Note '{title}' created.", "note": note}, indent=2)


@mcp.tool()
def list_notes(tag: str = "", search: str = "") -> str:
    """List all notes, optionally filtered by tag or search query.

    Args:
        tag: Filter by tag name (optional)
        search: Search in title and content (optional, case-insensitive)
    """
    notes = load_notes()

    if tag:
        notes = [n for n in notes if tag.lower() in [t.lower() for t in n.get("tags", [])]]
    if search:
        search_lower = search.lower()
        notes = [
            n
            for n in notes
            if search_lower in n["title"].lower() or search_lower in n["content"].lower()
        ]

    summaries = [
        {
            "id": n["id"],
            "title": n["title"],
            "tags": n.get("tags", []),
            "created_at": n["created_at"],
            "preview": n["content"][:100] + ("..." if len(n["content"]) > 100 else ""),
        }
        for n in notes
    ]

    return json.dumps({"count": len(summaries), "notes": summaries}, indent=2)


@mcp.tool()
def get_note(note_id: str) -> str:
    """Get the full content of a note by its ID.

    Args:
        note_id: The ID of the note to retrieve
    """
    notes = load_notes()
    note = next((n for n in notes if n["id"] == note_id), None)
    if not note:
        return json.dumps({"error": f"Note with ID '{note_id}' not found."})
    return json.dumps(note, indent=2)


@mcp.tool()
def update_note(note_id: str, title: str = "", content: str = "", tags: str = "") -> str:
    """Update an existing note. Only provided fields will be updated.

    Args:
        note_id: The ID of the note to update
        title: New title (leave empty to keep current)
        content: New content (leave empty to keep current)
        tags: New comma-separated tags (leave empty to keep current)
    """
    notes = load_notes()
    note = next((n for n in notes if n["id"] == note_id), None)
    if not note:
        return json.dumps({"error": f"Note with ID '{note_id}' not found."})

    if title:
        note["title"] = title
    if content:
        note["content"] = content
    if tags:
        note["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    note["updated_at"] = datetime.now().isoformat()

    save_notes(notes)
    return json.dumps({"message": "Note updated.", "note": note}, indent=2)


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Delete a note by its ID.

    Args:
        note_id: The ID of the note to delete
    """
    notes = load_notes()
    original_count = len(notes)
    notes = [n for n in notes if n["id"] != note_id]

    if len(notes) == original_count:
        return json.dumps({"error": f"Note with ID '{note_id}' not found."})

    save_notes(notes)
    return json.dumps({"message": f"Note '{note_id}' deleted."})


# ──────────────────────────────────────────────
# Todo Tools
# ──────────────────────────────────────────────


@mcp.tool()
def create_todo(task: str, priority: str = "medium") -> str:
    """Create a new todo item.

    Args:
        task: Description of the task
        priority: Priority level - "low", "medium", or "high" (default: medium)
    """
    if priority.lower() not in ("low", "medium", "high"):
        return json.dumps({"error": "Priority must be 'low', 'medium', or 'high'."})

    todos = load_todos()
    todo = {
        "id": str(uuid.uuid4())[:8],
        "task": task,
        "priority": priority.lower(),
        "completed": False,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }

    todos.append(todo)
    save_todos(todos)
    return json.dumps({"message": "Todo created.", "todo": todo}, indent=2)


@mcp.tool()
def list_todos(show_completed: bool = False, priority: str = "") -> str:
    """List todo items.

    Args:
        show_completed: Whether to include completed todos (default: false)
        priority: Filter by priority - "low", "medium", or "high" (optional)
    """
    todos = load_todos()

    if not show_completed:
        todos = [t for t in todos if not t["completed"]]
    if priority:
        todos = [t for t in todos if t["priority"] == priority.lower()]

    # Sort: high priority first, then medium, then low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    todos.sort(key=lambda t: priority_order.get(t["priority"], 1))

    return json.dumps({"count": len(todos), "todos": todos}, indent=2)


@mcp.tool()
def complete_todo(todo_id: str) -> str:
    """Mark a todo item as completed.

    Args:
        todo_id: The ID of the todo to complete
    """
    todos = load_todos()
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return json.dumps({"error": f"Todo with ID '{todo_id}' not found."})

    todo["completed"] = True
    todo["completed_at"] = datetime.now().isoformat()
    save_todos(todos)
    return json.dumps({"message": f"Todo '{todo_id}' marked as completed.", "todo": todo}, indent=2)


@mcp.tool()
def delete_todo(todo_id: str) -> str:
    """Delete a todo item.

    Args:
        todo_id: The ID of the todo to delete
    """
    todos = load_todos()
    original_count = len(todos)
    todos = [t for t in todos if t["id"] != todo_id]

    if len(todos) == original_count:
        return json.dumps({"error": f"Todo with ID '{todo_id}' not found."})

    save_todos(todos)
    return json.dumps({"message": f"Todo '{todo_id}' deleted."})


# ──────────────────────────────────────────────
# Resources
# ──────────────────────────────────────────────


@mcp.resource("notes://all")
def all_notes() -> str:
    """Get all notes."""
    notes = load_notes()
    return json.dumps({"count": len(notes), "notes": notes}, indent=2)


@mcp.resource("notes://tags")
def all_tags() -> str:
    """Get all unique tags used across notes."""
    notes = load_notes()
    tags = set()
    for note in notes:
        tags.update(note.get("tags", []))
    return json.dumps({"tags": sorted(tags)})


@mcp.resource("todos://summary")
def todo_summary() -> str:
    """Get a summary of todo status."""
    todos = load_todos()
    completed = sum(1 for t in todos if t["completed"])
    pending = len(todos) - completed
    by_priority = {}
    for t in todos:
        if not t["completed"]:
            p = t["priority"]
            by_priority[p] = by_priority.get(p, 0) + 1

    return json.dumps(
        {
            "total": len(todos),
            "completed": completed,
            "pending": pending,
            "pending_by_priority": by_priority,
        },
        indent=2,
    )


# ──────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────


@mcp.prompt()
def daily_review() -> str:
    """Generate a prompt for daily review of notes and todos."""
    return """Please help me with my daily review:
1. List all pending todos sorted by priority
2. List any notes created or updated today
3. Suggest which high-priority tasks I should focus on
4. Identify any tasks that might be overdue or stale"""


@mcp.prompt()
def brainstorm(topic: str) -> str:
    """Generate a brainstorming prompt that saves ideas as notes."""
    return f"""Let's brainstorm about: {topic}

Please:
1. Generate 5 creative ideas related to this topic
2. Save each idea as a separate note with the tag "brainstorm"
3. Create a todo item for the most actionable idea
4. Summarize all the ideas at the end"""


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
