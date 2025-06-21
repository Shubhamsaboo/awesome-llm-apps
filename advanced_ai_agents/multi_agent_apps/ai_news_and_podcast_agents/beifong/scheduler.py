import os
import time
import signal
import subprocess
from datetime import datetime
import traceback
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from db.config import get_tasks_db_path
from db.connection import db_connection
from db.tasks import (
    get_pending_tasks,
    update_task_last_run,
    update_task_execution,
)

running = True
MAX_WORKERS = 5
DEFAULT_TASK_TIMEOUT = 3600


def cleanup_stuck_tasks():
    tasks_db_path = get_tasks_db_path()
    try:
        with db_connection(tasks_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM task_executions 
                WHERE status = 'running'
                LIMIT 100
                """
            )
            running_executions = [dict(row) for row in cursor.fetchall()]
            if running_executions:
                print(f"WARNING: Found {len(running_executions)} tasks stuck in 'running' state. Marking as failed.")
                for execution in running_executions:
                    execution_id = execution["id"]
                    error_message = "Task was interrupted by system shutdown or crash"
                    cursor.execute(
                        """
                        UPDATE task_executions
                        SET end_time = ?, status = ?, error_message = ?
                        WHERE id = ?
                        """,
                        (datetime.now().isoformat(), "failed", error_message, execution_id),
                    )
                    print(f"INFO: Marked execution {execution_id} as failed")
                conn.commit()
            else:
                print("INFO: No stuck tasks found")
    except Exception as e:
        print(f"ERROR: Error cleaning up stuck tasks: {str(e)}")
        print(f"ERROR: {traceback.format_exc()}")


def execute_task(task_id, command):
    tasks_db_path = get_tasks_db_path()
    with db_connection(tasks_db_path) as conn:
        conn.execute("BEGIN EXCLUSIVE TRANSACTION")
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM task_executions 
                WHERE task_id = ? AND status = 'running'
                LIMIT 1
                """,
                (task_id,),
            )
            is_running = cursor.fetchone() is not None
            if is_running:
                print(f"WARNING: Task {task_id} is already running, skipping this execution")
                conn.commit()
                return
            cursor.execute(
                """
                INSERT INTO task_executions 
                (task_id, start_time, status)
                VALUES (?, ?, ?)
                """,
                (task_id, datetime.now().isoformat(), "running"),
            )
            execution_id = cursor.lastrowid
            conn.commit()
            if not execution_id:
                print(f"ERROR: Failed to create execution record for task {task_id}")
                return
        except Exception as e:
            conn.rollback()
            print(f"ERROR: Transaction error for task {task_id}: {str(e)}")
            return
    print(f"INFO: Starting task {task_id}: {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=DEFAULT_TASK_TIMEOUT)
            if process.returncode == 0:
                status = "success"
                error_message = None
                print(f"INFO: Task {task_id} completed successfully")
            else:
                status = "failed"
                error_message = stderr if stderr else f"Process exited with code {process.returncode}"
                print(f"ERROR: Task {task_id} failed: {error_message}")
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            status = "failed"
            error_message = f"Task timed out after {DEFAULT_TASK_TIMEOUT} seconds"
            print(f"ERROR: Task {task_id} timed out")
        output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}" if stderr else stdout
        update_task_execution(tasks_db_path, execution_id, status, error_message, output)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        update_task_last_run(tasks_db_path, task_id, timestamp)
    except Exception as e:
        print(f"ERROR: Error executing task {task_id}: {str(e)}")
        error_message = traceback.format_exc()
        update_task_execution(tasks_db_path, execution_id, "failed", error_message)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        update_task_last_run(tasks_db_path, task_id, timestamp)


def check_for_tasks():
    tasks_db_path = get_tasks_db_path()
    try:
        print("DEBUG: Checking for pending tasks...")
        pending_tasks = get_pending_tasks(tasks_db_path)
        if not pending_tasks:
            print("DEBUG: No pending tasks found")
            return
        print(f"INFO: Found {len(pending_tasks)} pending tasks")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for task in pending_tasks:
                task_id = task["id"]
                command = task["command"]
                print(f"INFO: Scheduling task {task_id}: {task['name']} (Last run: {task['last_run']})")
                executor.submit(execute_task, task_id, command)
    except Exception as e:
        print(f"ERROR: Error in check_for_tasks: {str(e)}")
        print(f"ERROR: {traceback.format_exc()}")


def check_missed_tasks():
    tasks_db_path = get_tasks_db_path()
    try:
        print("INFO: Checking for missed tasks during downtime...")
        pending_tasks = get_pending_tasks(tasks_db_path)
        if pending_tasks:
            print(f"INFO: Found {len(pending_tasks)} tasks to run (including any missed during downtime)")
        else:
            print("INFO: No missed tasks found")
    except Exception as e:
        print(f"ERROR: Error checking for missed tasks: {str(e)}")


def signal_handler(sig, frame):
    global running
    print("INFO: Shutdown signal received, stopping scheduler...")
    running = False


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("INFO: Starting task scheduler")
    tasks_db_path = get_tasks_db_path()
    cleanup_stuck_tasks()
    scheduler_dir = os.path.dirname(tasks_db_path)
    os.makedirs(scheduler_dir, exist_ok=True)
    scheduler_db_path = os.path.join(scheduler_dir, "scheduler.sqlite")
    jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{scheduler_db_path}")}
    scheduler = BackgroundScheduler(jobstores=jobstores, daemon=True)
    scheduler.add_job(
        check_for_tasks,
        IntervalTrigger(minutes=1),
        id="check_tasks",
        name="Check for pending tasks",
        replace_existing=True,
    )
    scheduler.start()
    print("INFO: Scheduler started, checking for tasks every minute")
    check_for_tasks()
    check_missed_tasks()
    try:
        while running:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("INFO: Scheduler interrupted")
    finally:
        scheduler.shutdown()
        print("INFO: Scheduler shutdown complete")


if __name__ == "__main__":
    main()
