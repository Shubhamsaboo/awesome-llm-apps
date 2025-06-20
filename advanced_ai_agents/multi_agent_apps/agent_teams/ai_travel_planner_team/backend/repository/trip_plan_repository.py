from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.trip_db import TripPlanStatus, TripPlanOutput
from services.db_service import get_db_session


async def create_trip_plan_status(
    trip_plan_id: str, status: str = "pending", current_step: Optional[str] = None
) -> TripPlanStatus:
    """Create a new trip plan status entry."""
    async with get_db_session() as session:
        status_entry = TripPlanStatus(
            tripPlanId=trip_plan_id,
            status=status,
            currentStep=current_step,
            createdAt=datetime.now().replace(tzinfo=None),
            updatedAt=datetime.now().replace(tzinfo=None),
        )
        session.add(status_entry)
        await session.commit()
        await session.refresh(status_entry)
        return status_entry


async def get_trip_plan_status(trip_plan_id: str) -> Optional[TripPlanStatus]:
    """Get the status entry for a trip plan."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanStatus).where(TripPlanStatus.tripPlanId == trip_plan_id)
        )
        return result.scalar_one_or_none()


async def update_trip_plan_status(
    trip_plan_id: str,
    status: str,
    current_step: Optional[str] = None,
    error: Optional[str] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
) -> Optional[TripPlanStatus]:
    """Update the status of a trip plan."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanStatus).where(TripPlanStatus.tripPlanId == trip_plan_id)
        )
        status_entry = result.scalar_one_or_none()

        if status_entry:
            status_entry.status = status
            if current_step is not None:
                status_entry.currentStep = current_step
            if error is not None:
                status_entry.error = error
            if started_at is not None:
                status_entry.startedAt = started_at.replace(tzinfo=None)
            if completed_at is not None:
                status_entry.completedAt = completed_at.replace(tzinfo=None)
            status_entry.updatedAt = datetime.now(timezone.utc).replace(tzinfo=None)

            await session.commit()
            await session.refresh(status_entry)
        return status_entry


async def create_trip_plan_output(
    trip_plan_id: str, itinerary: str, summary: Optional[str] = None
) -> TripPlanOutput:
    """Create a new trip plan output entry."""
    async with get_db_session() as session:
        output_entry = TripPlanOutput(
            tripPlanId=trip_plan_id,
            itinerary=itinerary,
            summary=summary,
            createdAt=datetime.now(timezone.utc).replace(tzinfo=None),
            updatedAt=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(output_entry)
        await session.commit()
        await session.refresh(output_entry)
        return output_entry


async def get_trip_plan_output(trip_plan_id: str) -> Optional[TripPlanOutput]:
    """Get the output entry for a trip plan."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanOutput).where(TripPlanOutput.tripPlanId == trip_plan_id)
        )
        return result.scalar_one_or_none()


async def update_trip_plan_output(
    trip_plan_id: str, itinerary: Optional[str] = None, summary: Optional[str] = None
) -> Optional[TripPlanOutput]:
    """Update the output of a trip plan."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanOutput).where(TripPlanOutput.tripPlanId == trip_plan_id)
        )
        output_entry = result.scalar_one_or_none()

        if output_entry:
            if itinerary is not None:
                output_entry.itinerary = itinerary
            if summary is not None:
                output_entry.summary = summary
            output_entry.updatedAt = datetime.now(timezone.utc).replace(tzinfo=None)

            await session.commit()
            await session.refresh(output_entry)
        return output_entry


async def get_all_pending_trip_plans() -> List[TripPlanStatus]:
    """Get all trip plans with pending status."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanStatus).where(TripPlanStatus.status == "pending")
        )
        return list(result.scalars().all())


async def get_all_processing_trip_plans() -> List[TripPlanStatus]:
    """Get all trip plans with processing status."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanStatus).where(TripPlanStatus.status == "processing")
        )
        return list(result.scalars().all())


async def get_trip_plans_by_status(status: str) -> List[TripPlanStatus]:
    """Get all trip plans with a specific status."""
    async with get_db_session() as session:
        result = await session.execute(
            select(TripPlanStatus).where(TripPlanStatus.status == status)
        )
        return list(result.scalars().all())


async def delete_trip_plan_outputs(trip_plan_id: str) -> None:
    """Delete all output entries for a given trip plan ID."""
    async with get_db_session() as session:
        await session.execute(
            delete(TripPlanOutput).where(TripPlanOutput.tripPlanId == trip_plan_id)
        )
        await session.commit()
