from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TaskStatus(str, Enum):
    queued = "queued"
    in_progress = "in_progress"
    success = "success"
    error = "error"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive enum values."""
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return None


class Base(DeclarativeBase):
    pass


class PlanTask(Base):
    """Model for tracking plan tasks and their states."""

    __tablename__ = "plan_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_plan_id: Mapped[str] = mapped_column(String(50), index=True)
    task_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="plan_task_status")
    )
    input_data: Mapped[dict] = mapped_column(JSON)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
