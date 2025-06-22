import asyncio
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from models.travel_plan import TravelPlanAgentRequest, TravelPlanResponse
from models.plan_task import TaskStatus
from services.plan_service import generate_travel_plan
from repository.plan_task_repository import create_plan_task, update_task_status
from typing import List

router = APIRouter(prefix="/api/plan", tags=["Travel Plan"])


@router.post(
    "/trigger",
    response_model=TravelPlanResponse,
    summary="Trigger Trip Craft Agent",
    description="Triggers the travel plan agent with the provided travel details",
)
async def trigger_trip_craft_agent(
    request: TravelPlanAgentRequest,
) -> TravelPlanResponse:
    """
    Trigger the trip craft agent to create a personalized travel itinerary.

    Args:
        request: Travel plan request containing trip details and plan ID

    Returns:
        TravelPlanResponse: Success status and trip plan ID
    """
    try:
        logger.info(f"Triggering travel plan agent for trip ID: {request.trip_plan_id}")
        logger.info(f"Travel plan details: {request.travel_plan}")

        # Create initial task
        task = await create_plan_task(
            trip_plan_id=request.trip_plan_id,
            task_type="travel_plan_generation",
            input_data=request.travel_plan.model_dump(),
        )

        logger.info(f"Task created: {task.id}")

        # Create background task for plan generation
        async def generate_plan_with_tracking():
            try:
                # Update task status to in progress when service starts
                await update_task_status(task.id, TaskStatus.in_progress)
                logger.info(f"Task updated to in progress: {task.id}")

                result = await generate_travel_plan(request)

                # Update task with success status and output
                await update_task_status(
                    task.id, TaskStatus.success, output_data={"travel_plan": result}
                )
                logger.info(f"Task updated to success: {task.id}")
            except Exception as e:
                logger.error(f"Error generating travel plan: {str(e)}")
                # Update task with error status
                await update_task_status(
                    task.id, TaskStatus.error, error_message=str(e)
                )
                logger.info(f"Task updated to error: {task.id}")
                raise

        asyncio.create_task(generate_plan_with_tracking())

        logger.info(
            f"Travel plan agent triggered successfully for trip ID: {request.trip_plan_id}"
        )

        return TravelPlanResponse(
            success=True,
            message="Travel plan agent triggered successfully",
            trip_plan_id=request.trip_plan_id,
        )

    except Exception as e:
        logger.error(f"Error triggering travel plan agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger travel plan agent: {str(e)}",
        )
