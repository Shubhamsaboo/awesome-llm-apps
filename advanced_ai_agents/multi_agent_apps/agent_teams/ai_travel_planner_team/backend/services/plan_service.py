from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.trip_db import TripPlanStatus, TripPlanOutput
from models.travel_plan import (
    TravelPlanAgentRequest,
    TravelPlanRequest,
    TravelPlanTeamResponse,
)
from loguru import logger
from agents.team import trip_planning_team
import json
import time
from agents.structured_output import convert_to_model
from repository.trip_plan_repository import (
    create_trip_plan_status,
    update_trip_plan_status,
    get_trip_plan_status,
    create_trip_plan_output,
    delete_trip_plan_outputs,
)
from agents.destination import destination_agent
from agents.itinerary import itinerary_agent
from agents.flight import flight_search_agent
from agents.hotel import hotel_search_agent
from agents.food import dining_agent
from agents.budget import budget_agent


def travel_request_to_markdown(data: TravelPlanRequest) -> str:
    # Map of travel vibes to their descriptions
    travel_vibes = {
        "relaxing": "a peaceful retreat focused on wellness, spa experiences, and leisurely activities",
        "adventure": "thrilling experiences including hiking, water sports, and adrenaline activities",
        "romantic": "intimate experiences with private dining, couples activities, and scenic spots",
        "cultural": "immersive experiences with local traditions, museums, and historical sites",
        "food-focused": "culinary experiences including cooking classes, food tours, and local cuisine",
        "nature": "outdoor experiences with national parks, wildlife, and scenic landscapes",
        "photography": "photogenic locations with scenic viewpoints, cultural sites, and natural wonders",
    }

    # Map of travel styles to their descriptions
    travel_styles = {
        "backpacker": "budget-friendly accommodations, local transportation, and authentic experiences",
        "comfort": "mid-range hotels, convenient transportation, and balanced comfort-value ratio",
        "luxury": "premium accommodations, private transfers, and exclusive experiences",
        "eco-conscious": "sustainable accommodations, eco-friendly activities, and responsible tourism",
    }

    # Map of pace levels (0-5) to their descriptions
    pace_levels = {
        0: "1-2 activities per day with plenty of free time and flexibility",
        1: "2-3 activities per day with significant downtime between activities",
        2: "3-4 activities per day with balanced activity and rest periods",
        3: "4-5 activities per day with moderate breaks between activities",
        4: "5-6 activities per day with minimal downtime",
        5: "6+ activities per day with back-to-back scheduling",
    }

    def format_date(date_str: str, is_picker: bool) -> str:
        if not date_str:
            return "Not specified"
        if is_picker:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%B %d, %Y")
            except ValueError:
                return date_str
        return date_str.strip()

    date_type = data.date_input_type
    is_picker = date_type == "picker"
    start_date = format_date(data.travel_dates.start, is_picker)
    end_date = format_date(data.travel_dates.end, is_picker)
    date_range = (
        f"between {start_date} and {end_date}"
        if end_date and end_date != "Not specified"
        else start_date
    )

    vibes = data.vibes
    vibes_descriptions = [travel_vibes.get(v, v) for v in vibes]

    lines = [
        f"# 🧳 Travel Plan Request",
        "",
        "## 📍 Trip Overview",
        f"- **Traveler:** {data.name.title() if data.name else 'Unnamed Traveler'}",
        f"- **Route:** {data.starting_location.title()} → {data.destination.title()}",
        f"- **Duration:** {data.duration} days ({date_range})",
        "",
        "## 👥 Travel Group",
        f"- **Group Size:** {data.adults} adults, {data.children} children",
        f"- **Traveling With:** {data.traveling_with or 'Not specified'}",
        f"- **Age Groups:** {', '.join(data.age_groups) or 'Not specified'}",
        f"- **Rooms Needed:** {data.rooms or 'Not specified'}",
        "",
        "## 💰 Budget & Preferences",
        f"- **Budget per person:** {data.budget} {data.budget_currency} ({'Flexible' if data.budget_flexible else 'Fixed'})",
        f"- **Travel Style:** {travel_styles.get(data.travel_style, data.travel_style or 'Not specified')}",
        f"- **Preferred Pace:** {', '.join([pace_levels.get(p, str(p)) for p in data.pace]) or 'Not specified'}",
        "",
        "## ✨ Trip Preferences",
    ]

    if vibes_descriptions:
        lines.append("- **Travel Vibes:**")
        for vibe in vibes_descriptions:
            lines.append(f"  - {vibe}")
    else:
        lines.append("- **Travel Vibes:** Not specified")

    if data.priorities:
        lines.append(f"- **Top Priorities:** {', '.join(data.priorities)}")
    if data.interests:
        lines.append(f"- **Interests:** {data.interests}")

    lines.extend(
        [
            "",
            "## 🗺️ Destination Context",
            f"- **Previous Visit:** {data.been_there_before.capitalize() if data.been_there_before else 'Not specified'}",
            f"- **Loved Places:** {data.loved_places or 'Not specified'}",
            f"- **Additional Notes:** {data.additional_info or 'Not specified'}",
        ]
    )

    return "\n".join(lines)


async def generate_travel_plan(request: TravelPlanAgentRequest) -> str:
    """Generate a travel plan based on the request and log status/output to database."""
    trip_plan_id = request.trip_plan_id
    logger.info(f"Generating travel plan for tripPlanId: {trip_plan_id}")

    # Get or create status entry using repository functions
    status_entry = await get_trip_plan_status(trip_plan_id)
    if not status_entry:
        status_entry = await create_trip_plan_status(
            trip_plan_id=trip_plan_id, status="pending"
        )

    # Update status to processing
    status_entry = await update_trip_plan_status(
        trip_plan_id=trip_plan_id,
        status="processing",
        current_step="Initializing travel plan generation",
        started_at=datetime.now(timezone.utc),
    )

    try:
        travel_request_md = travel_request_to_markdown(request.travel_plan)
        logger.info(f"Travel request markdown: {travel_request_md}")

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Generating plan with TripCraft AI agents",
        )

        last_response_content = ""
        time_start = time.time()

        # Team Collaboration
        # prompt = f"""
        #     Below is my travel plan request. Please generate a travel plan for the request.
        #     {travel_request_md}
        # """

        # time_start = time.time()
        # ai_response = await trip_planning_team.arun(prompt)
        # time_end = time.time()
        # logger.info(f"AI team processing time: {time_end - time_start:.2f} seconds")

        # last_response_content = ai_response.messages[-1].content
        # logger.info(
        #     f"Last AI Response for conversion: {last_response_content[:500]}..."
        # )

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Researching about the destination",
        )

        # Destination Research
        destionation_research_response = await destination_agent.arun(
            f"""
            Please research about the destination {request.travel_plan.destination}

            Below are user's travel request:
            {travel_request_md}

            Provide a very detailed research about the destination, its attractions, activities, and other relevant information that user might be interested in.

            Give 10 attractions/activities that user might be interested in.
            """
        )

        logger.info(
            f"Destination research response: {destionation_research_response.messages[-1].content}"
        )

        last_response_content = f"""
        ## Destination Attractions:
        ---
        {destionation_research_response.messages[-1].content}
        ---
"""

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Searching for the best flights",
        )
        # Flight Search
        flight_search_response = await flight_search_agent.arun(
            f"""
            Please find flights according to the user's travel request:
            {travel_request_md}

            If user has not specified the exact flight date, please consider it by yourself based on the user's travel request.

            Provide a very detailed research about the flights, its price, duration, and other relevant information that user might be interested in.

            Give top 5 flights.
            """
        )

        logger.info(
            f"Flight search response: {flight_search_response.messages[-1].content}"
        )

        last_response_content += f"""
        ## Flight recommendations:
        ---
        {flight_search_response.messages[-1].content}
        ---
        """

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Searching for the best hotels",
        )
        # Hotel Search
        hotel_search_response = await hotel_search_agent.arun(
            f"""
            Please find hotels according to the user's travel request:
            {travel_request_md}

            If user has not specified the exact hotel dates, please consider it by yourself based on the user's travel request.

            Provide a very detailed research about the hotels, its price, amenities, and other relevant information that user might be interested in.

            Give top 5 hotels.
            """
        )

        last_response_content += f"""
        ## Hotel recommendations:
        ---
        {hotel_search_response.messages[-1].content}
        ---
        """

        logger.info(
            f"Hotel search response: {hotel_search_response.messages[-1].content}"
        )

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Searching for the best restaurants",
        )
        # Restaurant Search
        restaurant_search_response = await dining_agent.arun(
            f"""
            Please find restaurants according to the user's travel request:
            {travel_request_md}

            If user has not specified the exact restaurant dates, please consider it by yourself based on the user's travel request.

            Provide a very detailed research about the restaurants, its price, menu, and other relevant information that user might be interested in.

            Give top 5 restaurants.
            """
        )

        last_response_content += f"""
        ## Restaurant recommendations:
        ---
        {restaurant_search_response.messages[-1].content}
        ---
        """

        logger.info(
            f"Restaurant search response: {restaurant_search_response.messages[-1].content}"
        )

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Creating the day-by-day itinerary",
        )
        # Itinerary
        itinerary_response = await itinerary_agent.arun(
            f"""
            Please create a detailed day-by-day itinerary for a trip to {request.travel_plan.destination}  for user's travel request:
            {travel_request_md}

            Based on the following information:
            {last_response_content}
            """
        )

        logger.info(f"Itinerary response: {itinerary_response.messages[-1].content}")

        last_response_content += f"""
        ## Day-by-day itinerary:
        ---
        {itinerary_response.messages[-1].content}
        ---
        """

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Optimizing the budget",
        )
        # Budget
        budget_response = await budget_agent.arun(
            f"""
            Please optimize the budget according to the user's travel request:
            {travel_request_md}

            Based on the following information:
            {last_response_content}
            """
        )

        logger.info(f"Budget response: {budget_response.messages[-1].content}")

        time_end = time.time()
        logger.info(f"Total time taken: {time_end - time_start:.2f} seconds")

        # Update status for response conversion
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Adding finishing touches",
        )

        json_response_output = await convert_to_model(
            last_response_content, TravelPlanTeamResponse
        )
        logger.info(f"Converted Structured Response: {json_response_output[:500]}...")

        # Delete any existing output entries for this trip plan
        await delete_trip_plan_outputs(trip_plan_id=trip_plan_id)

        final_response = json.dumps(
            {
                "itinerary": json_response_output,
                "budget_agent_response": budget_response.messages[-1].content,
                "destination_agent_response": destionation_research_response.messages[
                    -1
                ].content,
                "flight_agent_response": flight_search_response.messages[-1].content,
                "hotel_agent_response": hotel_search_response.messages[-1].content,
                "restaurant_agent_response": restaurant_search_response.messages[
                    -1
                ].content,
                "itinerary_agent_response": itinerary_response.messages[-1].content,
            },
            indent=2,
        )

        # Create new output entry
        await create_trip_plan_output(
            trip_plan_id=trip_plan_id,
            itinerary=final_response,
            summary="",
        )

        # Update status to completed
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="completed",
            current_step="Plan generated and saved",
            completed_at=datetime.now(timezone.utc),
        )

        return final_response
    except Exception as e:
        logger.error(
            f"Error generating travel plan for {trip_plan_id}: {str(e)}", exc_info=True
        )
        # Update status to failed
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="failed",
            error=str(e),
            completed_at=datetime.now(timezone.utc),
        )
        raise
