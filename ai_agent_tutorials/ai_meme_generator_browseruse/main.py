import asyncio
from browser_use import Agent, SystemPrompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

async def generate_meme(query: str) -> None:
    api_key = "sk-A"  # Replace with your actual DeepSeek API key
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        api_key=api_key
    )

    task_description = (
        "You are a meme generator expert. You are given a query and you need to generate a meme for it.\n"
        "1. Go to https://imgflip.com/memetemplates \n"
        "2. Click on the Search bar in the middle and search for ONLY ONE MAIN ACTION VERB (like 'bully', 'laugh', 'cry') in this query: '{0}'\n"
        "3. Choose any meme template that metaphorically fits the meme topic: '{0}'\n"
        "   by clicking on the 'Add Caption' button below it\n"
        "4. Write a Top Text (setup/context) and Bottom Text (punchline/outcome) related to '{0}'.\n" 
        "5. Check the preview making sure it is funny and a meaningful meme. Adjust text directly if needed. \n"
        "6. Look at the meme and text on it, if it doesnt make sense, PLEASE retry by filling the text boxes with different text. \n"
        "7. Click on the Generate meme button to generate the meme\n"
        "8. Copy the image link and give it as the output\n"
    ).format(query)

    agent = Agent(
        task=task_description,
        llm=llm,
        max_actions_per_step=5,
        max_failures=25
    )

    history = await agent.run()
    history.final_result()

if __name__ == '__main__':
    query = "Elon Musk bullying sam altman about trump winning the election"
    asyncio.run(generate_meme(query))
