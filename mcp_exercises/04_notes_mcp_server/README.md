# Notes MCP Server

A notes and todo management MCP server with persistent JSON file storage. Demonstrates full CRUD operations through MCP tools.

## Features

**Tools - Notes:**
- `create_note` - Create a new note with title, content, and tags
- `list_notes` - List notes with optional tag/search filtering
- `get_note` - Retrieve full content of a note by ID
- `update_note` - Update title, content, or tags of an existing note
- `delete_note` - Delete a note by ID

**Tools - Todos:**
- `create_todo` - Create a todo with priority (low/medium/high)
- `list_todos` - List todos filtered by completion status and priority
- `complete_todo` - Mark a todo as completed
- `delete_todo` - Delete a todo

**Resources:**
- `notes://all` - Get all notes
- `notes://tags` - Get all unique tags
- `todos://summary` - Todo completion statistics and priority breakdown

**Prompts:**
- `daily_review` - Review pending todos and recent notes
- `brainstorm` - Brainstorm ideas and save them as notes

## Concepts Demonstrated

- Full CRUD operations (Create, Read, Update, Delete)
- Persistent state via JSON file storage
- UUID-based entity identification
- Tag-based organization and filtering
- Multiple entity types (notes + todos) in one server
- Priority-based sorting
- Configurable storage directory via environment variables

## Setup

```bash
pip install -r requirements.txt

# Run with default storage (./notes_data/)
python server.py

# Or set a custom storage directory
NOTES_STORAGE_DIR=/path/to/storage python server.py
```

## Data Storage

Notes and todos are stored as JSON files in the `notes_data/` directory (or the path set in `NOTES_STORAGE_DIR`):

```
notes_data/
├── notes.json
└── todos.json
```

## Example Tool Calls

```
create_note(title="Meeting Notes", content="Discussed Q4 goals.", tags="work, meetings")
list_notes(tag="work")
create_todo(task="Review PR #42", priority="high")
complete_todo(todo_id="a1b2c3d4")
```
