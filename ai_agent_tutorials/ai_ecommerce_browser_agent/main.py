import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio

from langchain_openai import ChatOpenAI

from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

browser = Browser(
	config=BrowserConfig(
		disable_security=True,
		headless=False,
	)
)
llm = ChatOpenAI(model='gpt-4o')


async def main():
	agents = [
		Agent(task=task, llm=llm, browser=browser)
		for task in [
			'Search Google for weather in Tokyo',
			'Check Reddit front page title',
			'Look up Bitcoin price on Coinbase',
			'Find NASA image of the day',
			# 'Check top story on CNN',
			# 'Search latest SpaceX launch date',

		]
	]

	await asyncio.gather(*[agent.run() for agent in agents])

	# async with await browser.new_context() as context:
	agentX = Agent(
		task='Go to apple.com and return the title of the page',
		llm=llm,
		browser=browser,
		# browser_context=context,
	)
	await agentX.run()

	await browser.close()


if __name__ == '__main__':
	asyncio.run(main())