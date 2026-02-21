import asyncio
import os
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

st.set_page_config(page_title="🚀 ShipSite Deploy Agent", page_icon="🚀", layout="wide")

st.markdown("<h1>🚀 ShipSite Deploy Agent</h1>", unsafe_allow_html=True)
st.markdown("Describe a website in natural language and deploy it live instantly")

with st.sidebar:
    st.header("🔑 Authentication")

    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Required for the AI agent to generate site code",
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    shipsite_key = st.text_input(
        "ShipSite API Key",
        type="password",
        help="Get one at shipsite.sh — your agent can also create an account for you",
    )

    st.markdown("---")
    st.markdown("### Example Prompts")

    st.markdown("**Simple Sites**")
    st.markdown("- Build a portfolio page for a designer named Alex")
    st.markdown("- Create a countdown to New Year's Eve")
    st.markdown("- Make a landing page for a coffee shop")

    st.markdown("**More Complex**")
    st.markdown("- Build a recipe page with ingredients and steps")
    st.markdown("- Create a team directory with photo placeholders")

    st.markdown("**Management**")
    st.markdown("- List all my deployed sites")
    st.markdown("- Delete site_abc123")

    st.markdown("---")
    st.caption("Sites cost $0.05/day and auto-expire after 24h unless pinned.")


prompt = st.text_area(
    "Describe Your Site",
    placeholder="e.g. Build a minimal landing page for my SaaS product called Acme Analytics with a hero section, feature grid, and pricing card",
    height=120,
)


async def run_deploy_agent(message: str, api_key: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not provided"

    if not api_key:
        return "Error: ShipSite API key not provided"

    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["@shipsite/mcp"],
            env={**os.environ, "SHIPSITE_API_KEY": api_key},
        )

        async with MCPTools(server_params=server_params) as mcp_tools:
            agent = Agent(
                tools=[mcp_tools],
                instructions=dedent("""\
                    You are a web developer agent that builds and deploys static websites.

                    When the user describes a site they want:
                    1. Generate clean, modern HTML/CSS (and JS if needed) for the site
                    2. Deploy it using the deploy_site tool
                    3. Return the live URL to the user

                    Guidelines for generated sites:
                    - Use modern CSS (flexbox/grid, custom properties, system fonts)
                    - Make sites responsive and mobile-friendly
                    - Keep designs clean and professional
                    - Include all code inline (styles in <style>, scripts in <script>)
                    - Do not use external CDNs or dependencies

                    When deploying:
                    - Put the main page in index.html
                    - Add a style.css file if styles are substantial
                    - Use descriptive names when the user provides one

                    For management requests (list, delete, etc.), use the appropriate tools.

                    Always show the deployed URL prominently in your response.
                """),
                markdown=True,
            )

            response: RunOutput = await asyncio.wait_for(
                agent.arun(message), timeout=120.0
            )
            return response.content

    except asyncio.TimeoutError:
        return "Error: Request timed out after 120 seconds"
    except Exception as e:
        return f"Error: {str(e)}"


if st.button("🚀 Deploy", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar")
    elif not shipsite_key:
        st.error("Please enter your ShipSite API key in the sidebar")
    elif not prompt:
        st.error("Please describe the site you want to build")
    else:
        with st.spinner("Building and deploying your site..."):
            result = asyncio.run(run_deploy_agent(prompt, shipsite_key))

        st.markdown("### Result")
        st.markdown(result)

if "result" not in locals():
    st.markdown(
        """<div style='padding: 1.5rem; border: 1px solid #333; border-radius: 8px; margin-top: 1rem;'>
        <h4>How to use this app:</h4>
        <ol>
            <li>Enter your <strong>OpenAI API key</strong> in the sidebar</li>
            <li>Enter your <strong>ShipSite API key</strong> in the sidebar
                (<a href="https://shipsite.sh" target="_blank">get one here</a>)</li>
            <li>Describe the website you want to create</li>
            <li>Click <strong>Deploy</strong> — your site goes live in seconds</li>
        </ol>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>The AI agent generates HTML, CSS, and JavaScript based on your description</li>
            <li>It calls ShipSite's MCP tools to deploy the files as a live website</li>
            <li>Your site is served on a global CDN with HTTPS — no build steps needed</li>
            <li>Sites auto-expire after 24 hours unless pinned</li>
        </ul>
        </div>""",
        unsafe_allow_html=True,
    )
