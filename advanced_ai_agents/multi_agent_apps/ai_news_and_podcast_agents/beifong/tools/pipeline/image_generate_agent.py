from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.dalle import DalleTools
from textwrap import dedent
import json
from dotenv import load_dotenv
import uuid
from db.agent_config_v2 import PODCAST_IMG_DIR
import os
import requests
from typing import Any


load_dotenv()

IMAGE_GENERATION_AGENT_DESCRIPTION = "You are an AI agent that can generate images using DALL-E."
IMAGE_GENERATION_AGENT_INSTRUCTIONS = dedent("""
                                             When the user asks you to create an image, use the `create_image` tool to create the image.
                                             Create a modern, eye-catching podcast cover images that represents a podcast given podcast topic.
                                             Create 3 images for the given podcast topic.

                                            IMPORTANT INSTRUCTIONS:
                                            - DO NOT include ANY text in the image
                                            - DO NOT include any words, titles, or lettering
                                            - Create a purely visual and symbolic representation
                                            - Use imagery that represents the specific topics mentioned
                                            - I like Studio Ghibli flavor if possible
                                            - The image should work well as a podcast cover thumbnail
                                            - Create a clean, professional design suitable for a podcast
                                            - AGAIN, DO NOT INCLUDE ANY TEXT
                                        """)


def download_images(image_urls):
    local_image_filenames = []
    try:
        if image_urls:
            for image_url in image_urls:
                unique_id = str(uuid.uuid4())
                filename = f"podcast_banner_{unique_id}.png"
                os.makedirs(PODCAST_IMG_DIR, exist_ok=True)
                print(f"Downloading image: {filename}")
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_path = os.path.join(PODCAST_IMG_DIR, filename)
                with open(image_path, "wb") as f:
                    f.write(response.content)
                local_image_filenames.append(filename)
                print(f"Successfully downloaded: {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading images (network): {e}")
    except Exception as e:
        print(f"Error downloading images: {e}")

    return local_image_filenames


def image_generation_agent_run(query: str, generated_script: Any) -> str:
    session_id = str(uuid.uuid4())
    try:
        image_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            tools=[DalleTools()],
            description=IMAGE_GENERATION_AGENT_DESCRIPTION,
            instructions=IMAGE_GENERATION_AGENT_INSTRUCTIONS,
            markdown=True,
            show_tool_calls=True,
            session_id=session_id,
        )
        image_agent.run(f"query: {query},\n podcast script: {json.dumps(generated_script)}", session_id=session_id)
        images = image_agent.get_images()
        image_urls = []
        if images and isinstance(images, list):
            for image_response in images:
                image_url = image_response.url
                image_urls.append(image_url)
        local_image_filenames = download_images(image_urls)
        return {"banner_images": local_image_filenames, "banner_url": local_image_filenames[0] if local_image_filenames else None}
    except Exception as e:
        print(f"Error in Image Generation Agent: {e}")
        return {}
