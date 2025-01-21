import os
import sys
from typing import NoReturn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import ChatOpenAI

from browser_use import Agent

def create_agents() -> tuple[Agent, Agent]:
	"""
	Creates two agent instances for Amazon and Flipkart searches.
	
	Returns:
		tuple[Agent, Agent]: A tuple containing Amazon and Flipkart agents
	"""
	llm = ChatOpenAI(model='gpt-4o-mini', api_key="sk-proj-")
	
	amazon_agent = Agent(
		task='Go to amazon.com, search for laptop, sort by best rating, and give me the price of the first result',
		llm=llm,
	)
	
	flipkart_agent = Agent(
		task='Go to flipkart.com, search for laptop, sort by best rating, and give me the price of the first result',
		llm=llm,
	)
	
	return amazon_agent, flipkart_agent

async def main() -> NoReturn:
	"""
	Main function to run both agents sequentially and compare results.
	"""
	amazon_agent, flipkart_agent = create_agents()
	
	print("Running Amazon search...")
	await amazon_agent.run(max_steps=10)
	
	print("\nRunning Flipkart search...")
	await flipkart_agent.run(max_steps=10)
	
	input('Press Enter to continue...')

if __name__ == "__main__":
	asyncio.run(main())