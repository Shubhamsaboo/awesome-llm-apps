import asyncio
from browser_use import Agent, SystemPrompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

class MemeSystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        existing_rules = super().important_rules()
        
        new_rules = """
9. TEMPLATE DISCOVERY PROTOCOL:
   - Templates appear in horizontal carousel below "Popular" heading
   - MUST click right arrow (→) until reaching end of template list
   - Continue clicking until arrow becomes disabled/greyed out
   - Wait 1.2 seconds between clicks for proper loading
   - Count total templates viewed before selection

10. CONTEXT-AWARE SELECTION:
   - Analyze query for key elements: teams/participants, outcome type, emotional tone
   - Match template to these abstract categories:
     1. Winner/loser dynamics
     2. Disappointment/failure themes
     3. Sports-specific imagery
   - Prefer templates with multiple text boxes for contrast

11. CAPTION GENERATION FRAMEWORK:
   - First text box: Highlight winning side's achievement
   - Second text box: Emphasize losing side's failure
   - Use domain-specific terms from query context (sports/politics/etc)
   - Maintain humorous contrast between text elements
"""
        return f'{existing_rules}\n{new_rules}'

async def generate_meme(query: str):
    api_key = "sk-proj-"
    llm = ChatOpenAI(model='gpt-4o-mini', api_key=api_key)

    agent = Agent(
        task=(
            "1. Navigate to imgflip.com/memegenerator\n"
            "2. Exhaustively scroll through ALL templates\n"
            "3. Create meme about: {query}\n" 
            "4. Select template matching query's core conflict\n"
            "5. Add contrasting captions based on query elements\n"
            "6. Generate final meme without watermark"
        ),
        llm=llm,
        max_actions_per_step=5,
        system_prompt_class=MemeSystemPrompt,
    )

    await agent.run(max_steps=25)

if __name__ == '__main__':
    query = "India losing against Australia in the final test match"
    asyncio.run(generate_meme(query))


#     📍 Step 4
# INFO     [agent] 🤷 Eval: Unknown - Loaded the Meme Generator page successfully.
# INFO     [agent] 🧠 Memory: 
# INFO     [agent] 🎯 Next goal: Scroll through all available meme templates.
# INFO     [agent] 🛠️  Action 1/1: {"scroll_down":{"amount":300}}
# INFO     [controller] 🔍  Scrolled down the page by 300 pixels
#SEEMS LIKE IT IS NOT SCROLLING TO THE RIGHT, IT IS GOING DOWN