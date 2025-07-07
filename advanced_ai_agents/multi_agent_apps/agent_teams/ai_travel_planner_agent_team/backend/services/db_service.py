"""
Database service module for PostgreSQL connections using SQLAlchemy.

This module provides utilities for connecting to a PostgreSQL database
with SQLAlchemy, including connection pooling, session management,
and context managers for proper resource management.
"""

import os
from typing import Any, AsyncGenerator, Dict, Optional
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from loguru import logger

# Database connection string from environment variable
# Convert psycopg to SQLAlchemy format if needed
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    # Convert to asyncpg format for SQLAlchemy async
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

async def initialize_db_pool(pool_size: int = 10, max_overflow: int = 20) -> None:
    """Initialize the SQLAlchemy engine and session factory.

    Args:
        pool_size: Pool size for the connection pool
        max_overflow: Maximum number of connections that can be created beyond the pool size
    """
    global _engine, _session_factory
    if _engine is not None:
        return

    logger.info("Initializing SQLAlchemy engine and session factory")

    try:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,  # Set to True for SQL query logging
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using them
        )

        _session_factory = async_sessionmaker(
            _engine,
            expire_on_commit=False,
            autoflush=False,
        )

        # Test the connection
        async with _session_factory() as session:
            await session.execute(text("SELECT 1"))

        logger.info("SQLAlchemy engine and session factory initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SQLAlchemy engine and session factory: {e}")
        raise

async def close_db_pool() -> None:
    """Close the SQLAlchemy engine and connection pool."""
    global _engine
    if _engine is not None:
        logger.info("Closing SQLAlchemy engine and connection pool")
        await _engine.dispose()
        _engine = None

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a SQLAlchemy session for database operations.

    Returns:
        AsyncSession: SQLAlchemy async session

    Example:
        ```python
        async with get_db_session() as session:
            result = await session.execute(text("SELECT * FROM users"))
            users = result.fetchall()
        ```
    """
    if _session_factory is None:
        await initialize_db_pool()

    async with _session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session operation failed: {e}")
            raise

async def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> list:
    """Execute a database query and return results.

    Args:
        query: SQL query to execute (raw SQL)
        params: Query parameters (for parameterized queries)

    Returns:
        list: Query results

    Example:
        ```python
        results = await execute_query(
            "SELECT * FROM users WHERE email = :email",
            {"email": "user@example.com"}
        )
        ```
    """
    async with get_db_session() as session:
        try:
            result = await session.execute(text(query), params or {})
            try:
                return result.fetchall()
            except Exception:
                # No results to fetch
                return []
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise