extracted_code = """import pygame
import random

pygame.init()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Bouncing Rectangle")

clock = pygame.time.Clock()

# Rectangle properties
rect_width = 50
rect_height = 30
x = screen_width // 2 - rect_width // 2
y = screen_height // 2 - rect_height // 2
dx = 5
dy = 5

colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)]
current_color = random.choice(colors)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update position
    x += dx
    y += dy

    # Check collisions and change direction/color
    if x <= 0 or x + rect_width >= screen_width:
        dx = -dx
        current_color = random.choice(colors)
    if y <= 0 or y + rect_height >= screen_height:
        dy = -dy
        current_color = random.choice(colors)

    # Fill the screen with a background color
    screen.fill((0, 0, 0))

    # Draw the rectangle
    pygame.draw.rect(screen, current_color, (x, y, rect_width, rect_height))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()"""

import asyncio
from browser_use import Agent as BrowserAgent, SystemPrompt
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


async def run_pygame_on_trinket(code: str) -> None:
    task_description = (
        "You are a Trinket.io PyGame expert. Follow these steps precisely:\n"
        "1. Navigate to https://trinket.io/features/pygame\n"
        "2. In the main.py file, clear and delete the existing code. If you dont know how to do it, copy the whole code by command + A and delete it.\n"
        "3. Paste this code into the editor:\n{0} by control\n"
        "4. Click the Run button on the right to execute the code\n"
        "5. Wait for the pygame visualisation to appear, once it does, view it for 10 seconds and then Quit the pygame window\n"
        "6. If you have any issues, try to fix them by yourself. If you cannot fix them, ask the user for help.\n"
    ).format(code)

    browser_agent = BrowserAgent(
        task=task_description,
        llm=ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        max_actions_per_step=10,
        max_failures=25
    )

    result = await browser_agent.run()

# Run the async function
asyncio.run(run_pygame_on_trinket(extracted_code))