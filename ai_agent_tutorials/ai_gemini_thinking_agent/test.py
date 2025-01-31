from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"), http_options={'api_version':'v1alpha'})

import asyncio

config = {'thinking_config': {'include_thoughts': True}}

async def main():
    chat = client.aio.chats.create(
        model='gemini-2.0-flash-thinking-exp-01-21',
        config=config
    )
    response = await chat.send_message('Explain Deep Q Networks from first principles')
    print(response.text)
    response = await chat.send_message('What did you just say before this?')
    print(response.text)

asyncio.run(main())