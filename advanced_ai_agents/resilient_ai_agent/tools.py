import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

class LLMTool:
    def run(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
