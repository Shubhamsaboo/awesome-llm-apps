from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from langchain_openai import ChatOpenAI
from composio_langchain import ComposioToolSet, Action, App
llm = ChatOpenAI(api_key="")
prompt = hub.pull("hwchase17/openai-functions-agent")

composio_toolset = ComposioToolSet(api_key="")
tools = composio_toolset.get_tools(actions=['GOOGLEDOCS_CREATE_DOCUMENT'])

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
task = "Open a new google doc and write a short paragraph about the benefits of using LLM Quantisation and KV Cache"
result = agent_executor.invoke({"input": task})
print(result)
