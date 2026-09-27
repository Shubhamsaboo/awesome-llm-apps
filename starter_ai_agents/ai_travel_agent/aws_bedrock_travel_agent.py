import os
import json
import re
from datetime import datetime, timedelta
from textwrap import dedent

import boto3
import streamlit as st
from agno.agent import Agent
from agno.models.aws import AwsBedrock
from agno.run.agent import RunOutput
from agno.run.base import RunStatus
from agno.tools.serpapi import SerpApiTools
from dotenv import load_dotenv
from icalendar import Calendar, Event
from pydantic import BaseModel, Field

load_dotenv()


class ItineraryActivity(BaseModel):
    time: str = Field(description="Suggested time of day, or 'Unscheduled' if unknown")
    name: str
    description: str
    location: str = ""
    source_url: str = ""


class ItineraryDay(BaseModel):
    day_number: int
    title: str
    activities: list[ItineraryActivity] = Field(default_factory=list)
    dining: list[ItineraryActivity] = Field(default_factory=list)
    accommodation: str = ""
    notes: str = ""


class TravelItinerary(BaseModel):
    destination: str
    duration_days: int
    overview: str
    days: list[ItineraryDay]


def parse_itinerary(content: object) -> TravelItinerary:
    if isinstance(content, TravelItinerary):
        return content
    if isinstance(content, str):
        # Bedrock models return JSON as text; strip Markdown code fences if present.
        match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
        return TravelItinerary.model_validate_json(match.group(1) if match else content)
    return TravelItinerary.model_validate(content)


def generate_ics_content(itinerary: TravelItinerary, start_date: datetime = None) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//AI Travel Planner//github.com//")
    calendar.add("version", "2.0")

    if start_date is None:
        start_date = datetime.today()

    for day in itinerary.days:
        event_date = start_date + timedelta(days=day.day_number - 1)
        description_lines = [day.notes] if day.notes else []
        for activity in day.activities:
            description_lines.append(f"{activity.time}: {activity.name} - {activity.description}")
            if activity.location:
                description_lines.append(f"Location: {activity.location}")
            if activity.source_url:
                description_lines.append(f"Source: {activity.source_url}")
        for dining in day.dining:
            description_lines.append(f"Dining: {dining.name} - {dining.description}")
            if dining.location:
                description_lines.append(f"Location: {dining.location}")
            if dining.source_url:
                description_lines.append(f"Source: {dining.source_url}")
        if day.accommodation:
            description_lines.append(f"Accommodation: {day.accommodation}")

        event = Event()
        event.add("summary", f"Day {day.day_number}: {day.title}")
        event.add("description", "\n".join(description_lines))
        event.add("dtstart", event_date.date())
        event.add("dtend", (event_date + timedelta(days=1)).date())
        event.add("dtstamp", datetime.now())
        calendar.add_component(event)

    return calendar.to_ical()


def build_result_json(itinerary: TravelItinerary, research_text: str, model_id: str, region: str, generated_at: str) -> dict:
    return {
        "metadata": {
            "destination": itinerary.destination,
            "duration_days": itinerary.duration_days,
            "provider": "aws-bedrock",
            "model_id": model_id,
            "aws_region": region,
            "generated_at": generated_at,
        },
        "itinerary": itinerary.model_dump(mode="json"),
        "research_results": research_text,
    }


def render_itinerary(itinerary: TravelItinerary) -> None:
    st.subheader(f"{itinerary.destination} - {itinerary.duration_days} days")
    st.write(itinerary.overview)
    for day in itinerary.days:
        with st.expander(f"Day {day.day_number}: {day.title}", expanded=day.day_number == 1):
            for activity in day.activities:
                line = f"**{activity.time}** - {activity.name}: {activity.description}"
                if activity.location:
                    line += f" _({activity.location})_"
                if activity.source_url:
                    line += f" [source]({activity.source_url})"
                st.markdown(f"- {line}")
            if day.dining:
                st.markdown("**Dining**")
                for dining in day.dining:
                    line = f"{dining.name}: {dining.description}"
                    if dining.source_url:
                        line += f" [source]({dining.source_url})"
                    st.markdown(f"- {line}")
            if day.accommodation:
                st.markdown(f"**Accommodation:** {day.accommodation}")
            if day.notes:
                st.caption(day.notes)


st.title("AI Travel Planner with AWS Bedrock")
st.caption("Research a destination and create a personalized itinerary using models on Amazon Bedrock.")

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "result_json" not in st.session_state:
    st.session_state.result_json = None

bedrock_api_key = st.text_input(
    "Bedrock API key (short-term)",
    type="password",
    value=os.getenv("AWS_BEARER_TOKEN_BEDROCK", ""),
    help="Generate a short-term API key in the Amazon Bedrock console. It expires after a few hours.",
)
aws_region = st.text_input(
    "AWS region",
    value=os.getenv("AWS_REGION", "us-east-1"),
    help="Must be the same region the short-term key was generated in.",
)
bedrock_model_id = st.text_input(
    "Bedrock model ID",
    value=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-5"),
    help="Copy the model ID (or inference profile ID) enabled for your account from the Bedrock console.",
)
serp_api_key = st.text_input(
    "SerpAPI key for travel research",
    type="password",
    value=os.getenv("SERPAPI_API_KEY", ""),
)

if not bedrock_api_key or not aws_region or not bedrock_model_id or not serp_api_key:
    st.info(
        "Set AWS_BEARER_TOKEN_BEDROCK, AWS_REGION, BEDROCK_MODEL_ID and SERPAPI_API_KEY "
        "in your local .env file, or enter them above."
    )
else:
    # boto3 picks up Bedrock API keys from this environment variable (boto3 >= 1.39).
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bedrock_api_key
    aws_session = boto3.Session(region_name=aws_region)

    researcher = Agent(
        name="Researcher",
        role="Searches for travel destinations, activities, and accommodations based on user preferences",
        model=AwsBedrock(id=bedrock_model_id, session=aws_session, aws_region=aws_region),
        description=dedent(
            """\
            You are a world-class travel researcher. Given a travel destination and trip duration,
            generate search terms, search the web, and return the 10 most relevant results.
            """
        ),
        instructions=[
            "Generate 3 search terms related to the destination and trip duration.",
            "Search each term and analyze the results.",
            "Return the 10 most relevant results for the user's preferences.",
            "Prioritize accurate, useful information.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )
    planner = Agent(
        name="Planner",
        role="Creates a draft itinerary from the user's preferences and research results",
        model=AwsBedrock(id=bedrock_model_id, session=aws_session, aws_region=aws_region),
        description=dedent(
            """\
            You are a senior travel planner. Create a detailed, practical itinerary from the
            destination, trip duration, and supplied research results.
            """
        ),
        instructions=[
            "Return an itinerary matching the supplied structured output schema.",
            "Include exactly one day entry for each requested trip day, numbered from 1.",
            "Include suggested activities, dining, and accommodation details when supported by research.",
            "Copy source URLs only from the supplied research results; leave source_url empty otherwise.",
            "Do not invent facts; ground recommendations in the research results.",
        ],
        output_schema=TravelItinerary,
        add_datetime_to_context=True,
    )

    destination = st.text_input("Where do you want to go?")
    num_days = st.number_input("How many days do you want to travel for?", min_value=1, max_value=30, value=7)
    generate_column, ics_download_column, json_download_column = st.columns(3)

    with generate_column:
        if st.button("Generate Itinerary"):
            if not destination.strip():
                st.warning("Enter a destination to continue.")
            else:
                research_prompt = f"Research {destination} for a {num_days} day trip"
                try:
                    with st.spinner("Researching your destination..."):
                        research_results: RunOutput = researcher.run(research_prompt, stream=False)
                    # agno reports model errors in the run status instead of raising.
                    if research_results.status == RunStatus.error:
                        raise RuntimeError(research_results.content)
                except Exception as error:
                    st.error(f"The research stage failed: {error}")
                else:
                    research_text = str(research_results.content or "")
                    prompt = f"""
                    Destination: {destination}
                    Duration: {num_days} days
                    Research Results: {research_text}

                        Create a detailed itinerary with exactly {num_days} days.
                        Return structured data matching the required itinerary schema.
                    """
                    try:
                        with st.spinner("Creating your personalized itinerary..."):
                            response: RunOutput = planner.run(prompt, stream=False)
                            if response.status == RunStatus.error:
                                raise RuntimeError(response.content)
                            itinerary = parse_itinerary(response.content)
                            st.session_state.itinerary = itinerary
                            st.session_state.result_json = build_result_json(
                                itinerary,
                                research_text,
                                bedrock_model_id,
                                aws_region,
                                datetime.now().isoformat(timespec="seconds"),
                            )
                    except Exception as error:
                        st.error(f"The planning stage failed: {error}")

    with ics_download_column:
        if st.session_state.itinerary:
            st.download_button(
                label="Download Itinerary as Calendar (.ics)",
                data=generate_ics_content(st.session_state.itinerary),
                file_name="travel_itinerary.ics",
                mime="text/calendar",
            )

    with json_download_column:
        if st.session_state.result_json:
            st.download_button(
                label="Download Result (.json)",
                data=json.dumps(st.session_state.result_json, indent=2, ensure_ascii=False),
                file_name="travel_itinerary.json",
                mime="application/json",
            )

    if st.session_state.itinerary and st.session_state.result_json:
        itinerary_tab, json_tab = st.tabs(["Itinerary", "JSON Result"])
        with itinerary_tab:
            render_itinerary(st.session_state.itinerary)
        with json_tab:
            st.json(st.session_state.result_json)
