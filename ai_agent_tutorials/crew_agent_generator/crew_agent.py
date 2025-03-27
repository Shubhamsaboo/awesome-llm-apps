import streamlit as st
import textwrap

# Function to generate agent code
def generate_agent_code(requirement, framework):
    if framework == "CrewAI":
        return textwrap.dedent(f"""
        from crewai import Agent, Task, Crew

        class ResearchAssistant(Agent):
            def __init__(self):
                super().__init__(
                    name='Research Assistant',
                    role='Fetches documents and summarizes key points',
                    backstory='{requirement}',
                    goal='Provide relevant and concise summaries'
                )

        class ResearchTask(Task):
            def __init__(self):
                super().__init__(
                    description='Retrieve relevant documents and extract key information',
                    expected_output='Summarized key points'
                )

        crew = Crew(agents=[ResearchAssistant()], tasks=[ResearchTask()])
        crew.run()
        """)
    elif framework == "LangGraph":
        return textwrap.dedent(f"""
        from langgraph.graph import StateGraph

        def research_agent(state):
            documents = retrieve_documents('{requirement}')
            summary = summarize_documents(documents)
            return {{"summary": summary}}

        workflow = StateGraph()
        workflow.add_node("research", research_agent)
        workflow.set_entry_point("research")
        output = workflow.run()
        print(output)
        """)
    else:
        return "Invalid framework selection."

# Streamlit UI
st.title("Crew-Agent-Generator")
st.markdown("Generate agent code for CrewAI or LangGraph based on natural language requirements.")

requirement = st.text_area("Describe your agent's requirements:")
framework = st.selectbox("Choose Framework:", ["CrewAI", "LangGraph"])

if st.button("Generate Code"):
    if requirement.strip():
        code = generate_agent_code(requirement, framework)
        st.code(code, language="python")
    else:
        st.warning("Please enter a requirement.")

    #Copy & Download Options
if 'code' in locals():
    st.download_button("Download Code", code, file_name="agent_code.py")
