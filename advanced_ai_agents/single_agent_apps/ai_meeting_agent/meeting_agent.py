import streamlit as st
from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from crewai_tools import SerperDevTool
import os

# Streamlit app setup
st.set_page_config(page_title="AI Meeting Agent 📝", layout="wide")
st.title("AI Meeting Preparation Agent 📝")

# Sidebar for API keys
st.sidebar.header("API Keys")
anthropic_api_key = st.sidebar.text_input("Anthropic API Key", type="password")
serper_api_key = st.sidebar.text_input("Serper API Key", type="password")

# Check if all API keys are set
if anthropic_api_key and serper_api_key:
    # # Set API keys as environment variables
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["SERPER_API_KEY"] = serper_api_key

    claude = LLM(model="claude-3-5-sonnet-20240620", temperature= 0.7, api_key=anthropic_api_key)
    search_tool = SerperDevTool()

    # Input fields
    company_name = st.text_input("Enter the company name:")
    meeting_objective = st.text_input("Enter the meeting objective:")
    attendees = st.text_area("Enter the attendees and their roles (one per line):")
    meeting_duration = st.number_input("Enter the meeting duration (in minutes):", min_value=15, max_value=180, value=60, step=15)
    focus_areas = st.text_input("Enter any specific areas of focus or concerns:")

    # Define the agents
    context_analyzer = Agent(
        role='Meeting Context Specialist',
        goal='Analyze and summarize key background information for the meeting',
        backstory='You are an expert at quickly understanding complex business contexts and identifying critical information.',
        verbose=True,
        allow_delegation=False,
        llm=claude,
        tools=[search_tool]
    )

    industry_insights_generator = Agent(
        role='Industry Expert',
        goal='Provide in-depth industry analysis and identify key trends',
        backstory='You are a seasoned industry analyst with a knack for spotting emerging trends and opportunities.',
        verbose=True,
        allow_delegation=False,
        llm=claude,
        tools=[search_tool]
    )

    strategy_formulator = Agent(
        role='Meeting Strategist',
        goal='Develop a tailored meeting strategy and detailed agenda',
        backstory='You are a master meeting planner, known for creating highly effective strategies and agendas.',
        verbose=True,
        allow_delegation=False,
        llm=claude,
    )

    executive_briefing_creator = Agent(
        role='Communication Specialist',
        goal='Synthesize information into concise and impactful briefings',
        backstory='You are an expert communicator, skilled at distilling complex information into clear, actionable insights.',
        verbose=True,
        allow_delegation=False,
        llm=claude,
    )

    # Define the tasks
    context_analysis_task = Task(
        description=f"""
        Analyze the context for the meeting with {company_name}, considering:
        1. The meeting objective: {meeting_objective}
        2. The attendees: {attendees}
        3. The meeting duration: {meeting_duration} minutes
        4. Specific focus areas or concerns: {focus_areas}

        Research {company_name} thoroughly, including:
        1. Recent news and press releases
        2. Key products or services
        3. Major competitors

        Provide a comprehensive summary of your findings, highlighting the most relevant information for the meeting context.
        Format your output using markdown with appropriate headings and subheadings.
        """,
        agent=context_analyzer,
        expected_output="A detailed analysis of the meeting context and company background, including recent developments, financial performance, and relevance to the meeting objective, formatted in markdown with headings and subheadings."
    )

    industry_analysis_task = Task(
        description=f"""
        Based on the context analysis for {company_name} and the meeting objective: {meeting_objective}, provide an in-depth industry analysis:
        1. Identify key trends and developments in the industry
        2. Analyze the competitive landscape
        3. Highlight potential opportunities and threats
        4. Provide insights on market positioning

        Ensure the analysis is relevant to the meeting objective and attendees' roles.
        Format your output using markdown with appropriate headings and subheadings.
        """,
        agent=industry_insights_generator,
        expected_output="A comprehensive industry analysis report, including trends, competitive landscape, opportunities, threats, and relevant insights for the meeting objective, formatted in markdown with headings and subheadings."
    )

    strategy_development_task = Task(
        description=f"""
        Using the context analysis and industry insights, develop a tailored meeting strategy and detailed agenda for the {meeting_duration}-minute meeting with {company_name}. Include:
        1. A time-boxed agenda with clear objectives for each section
        2. Key talking points for each agenda item
        3. Suggested speakers or leaders for each section
        4. Potential discussion topics and questions to drive the conversation
        5. Strategies to address the specific focus areas and concerns: {focus_areas}

        Ensure the strategy and agenda align with the meeting objective: {meeting_objective}
        Format your output using markdown with appropriate headings and subheadings.
        """,
        agent=strategy_formulator,
        expected_output="A detailed meeting strategy and time-boxed agenda, including objectives, key talking points, and strategies to address specific focus areas, formatted in markdown with headings and subheadings."
    )

    executive_brief_task = Task(
        description=f"""
        Synthesize all the gathered information into a comprehensive yet concise executive brief for the meeting with {company_name}. Create the following components:

        1. A detailed one-page executive summary including:
           - Clear statement of the meeting objective
           - List of key attendees and their roles
           - Critical background points about {company_name} and relevant industry context
           - Top 3-5 strategic goals for the meeting, aligned with the objective
           - Brief overview of the meeting structure and key topics to be covered

        2. An in-depth list of key talking points, each supported by:
           - Relevant data or statistics
           - Specific examples or case studies
           - Connection to the company's current situation or challenges

        3. Anticipate and prepare for potential questions:
           - List likely questions from attendees based on their roles and the meeting objective
           - Craft thoughtful, data-driven responses to each question
           - Include any supporting information or additional context that might be needed

        4. Strategic recommendations and next steps:
           - Provide 3-5 actionable recommendations based on the analysis
           - Outline clear next steps for implementation or follow-up
           - Suggest timelines or deadlines for key actions
           - Identify potential challenges or roadblocks and propose mitigation strategies

        Ensure the brief is comprehensive yet concise, highly actionable, and precisely aligned with the meeting objective: {meeting_objective}. The document should be structured for easy navigation and quick reference during the meeting.
        Format your output using markdown with appropriate headings and subheadings.
        """,
        agent=executive_briefing_creator,
        expected_output="A comprehensive executive brief including summary, key talking points, Q&A preparation, and strategic recommendations, formatted in markdown with main headings (H1), section headings (H2), and subsection headings (H3) where appropriate. Use bullet points, numbered lists, and emphasis (bold/italic) for key information."
    )

    # Create the crew
    meeting_prep_crew = Crew(
        agents=[context_analyzer, industry_insights_generator, strategy_formulator, executive_briefing_creator],
        tasks=[context_analysis_task, industry_analysis_task, strategy_development_task, executive_brief_task],
        verbose=True,
        process=Process.sequential
    )

    # Run the crew when the user clicks the button
    if st.button("Prepare Meeting"):
        with st.spinner("AI agents are preparing your meeting..."):
            result = meeting_prep_crew.kickoff()        
        st.markdown(result)

    st.sidebar.markdown("""
    ## How to use this app:
    1. Enter your API keys in the sidebar.
    2. Provide the requested information about the meeting.
    3. Click 'Prepare Meeting' to generate your comprehensive meeting preparation package.

    The AI agents will work together to:
    - Analyze the meeting context and company background
    - Provide industry insights and trends
    - Develop a tailored meeting strategy and agenda
    - Create an executive brief with key talking points

    This process may take a few minutes. Please be patient!
    """)
else:
    st.warning("Please enter all API keys in the sidebar before proceeding.")