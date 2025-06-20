from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from services.db_service import initialize_db_pool, close_db_pool
from router.plan import router as plan_router

router = APIRouter(prefix="/api")


@router.get("/health", summary="API Health Check")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("API server started")

    # Initialize database connection pool
    logger.info("Initializing database connection pool")
    await initialize_db_pool()
    logger.info("Database connection pool initialized")

    yield

    # Shutdown logic
    # Close database connection pool
    logger.info("Closing database connection pool")
    await close_db_pool()

    logger.info("API server shutting down")


app = FastAPI(
    title="TripCraft AI API",
    description="API for running intelligent trip planning in the background",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)
app.include_router(plan_router)
