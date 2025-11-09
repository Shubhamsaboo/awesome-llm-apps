# Import the required libraries
import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.team import Team
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from textwrap import dedent

# Set up the Streamlit app
st.title("AI Movie Production Agent 🎬")
st.caption("Bring your movie ideas to life with the teams of script writing and casting AI agents")

# Get Google API key from user
google_api_key = st.text_input("Enter Google API Key to access Gemini 2.5 Flash", type="password")
# Get SerpAPI key from the user
serp_api_key = st.text_input("Enter Serp API Key for Search functionality", type="password")

if google_api_key and serp_api_key:
    script_writer = Agent(
        name="ScriptWriter",
        model=Gemini(id="gemini-2.5-flash", api_key=google_api_key),
        description=dedent(
            """\
        You are an expert screenplay writer. Given a movie idea and genre, 
        develop a compelling script outline with character descriptions and key plot points.
        """
        ),
        instructions=[
            "Write a script outline with 3-5 main characters and key plot points.",
            "Outline the three-act structure and suggest 2-3 twists.",
            "Ensure the script aligns with the specified genre and target audience.",
        ],
    )

    casting_director = Agent(
        name="CastingDirector",
        model=Gemini(id="gemini-2.5-flash", api_key=google_api_key),
        description=dedent(
            """\
        You are a talented casting director. Given a script outline and character descriptions,
        suggest suitable actors for the main roles, considering their past performances and current availability.
        """
        ),
        instructions=[
            "Suggest 2-3 actors for each main role.",
            "Check actors' current status using `search_google`.",
            "Provide a brief explanation for each casting suggestion.",
            "Consider diversity and representation in your casting choices.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
    )

    movie_producer = Team(
        name="MovieProducer",
        model=Gemini(id="gemini-2.5-flash", api_key=google_api_key),
        members=[script_writer, casting_director],
        description="Experienced movie producer overseeing script and casting.",
        instructions=[
            "Ask ScriptWriter for a script outline based on the movie idea.",
            "Pass the outline to CastingDirector for casting suggestions.",
            "Summarize the script outline and casting suggestions.",
            "Provide a concise movie concept overview.",
        ],
        markdown=True,
    )

    # Input field for the report query
    movie_idea = st.text_area("Describe your movie idea in a few sentences:")
    genre = st.selectbox("Select the movie genre:", 
                         ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Romance", "Thriller"])
    target_audience = st.selectbox("Select the target audience:", 
                                   ["General", "Children", "Teenagers", "Adults", "Mature"])
    estimated_runtime = st.slider("Estimated runtime (in minutes):", 60, 180, 120)

    # Process the movie concept
    if st.button("Develop Movie Concept"):
        with st.spinner("Developing movie concept..."):
            input_text = (
                f"Movie idea: {movie_idea}, Genre: {genre}, "
                f"Target audience: {target_audience}, Estimated runtime: {estimated_runtime} minutes"
            )
            # Get the response from the assistant
            response: RunOutput = movie_producer.run(input_text, stream=False)
            st.write(response.content)