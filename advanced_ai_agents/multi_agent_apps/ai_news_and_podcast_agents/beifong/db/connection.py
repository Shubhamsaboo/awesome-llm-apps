import sqlite3
from contextlib import contextmanager


@contextmanager
def db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_query(db_path, query, params=(), fetch=False, fetch_one=False):
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetch_one:
            result = cursor.fetchone()
            return dict(result) if result else None
        elif fetch:
            return [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            return cursor.lastrowid
