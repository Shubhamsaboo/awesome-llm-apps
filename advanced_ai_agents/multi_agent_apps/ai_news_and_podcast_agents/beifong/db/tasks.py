from datetime import datetime, timedelta
from .connection import execute_query, db_connection


def create_task(
    tasks_db_path,
    name,
    command,
    frequency,
    frequency_unit,
    description=None,
    enabled=True,
):
    query = """
    INSERT INTO tasks 
    (name, description, command, frequency, frequency_unit, enabled, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        name,
        description,
        command,
        frequency,
        frequency_unit,
        1 if enabled else 0,
        datetime.now().isoformat(),
    )
    return execute_query(tasks_db_path, query, params)


def is_task_running(tasks_db_path, task_id):
    query = """
    SELECT 1 
    FROM task_executions 
    WHERE task_id = ? AND status = 'running'
    LIMIT 1
    """
    try:
        result = execute_query(tasks_db_path, query, (task_id,), fetch=True, fetch_one=True)
        return result is not None  # True if a running entry exists
    except Exception as e:
        print(f"Database error checking running status for task {task_id}: {e}")
        return True


def get_task(tasks_db_path, task_id):
    query = """
    SELECT id, name, description, command, frequency, frequency_unit, enabled, last_run, created_at
    FROM tasks
    WHERE id = ?
    """
    return execute_query(tasks_db_path, query, (task_id,), fetch=True, fetch_one=True)


def get_all_tasks(tasks_db_path, include_disabled=False):
    if include_disabled:
        query = """
        SELECT id, name, description, command, frequency, frequency_unit, enabled, last_run, created_at
        FROM tasks
        ORDER BY name
        """
        return execute_query(tasks_db_path, query, fetch=True)
    else:
        query = """
        SELECT id, name, description, command, frequency, frequency_unit, enabled, last_run, created_at
        FROM tasks
        WHERE enabled = 1
        ORDER BY name
        """
        return execute_query(tasks_db_path, query, fetch=True)


def update_task(tasks_db_path, task_id, updates):
    allowed_fields = [
        "name",
        "description",
        "command",
        "frequency",
        "frequency_unit",
        "enabled",
    ]

    set_clauses = []
    params = []
    for field, value in updates.items():
        if field in allowed_fields:
            if field == "enabled":
                value = 1 if value else 0
            set_clauses.append(f"{field} = ?")
            params.append(value)
    if not set_clauses:
        return 0
    query = f"""
    UPDATE tasks
    SET {", ".join(set_clauses)}
    WHERE id = ?
    """
    params.append(task_id)
    return execute_query(tasks_db_path, query, tuple(params))


def delete_task(tasks_db_path, task_id):
    query = """
    DELETE FROM tasks
    WHERE id = ?
    """
    return execute_query(tasks_db_path, query, (task_id,))


def update_task_last_run(tasks_db_path, task_id, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    query = """
    UPDATE tasks
    SET last_run = ?
    WHERE id = ?
    """
    return execute_query(tasks_db_path, query, (timestamp, task_id))


def create_task_execution(tasks_db_path, task_id, status, error_message=None, output=None):
    start_time = datetime.now().isoformat()
    query = """
    INSERT INTO task_executions 
    (task_id, start_time, status, error_message, output)
    VALUES (?, ?, ?, ?, ?)
    """
    params = (task_id, start_time, status, error_message, output)
    execute_query(tasks_db_path, query, params)
    try:
        with db_connection(tasks_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid  # Return the ID of the inserted row
    except Exception as e:
        print(f"Database error in create_task_execution: {e}")
        return None  #


def update_task_execution(tasks_db_path, execution_id, status, error_message=None, output=None):
    end_time = datetime.now().isoformat()
    query = """
    UPDATE task_executions
    SET end_time = ?, status = ?, error_message = ?, output = ?
    WHERE id = ?
    """
    params = (end_time, status, error_message, output, execution_id)
    return execute_query(tasks_db_path, query, params)


def get_recent_task_executions(tasks_db_path, task_id=None, limit=10):
    if task_id:
        query = """
        SELECT id, task_id, start_time, end_time, status, error_message, output
        FROM task_executions
        WHERE task_id = ?
        ORDER BY start_time DESC
        LIMIT ?
        """
        params = (task_id, limit)
    else:
        query = """
        SELECT id, task_id, start_time, end_time, status, error_message, output
        FROM task_executions
        ORDER BY start_time DESC
        LIMIT ?
        """
        params = (limit,)
    return execute_query(tasks_db_path, query, params, fetch=True)


def get_task_execution(tasks_db_path, execution_id):
    query = """
    SELECT id, task_id, start_time, end_time, status, error_message, output
    FROM task_executions
    WHERE id = ?
    """
    return execute_query(tasks_db_path, query, (execution_id,), fetch=True, fetch_one=True)


def mark_task_disabled(tasks_db_path, task_id):
    query = """
    UPDATE tasks
    SET enabled = 0
    WHERE id = ?
    """
    return execute_query(tasks_db_path, query, (task_id,))


def mark_task_enabled(tasks_db_path, task_id):
    query = """
    UPDATE tasks
    SET enabled = 1
    WHERE id = ?
    """
    return execute_query(tasks_db_path, query, (task_id,))


def get_task_stats(tasks_db_path):
    query = """
    SELECT 
        COUNT(*) as total_tasks,
        SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as active_tasks,
        SUM(CASE WHEN enabled = 0 THEN 1 ELSE 0 END) as disabled_tasks,
        SUM(CASE WHEN last_run IS NULL THEN 1 ELSE 0 END) as never_run_tasks
    FROM tasks
    """
    return execute_query(tasks_db_path, query, fetch=True, fetch_one=True)


def get_execution_stats(tasks_db_path, days=7):
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    query = """
    SELECT 
        COUNT(*) as total_executions,
        COALESCE(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END), 0) as successful_executions,
        COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed_executions,
        COALESCE(SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END), 0) as running_executions,
        COALESCE(AVG(CASE WHEN end_time IS NOT NULL 
            THEN (julianday(end_time) - julianday(start_time)) * 86400.0 
            ELSE NULL END), 0) as avg_execution_time_seconds
    FROM task_executions
    WHERE start_time >= ?
    """
    return execute_query(tasks_db_path, query, (cutoff_date,), fetch=True, fetch_one=True)


def get_pending_tasks(tasks_db_path):
    query = """
    SELECT id, name, description, command, frequency, frequency_unit, enabled, last_run
    FROM tasks
    WHERE enabled = 1
    AND (
        last_run IS NULL 
        OR 
        CASE frequency_unit
            WHEN 'minutes' THEN datetime(last_run, '+' || frequency || ' minutes') <= datetime('now', 'localtime')
            WHEN 'hours' THEN datetime(last_run, '+' || frequency || ' hours') <= datetime('now', 'localtime')
            WHEN 'days' THEN datetime(last_run, '+' || frequency || ' days') <= datetime('now', 'localtime')
            ELSE datetime(last_run, '+' || frequency || ' seconds') <= datetime('now', 'localtime')
        END
    )
    ORDER BY last_run
    """
    tasks = execute_query(tasks_db_path, query, fetch=True)
    return tasks
