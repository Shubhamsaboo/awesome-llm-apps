from fastapi import APIRouter, Query, Path, Body, status
from typing import List, Optional, Dict
from models.tasks_schemas import Task, TaskCreate, TaskUpdate, TaskStats, TASK_TYPES
from services.task_service import task_service

router = APIRouter()


@router.get("/", response_model=List[Task])
async def get_tasks(
    include_disabled: bool = Query(False, description="Include disabled tasks"),
):
    """
    Get all tasks with optional filtering.

    - **include_disabled**: If true, includes disabled tasks
    """
    return await task_service.get_tasks(include_disabled=include_disabled)


@router.get("/pending", response_model=List[Task])
async def get_pending_tasks():
    """
    Get tasks that are due to run.
    """
    return await task_service.get_pending_tasks()


@router.get("/stats", response_model=TaskStats)
async def get_task_stats():
    """
    Get task statistics.
    """
    return await task_service.get_stats()


@router.get("/executions")
async def get_task_executions(
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """
    Get paginated task executions.

    - **task_id**: Filter by task ID
    - **page**: Page number (starting from 1)
    - **per_page**: Number of items per page (max 100)
    """
    return await task_service.get_task_executions(task_id=task_id, page=page, per_page=per_page)


@router.get("/types", response_model=Dict[str, Dict[str, str]])
async def get_task_types():
    """
    Get all available task types.
    """
    return TASK_TYPES


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int = Path(..., description="The ID of the task to retrieve"),
):
    """
    Get a specific task by ID.

    - **task_id**: The ID of the task to retrieve
    """
    return await task_service.get_task(task_id=task_id)


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate = Body(...)):
    """
    Create a new task.

    - **task_data**: Data for the new task
    """
    return await task_service.create_task(
        name=task_data.name,
        task_type=task_data.task_type,
        frequency=task_data.frequency,
        frequency_unit=task_data.frequency_unit,
        description=task_data.description,
        enabled=task_data.enabled,
    )


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int = Path(..., description="The ID of the task to update"),
    task_data: TaskUpdate = Body(...),
):
    """
    Update an existing task.

    - **task_id**: The ID of the task to update
    - **task_data**: Updated data for the task
    """
    updates = {k: v for k, v in task_data.dict().items() if v is not None}
    return await task_service.update_task(task_id=task_id, updates=updates)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete"),
):
    """
    Delete a task.

    - **task_id**: The ID of the task to delete
    """
    return await task_service.delete_task(task_id=task_id)


@router.post("/{task_id}/enable", response_model=Task)
async def enable_task(
    task_id: int = Path(..., description="The ID of the task to enable"),
):
    """
    Enable a task.

    - **task_id**: The ID of the task to enable
    """
    return await task_service.toggle_task(task_id=task_id, enable=True)


@router.post("/{task_id}/disable", response_model=Task)
async def disable_task(
    task_id: int = Path(..., description="The ID of the task to disable"),
):
    """
    Disable a task.

    - **task_id**: The ID of the task to disable
    """
    return await task_service.toggle_task(task_id=task_id, enable=False)
