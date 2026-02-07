from textwrap import dedent
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.serpapi import SerpApiTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.models.openai import OpenAIChat
import streamlit as st

st.set_page_config(page_title="AgroDrone Europe - Content Factory", layout="wide")
st.title("AgroDrone Europe - Content Factory")
st.caption(
    "Generate SEO-optimized content for agrodroneeurope.com: "
    "blog posts, landing pages, service descriptions, and social media content."
)

openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
serp_api_key = st.sidebar.text_input("SerpAPI Key (for research)", type="password")

CONTENT_TYPES = [
    "Blog Post (SEO-optimized)",
    "Landing Page Copy",
    "Service Description",
    "Social Media Post Pack",
    "Case Study",
    "FAQ Section",
]

SERVICES = [
    "Pflanzenschutz (Crop Protection)",
    "Aussaat (Seeding/Sowing)",
    "NDVI Monitoring",
    "Dachreinigung (Roof Cleaning)",
    "General / Company Overview",
]

content_type = st.sidebar.selectbox("Content Type", CONTENT_TYPES)
service_focus = st.sidebar.selectbox("Service Focus", SERVICES)
language = st.sidebar.selectbox("Language", ["German (Deutsch)", "English"])
target_keywords = st.sidebar.text_input(
    "Target SEO Keywords (comma-separated)",
    placeholder="e.g. Drohne Pflanzenschutz, Agrardrohne Deutschland",
)

lang_code = "German" if "German" in language else "English"

if openai_api_key and serp_api_key:
    researcher = Agent(
        name="Researcher",
        role="Researches agricultural drone industry trends and competitors",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
            You are a senior market researcher specializing in agricultural technology,
            precision farming, and drone services in Europe (especially Germany).
            Given a topic, generate targeted search queries, find the most relevant
            sources, and compile key facts, statistics, and insights.
            """
        ),
        instructions=[
            "Generate 3-5 search queries related to the given topic, focusing on the German/European agricultural drone market.",
            "Search for each query and analyze the results.",
            "Return the 10 most relevant URLs with a brief summary of key findings from each.",
            "Focus on: industry statistics, regulations, benefits, case studies, and trends.",
            "Include German-language sources when available.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )

    seo_writer = Agent(
        name="SEO Content Writer",
        role="Writes SEO-optimized content for agricultural drone services",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
            You are a professional SEO content writer specializing in B2B agricultural
            technology content. You write for AgroDrone Europe (agrodroneeurope.com),
            a German company offering professional drone services for agriculture
            (crop protection, seeding, NDVI monitoring) and building maintenance
            (roof cleaning).
            """
        ),
        instructions=[
            "Write content based on the research provided and the specified content type.",
            "Naturally incorporate the target SEO keywords without keyword stuffing.",
            "Use proper heading hierarchy (H1, H2, H3) for SEO.",
            "Include a compelling meta title (max 60 chars) and meta description (max 155 chars).",
            "Write in the specified language with a professional but approachable tone.",
            "For blog posts: include introduction, 3-5 main sections, conclusion, and a call-to-action.",
            "For landing pages: focus on benefits, social proof, and clear CTAs.",
            "For social media packs: create 5 posts for different platforms (LinkedIn, Instagram, Facebook).",
            "For case studies: use the Problem-Solution-Result framework.",
            "For FAQ sections: create 8-10 relevant Q&A pairs with schema-friendly formatting.",
            "Always reference agrodroneeurope.com services where appropriate.",
            "Include internal linking suggestions to relevant service pages.",
        ],
        tools=[Newspaper4kTools()],
        add_datetime_to_context=True,
        markdown=True,
    )

    editor = Agent(
        name="Content Editor",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        team=[researcher, seo_writer],
        description=dedent(
            """\
            You are the head of content at AgroDrone Europe. You coordinate research
            and writing to produce high-quality, SEO-optimized content that drives
            organic traffic and converts visitors into leads for drone services.
            """
        ),
        instructions=[
            "First, ask the Researcher to gather relevant data and sources on the topic.",
            "Then, pass the research findings, content type, target keywords, and language to the SEO Content Writer.",
            f"The content must be written in {lang_code}.",
            f"Content type requested: {content_type}.",
            f"Service focus: {service_focus}.",
            "Review the draft for: SEO optimization, factual accuracy, brand voice consistency, and conversion potential.",
            "Ensure the content includes meta title, meta description, and heading structure.",
            "Add a section at the end with: suggested internal links, target keywords used, and content score notes.",
            "The final content must be publication-ready for agrodroneeurope.com.",
        ],
        add_datetime_to_context=True,
        markdown=True,
    )

    topic = st.text_area(
        "Describe the content topic",
        placeholder="e.g. Benefits of drone-based crop protection for German wheat farmers compared to traditional spraying methods",
        height=100,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        generate = st.button("Generate Content", type="primary")

    if generate and topic:
        prompt = dedent(
            f"""\
            Create {content_type} content for agrodroneeurope.com.

            Topic: {topic}
            Service Focus: {service_focus}
            Target Keywords: {target_keywords if target_keywords else "determine the best keywords based on the topic"}
            Language: {lang_code}

            The company AgroDrone Europe offers professional drone services in Germany:
            - Pflanzenschutz (Crop Protection) - precision spraying with agricultural drones
            - Aussaat (Seeding/Sowing) - drone-based seeding for hard-to-reach areas
            - NDVI Monitoring - crop health analysis using multispectral drone imaging
            - Dachreinigung (Roof Cleaning) - professional drone-assisted roof cleaning

            Website: agrodroneeurope.com
            """
        )

        with st.spinner("Researching, writing, and editing content..."):
            response: RunOutput = editor.run(prompt, stream=False)

        st.divider()
        st.subheader("Generated Content")
        st.markdown(response.content)

        st.divider()
        st.download_button(
            label="Download as Markdown",
            data=response.content,
            file_name="agrodrone_content.md",
            mime="text/markdown",
        )
else:
    st.info("Enter your OpenAI and SerpAPI keys in the sidebar to get started.")
