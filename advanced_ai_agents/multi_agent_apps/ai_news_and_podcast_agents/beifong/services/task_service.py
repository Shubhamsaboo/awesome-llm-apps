from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
from services.db_service import tasks_db
from models.tasks_schemas import TASK_TYPES


class TaskService:
    """Service for managing scheduled tasks."""

    async def get_tasks(self, include_disabled: bool = False) -> List[Dict[str, Any]]:
        """Get all tasks with optional filtering."""
        try:
            if include_disabled:
                query = """
                SELECT id, name, description, command, task_type, frequency, frequency_unit, 
                       enabled, last_run, created_at
                FROM tasks
                ORDER BY name
                """
                params = ()
            else:
                query = """
                SELECT id, name, description, command, task_type, frequency, frequency_unit, 
                       enabled, last_run, created_at
                FROM tasks
                WHERE enabled = 1
                ORDER BY name
                """
                params = ()
            tasks = await tasks_db.execute_query(query, params, fetch=True)
            for task in tasks:
                task["enabled"] = bool(task.get("enabled", 0))
            return tasks
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

    async def get_task(self, task_id: int) -> Dict[str, Any]:
        """Get a specific task by ID."""
        try:
            query = """
            SELECT id, name, description, command, task_type, frequency, frequency_unit, 
                   enabled, last_run, created_at
            FROM tasks
            WHERE id = ?
            """
            task = await tasks_db.execute_query(query, (task_id,), fetch=True, fetch_one=True)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            task["enabled"] = bool(task.get("enabled", 0))
            return task
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching task: {str(e)}")

    async def check_task_exists(self, task_type: str) -> Optional[Dict[str, Any]]:
        """Check if a task with the given type already exists."""
        try:
            query = """
            SELECT id, name, task_type
            FROM tasks
            WHERE task_type = ?
            LIMIT 1
            """
            task = await tasks_db.execute_query(query, (task_type,), fetch=True, fetch_one=True)
            return task
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error checking task existence: {str(e)}")

    async def create_task(
        self,
        name: str,
        task_type: str,
        frequency: int,
        frequency_unit: str,
        description: Optional[str] = None,
        enabled: bool = True,
    ) -> Dict[str, Any]:
        """Create a new task."""
        try:
            existing_task = await self.check_task_exists(task_type)
            if existing_task:
                raise HTTPException(
                    status_code=409,
                    detail=f"A task with type '{task_type}' already exists (Task: '{existing_task['name']}', ID: {existing_task['id']}). Please edit the existing task instead of creating a duplicate.",
                )
            if task_type not in TASK_TYPES:
                raise HTTPException(
                    status_code=400, detail=f"Invalid task type: '{task_type}'. Please select a valid task type from the available options."
                )
            command = TASK_TYPES[task_type]["command"]
            current_time = datetime.now().isoformat()
            query = """
            INSERT INTO tasks 
            (name, description, command, task_type, frequency, frequency_unit, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                name,
                description,
                command,
                task_type,
                frequency,
                frequency_unit,
                1 if enabled else 0,
                current_time,
            )
            task_id = await tasks_db.execute_query(query, params)
            return await self.get_task(task_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

    async def update_task(self, task_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        try:
            current_task = await self.get_task(task_id)
            if "task_type" in updates and updates["task_type"] != current_task["task_type"]:
                existing_task = await self.check_task_exists(updates["task_type"])
                if existing_task and existing_task["id"] != task_id:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A task with type '{updates['task_type']}' already exists (Task: '{existing_task['name']}', ID: {existing_task['id']}). You cannot have duplicate task types in the system.",
                    )
                if updates["task_type"] in TASK_TYPES:
                    updates["command"] = TASK_TYPES[updates["task_type"]]["command"]
            allowed_fields = [
                "name",
                "description",
                "command",
                "task_type",
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
                return await self.get_task(task_id)
            params.append(task_id)
            update_query = f"""
            UPDATE tasks
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """
            await tasks_db.execute_query(update_query, tuple(params))
            return await self.get_task(task_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

    async def delete_task(self, task_id: int) -> Dict[str, str]:
        """Delete a task."""
        try:
            task = await self.get_task(task_id)
            query = """
            DELETE FROM tasks
            WHERE id = ?
            """
            await tasks_db.execute_query(query, (task_id,))
            return {"message": f"Task '{task['name']}' has been deleted"}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

    async def toggle_task(self, task_id: int, enable: bool) -> Dict[str, Any]:
        """Enable or disable a task."""
        try:
            query = """
            UPDATE tasks
            SET enabled = ?
            WHERE id = ?
            """
            await tasks_db.execute_query(query, (1 if enable else 0, task_id))
            return await self.get_task(task_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

    async def get_task_executions(self, task_id: Optional[int] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get paginated task executions."""
        try:
            offset = (page - 1) * per_page
            if task_id:
                count_query = """
                SELECT COUNT(*) as count
                FROM task_executions
                WHERE task_id = ?
                """
                count_params = (task_id,)
                query = """
                SELECT id, task_id, start_time, end_time, status, error_message, output
                FROM task_executions
                WHERE task_id = ?
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
                """
                params = (task_id, per_page, offset)
            else:
                count_query = """
                SELECT COUNT(*) as count
                FROM task_executions
                """
                count_params = ()
                query = """
                SELECT id, task_id, start_time, end_time, status, error_message, output
                FROM task_executions
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
                """
                params = (per_page, offset)
            count_result = await tasks_db.execute_query(count_query, count_params, fetch=True, fetch_one=True)
            total_items = count_result.get("count", 0) if count_result else 0
            executions = await tasks_db.execute_query(query, params, fetch=True)
            for execution in executions:
                if execution.get("task_id"):
                    try:
                        task = await self.get_task(execution["task_id"])
                        execution["task_name"] = task.get("name", "Unknown Task")
                    except Exception as _:
                        execution["task_name"] = "Unknown Task"
            total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return {
                "items": executions,
                "total": total_items,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching task executions: {str(e)}")

    async def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are due to run."""
        try:
            query = """
            SELECT id, name, description, command, task_type, frequency, frequency_unit, enabled, last_run
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
            tasks = await tasks_db.execute_query(query, fetch=True)
            for task in tasks:
                task["enabled"] = bool(task.get("enabled", 0))
            return tasks
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching pending tasks: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        try:
            task_query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as active_tasks,
                SUM(CASE WHEN enabled = 0 THEN 1 ELSE 0 END) as disabled_tasks,
                SUM(CASE WHEN last_run IS NULL THEN 1 ELSE 0 END) as never_run_tasks
            FROM tasks
            """
            task_stats = await tasks_db.execute_query(task_query, fetch=True, fetch_one=True)
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            exec_query = """
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
            exec_stats = await tasks_db.execute_query(exec_query, (cutoff_date,), fetch=True, fetch_one=True)
            return {"tasks": task_stats or {}, "executions": exec_stats or {}}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching task statistics: {str(e)}")


task_service = TaskService()
