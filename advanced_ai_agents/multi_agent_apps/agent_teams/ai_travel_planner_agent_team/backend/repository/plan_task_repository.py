from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.plan_task import PlanTask, TaskStatus
from services.db_service import get_db_session


async def create_plan_task(
    trip_plan_id: str,
    task_type: str,
    input_data: dict,
    status: TaskStatus = TaskStatus.queued,
) -> PlanTask:
    """Create a new plan task."""
    async with get_db_session() as session:
        task = PlanTask(
            trip_plan_id=trip_plan_id,
            task_type=task_type,
            status=status,
            input_data=input_data,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def update_task_status(
    task_id: int,
    status: TaskStatus,
    output_data: Optional[dict] = None,
    error_message: Optional[str] = None,
) -> Optional[PlanTask]:
    """Update the status and output of a plan task."""
    async with get_db_session() as session:
        result = await session.execute(select(PlanTask).where(PlanTask.id == task_id))
        task = result.scalar_one_or_none()

        if task:
            task.status = status
            if output_data is not None:
                task.output_data = output_data
            if error_message is not None:
                task.error_message = error_message
            task.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(task)
        return task


async def get_task_by_id(task_id: int) -> Optional[PlanTask]:
    """Get a plan task by its ID."""
    async with get_db_session() as session:
        result = await session.execute(select(PlanTask).where(PlanTask.id == task_id))
        return result.scalar_one_or_none()


async def get_tasks_by_trip_plan(trip_plan_id: str) -> List[PlanTask]:
    """Get all tasks for a specific trip plan."""
    async with get_db_session() as session:
        result = await session.execute(
            select(PlanTask).where(PlanTask.trip_plan_id == trip_plan_id)
        )
        return list(result.scalars().all())


async def get_tasks_by_status(status: TaskStatus) -> List[PlanTask]:
    """Get all tasks with a specific status."""
    async with get_db_session() as session:
        result = await session.execute(
            select(PlanTask).where(PlanTask.status == status)
        )
        return list(result.scalars().all())
