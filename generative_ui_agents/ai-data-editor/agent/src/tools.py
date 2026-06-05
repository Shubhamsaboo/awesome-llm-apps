import json
import uuid
from typing import Any

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command

from .db import execute_read, execute_write, get_row_by_pk, validate_write_sql


@tool
def query_database(query: str, runtime: ToolRuntime) -> Command:
    """Execute a SQL SELECT query against the database and return results.

    Args:
        query: The SQL SELECT statement to execute.
    """
    query = query.strip().rstrip(";")

    if not query.upper().startswith("SELECT"):
        return Command(update={
            "query_result": {
                "sql": query,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "result_type": "table",
            },
            "messages": [ToolMessage(
                content="Error: Only SELECT statements are allowed for reads.",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    try:
        columns, rows = execute_read(query)
    except Exception as e:
        return Command(update={
            "query_result": {
                "sql": query,
                "columns": [],
                "rows": [{"error": str(e)}],
                "row_count": 0,
                "result_type": "table",
            },
            "messages": [ToolMessage(
                content=f"Query error: {e}",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    if len(rows) == 1 and len(columns) <= 3:
        result_type = "aggregate" if all(isinstance(v, (int, float)) for v in rows[0].values()) else "single_row"
    elif len(rows) == 1:
        result_type = "single_row"
    else:
        result_type = "table"

    summary = f"Query returned {len(rows)} row(s) with columns: {', '.join(columns)}"

    return Command(update={
        "query_result": {
            "sql": query,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "result_type": result_type,
        },
        "messages": [ToolMessage(
            content=summary,
            tool_call_id=runtime.tool_call_id,
        )],
    })


@tool
def propose_mutation(table: str, row_id: int, changes: str, sql: str, params: str, runtime: ToolRuntime) -> Command:
    """Propose a data mutation for human approval. Does NOT execute.

    Args:
        table: The table to modify (accounts, usage, or invoices).
        row_id: The primary key of the row to modify.
        changes: JSON string of changes: [{"column": "...", "old_value": ..., "new_value": ...}]
        sql: The parameterized SQL statement (use ? placeholders).
        params: JSON string of parameter values for the SQL statement.
    """
    error = validate_write_sql(sql)
    if error:
        return Command(update={
            "pending_mutation": None,
            "messages": [ToolMessage(
                content=f"Validation error: {error}",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    try:
        parsed_changes = json.loads(changes)
        parsed_params = json.loads(params)
    except json.JSONDecodeError as e:
        return Command(update={
            "pending_mutation": None,
            "messages": [ToolMessage(
                content=f"Invalid JSON: {e}",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    current_row = get_row_by_pk(table, row_id)
    if current_row is None:
        return Command(update={
            "pending_mutation": None,
            "messages": [ToolMessage(
                content=f"Row {row_id} not found in {table}",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    for change in parsed_changes:
        col = change["column"]
        if col in current_row:
            change["old_value"] = current_row[col]

    mutation_id = str(uuid.uuid4())[:8]
    description_parts = [f"{c['column']}: {c['old_value']} → {c['new_value']}" for c in parsed_changes]
    description = f"Update {table} row {row_id}: " + ", ".join(description_parts)

    return Command(update={
        "pending_mutation": {
            "mutation_id": mutation_id,
            "sql": sql,
            "params": parsed_params,
            "table": table,
            "row_id": row_id,
            "changes": parsed_changes,
            "description": description,
        },
        "messages": [ToolMessage(
            content=f"Mutation proposed ({mutation_id}): {description}. Awaiting user confirmation.",
            tool_call_id=runtime.tool_call_id,
        )],
    })


@tool
def execute_mutation(mutation_id: str, runtime: ToolRuntime) -> Command:
    """Execute a previously proposed and user-approved mutation.

    Only call this AFTER the user has explicitly confirmed the mutation.

    Args:
        mutation_id: The ID of the mutation to execute (from propose_mutation).
    """
    pending = runtime.state.get("pending_mutation")

    if not pending or pending.get("mutation_id") != mutation_id:
        return Command(update={
            "pending_mutation": None,
            "messages": [ToolMessage(
                content=f"Mutation {mutation_id} not found or already executed.",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    try:
        result = execute_write(pending["sql"], pending["params"])
    except Exception as e:
        return Command(update={
            "pending_mutation": None,
            "messages": [ToolMessage(
                content=f"Write failed: {e}",
                tool_call_id=runtime.tool_call_id,
            )],
        })

    updated_row = get_row_by_pk(pending["table"], pending["row_id"])
    columns = list(updated_row.keys()) if updated_row else []
    rows = [updated_row] if updated_row else []

    return Command(update={
        "pending_mutation": None,
        "query_result": {
            "sql": pending["sql"],
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "result_type": "single_row",
        },
        "messages": [ToolMessage(
            content=f"Mutation {mutation_id} executed successfully. {result.get('rows_affected', 0)} row(s) affected.",
            tool_call_id=runtime.tool_call_id,
        )],
    })
