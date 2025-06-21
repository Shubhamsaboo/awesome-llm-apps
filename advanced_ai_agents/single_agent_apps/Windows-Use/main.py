# main.py
from langchain_google_genai import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv

load_dotenv()

llm=ChatGoogleGenerativeAI(model='gemini-2.0-flash')
instructions=['We have Claude Desktop, Perplexity and ChatGPT App installed on the desktop so if you need any help, just ask your AI friends.']
agent = Agent(instructions=instructions,llm=llm,use_vision=True)
query=input("Enter your query: ")
agent_result=agent.invoke(query=query)
print(agent_result.content)