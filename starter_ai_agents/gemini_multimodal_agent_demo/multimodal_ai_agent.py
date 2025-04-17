from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from google.generativeai import upload_file, get_file
import time

# 1. Initialize the Multimodal Agent
agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"), tools=[DuckDuckGoTools()], markdown=True)

# 2. Image Input
image_url = "https://example.com/sample_image.jpg"

# 3. Audio Input
audio_file = "sample_audio.mp3"

# 4. Video Input
video_file = upload_file("sample_video.mp4")  
while video_file.state.name == "PROCESSING":  
    time.sleep(2)
    video_file = get_file(video_file.name)

# 5. Multimodal Query
query = """ 
Combine insights from the inputs:
1. **Image**: Describe the scene and its significance.  
2. **Audio**: Extract key messages that relate to the visual.  
3. **Video**: Look at the video input and provide insights that connect with the image and audio context.  
4. **Web Search**: Find the latest updates or events linking all these topics.
Summarize the overall theme or story these inputs convey.
"""

# 6. Multimodal Agent generates unified response
agent.print_response(query, images=[image_url], audio=audio_file, videos=[video_file], stream=True)