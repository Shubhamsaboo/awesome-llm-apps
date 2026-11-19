import pytest

pytest.skip("catalog fixture, not a collected test", allow_module_level=True)

from phi.agent import Agent
from langchain.chat_models import ChatOpenAI
