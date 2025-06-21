import os
from pathlib import Path
from dotenv import load_dotenv


def load_api_key(key_name="OPENAI_API_KEY"):
    env_path = Path(".") / ".env"
    load_dotenv(dotenv_path=env_path)
    return os.environ.get(key_name)
