import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "saas_accounts.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('Enterprise', 'Free', 'Startup', 'Scale')),
    owner TEXT NOT NULL,
    csm TEXT,
    status TEXT CHECK(status IN ('Active', 'Churned', 'Trial', 'Suspended')) DEFAULT 'Active',
    mrr REAL DEFAULT 0,
    created_at TEXT DEFAULT (date('now')),
    salesforce_id TEXT
);

CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    metric TEXT NOT NULL,
    period TEXT NOT NULL,
    value REAL NOT NULL,
    recorded_at TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    amount REAL NOT NULL,
    status TEXT CHECK(status IN ('Paid', 'Overdue', 'Draft', 'Void')) DEFAULT 'Draft',
    due_date TEXT,
    paid_at TEXT
);
"""

ALLOWED_WRITE_STATEMENTS = {"UPDATE", "INSERT"}
BLOCKED_STATEMENTS = {"DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"}


def get_read_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def get_write_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_write_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def get_schema_context() -> str:
    conn = get_read_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    schema_parts = []
    for table in tables:
        name = table["name"]
        cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
        fks = conn.execute(f"PRAGMA foreign_key_list({name})").fetchall()

        col_descs = []
        for c in cols:
            desc = f"  {c['name']} {c['type']}"
            if c["pk"]:
                desc += " PRIMARY KEY"
            if c["notnull"]:
                desc += " NOT NULL"
            if c["dflt_value"]:
                desc += f" DEFAULT {c['dflt_value']}"
            col_descs.append(desc)

        fk_descs = [f"  FOREIGN KEY ({fk['from']}) REFERENCES {fk['table']}({fk['to']})" for fk in fks]

        check_constraints = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        check_info = ""
        if check_constraints and check_constraints["sql"]:
            sql = check_constraints["sql"]
            import re
            checks = re.findall(r"CHECK\(([^)]+)\)", sql)
            if checks:
                check_info = "\n  CHECK constraints: " + "; ".join(checks)

        row_count = conn.execute(f"SELECT COUNT(*) as cnt FROM {name}").fetchone()["cnt"]

        schema_parts.append(
            f"TABLE {name} ({row_count} rows):\n"
            + "\n".join(col_descs)
            + ("\n" + "\n".join(fk_descs) if fk_descs else "")
            + check_info
        )

    conn.close()
    return "\n\n".join(schema_parts)


def validate_write_sql(sql: str) -> str | None:
    normalized = sql.strip().upper()
    first_word = normalized.split()[0] if normalized.split() else ""

    if first_word in BLOCKED_STATEMENTS:
        return f"Statement type '{first_word}' is not allowed. Only UPDATE and INSERT are permitted."

    if first_word not in ALLOWED_WRITE_STATEMENTS:
        return f"Statement type '{first_word}' is not recognized as a safe write operation."

    if first_word == "UPDATE" and "WHERE" not in normalized:
        return "UPDATE without WHERE clause is not allowed. Must target a specific row by primary key."

    return None


def execute_read(sql: str, params: list | None = None) -> tuple[list[str], list[dict]]:
    conn = get_read_connection()
    try:
        if not sql.strip().upper().startswith("SELECT"):
            raise ValueError("Read connection only accepts SELECT statements.")

        limited_sql = sql.rstrip(";").strip()
        if "LIMIT" not in limited_sql.upper():
            limited_sql += " LIMIT 100"

        cursor = conn.execute(limited_sql, params or [])
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(row) for row in cursor.fetchall()]
        return columns, rows
    finally:
        conn.close()


def execute_write(sql: str, params: list) -> dict:
    error = validate_write_sql(sql)
    if error:
        raise ValueError(error)

    conn = get_write_connection()
    try:
        conn.execute("BEGIN")
        cursor = conn.execute(sql, params)
        conn.commit()
        return {"rows_affected": cursor.rowcount}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_row_by_pk(table: str, pk_value: int) -> dict | None:
    allowed_tables = {"accounts", "usage", "invoices"}
    if table not in allowed_tables:
        raise ValueError(f"Table '{table}' is not allowed.")

    conn = get_read_connection()
    try:
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (pk_value,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
