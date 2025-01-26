import asyncio
from browser_use import Agent, SystemPrompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
# class MemeSystemPrompt(SystemPrompt):
#     def important_rules(self) -> str:
#         existing_rules = super().important_rules()
        
#         new_rules = """
# 9. TEMPLATE DISCOVERY PROTOCOL:
#    - Templates appear in horizontal carousel below "Popular" heading
#    - MUST click right arrow (→) until reaching end of template list
#    - Continue clicking until arrow becomes disabled/greyed out
#    - Wait 1.2 seconds between clicks for proper loading
#    - Count total templates viewed before selection

# 10. CONTEXT-AWARE SELECTION:
#    - Analyze query for key elements: teams/participants, outcome type, emotional tone
#    - Match template to these abstract categories:
#      1. Winner/loser dynamics
#      2. Disappointment/failure themes
#      3. Sports-specific imagery
#    - Prefer templates with multiple text boxes for contrast

# 11. CAPTION GENERATION FRAMEWORK:
#    - First text box: Highlight winning side's achievement
#    - Second text box: Emphasize losing side's failure
#    - Use domain-specific terms from query context (sports/politics/etc)
#    - Maintain humorous contrast between text elements
# """
#         return f'{existing_rules}\n{new_rules}'

async def generate_meme(query: str) -> None:
    api_key = "sk-ant-api03---dfg9zwAA"  
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        api_key=api_key,
    )

    task_description = (
        "You are a meme generator expert. You are given a query and you need to generate a meme for it.\n"
        "1. Go to https://imgflip.com/memetemplates \n"
        "2. Click on the Search bar in the middle and search for the main keyword in this query: '{0}'\n"
        "3. Choose any meme template that metaphorically fits the meme topic: '{0}'\n"
        "   by clicking on the 'Add Caption' button below it\n"
        "4. Write a Top Text (setup/context) and Bottom Text (punchline/outcome) related to '{0}'.\n" 
        "5. Check the preview making sure it is funny and a meaningful meme. Adjust text directly if needed. \n"
        "6. Look at the meme and text on it, if it doesnt make sense, PLEASE retry by filling the text boxes with different text. \n"
        "7. Click on the Generate meme button to generate the meme\n"
    ).format(query)

    agent = Agent(
        task=task_description,
        llm=llm,
        max_actions_per_step=5,
        # system_prompt_class=MemeSystemPrompt,
    )

    await agent.run(max_steps=25)

if __name__ == '__main__':
    query = "India losing against Australia in the final test match"
    asyncio.run(generate_meme(query))
