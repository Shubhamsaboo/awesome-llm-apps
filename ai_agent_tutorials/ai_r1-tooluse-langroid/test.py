
import os
from typing import List
import fire

from langroid.pydantic_v1 import BaseModel, Field
import langroid as lr
from langroid.utils.configuration import settings
from langroid.agent.tool_message import ToolMessage
from langroid.agent.tools.orchestration import FinalResultTool
import langroid.language_models as lm
from rich.prompt import Prompt
from langroid.agent.chat_document import ChatDocument

# for best results:
DEFAULT_LLM = lm.OpenAIChatModel.GPT4o

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# (1) Define the desired structure via Pydantic.
# Here we define a nested structure for City information.
# The "Field" annotations are optional, and are included in the system message
# if provided, and help with generation accuracy.


class CityData(BaseModel):
    population: int = Field(..., description="population of city")
    country: str = Field(..., description="country of city")


class City(BaseModel):
    name: str = Field(..., description="name of city")
    details: CityData = Field(..., description="details of city")


# (2) Define the Tool class for the LLM to use, to produce the above structure.
class CityTool(lr.agent.ToolMessage):
    """Present information about a city"""

    request: str = "city_tool"
    purpose: str = """
    To present <city_info> AFTER user gives a city name,
    with all fields of the appropriate type filled out;
    """
    city_info: City = Field(..., description="information about a city")

    def handle(self) -> FinalResultTool:
        """Handle LLM's structured output if it matches City structure"""
        print("SUCCESS! Got Valid City Info")
        return FinalResultTool(answer=self.city_info)

    @staticmethod
    def handle_message_fallback(
        agent: lr.ChatAgent, msg: str | ChatDocument
    ) -> str | None:
        """
        We end up here when there was no recognized tool msg from the LLM;
        In this case use the AgentDoneTool with content set to
        the original message content.
        """
        if isinstance(msg, ChatDocument) and msg.metadata.sender == lr.Entity.LLM:
            return f"""
            You forgot to use the TOOL/Function `{CityTool.name()}`.
            Please use this tool to present the city info.
            """

    @classmethod
    def examples(cls) -> List["ToolMessage"]:
        # Used to provide few-shot examples in the system prompt
        return [
            cls(
                city_info=City(
                    name="San Francisco",
                    details=CityData(
                        population=800_000,
                        country="USA",
                    ),
                )
            )
        ]


def app(
    m: str = DEFAULT_LLM,  # model
    d: bool = False,  # pass -d to enable debug mode (see prompts etc)
    nc: bool = False,  # pass -nc to disable cache-retrieval (i.e. get fresh answers)
):
    settings.debug = d
    settings.cache = not nc
    # create LLM config
    llm_cfg = lm.OpenAIGPTConfig(
        chat_model=m or DEFAULT_LLM,
        chat_context_length=32000,  # set this based on model
        max_output_tokens=1000,
        temperature=0.2,
        stream=True,
        timeout=45,
    )

    # Recommended: First test if basic chat works with this llm setup as below:
    # Once this works, then you can try the rest of the example.
    #
    # agent = lr.ChatAgent(
    #     lr.ChatAgentConfig(
    #         llm=llm_cfg,
    #     )
    # )
    #
    # agent.llm_response("What is 3 + 4?")
    #
    # task = lr.Task(agent)
    # verify you can interact with this in a chat loop on cmd line:
    # task.run("Concisely answer some questions")

    # Define a ChatAgentConfig and ChatAgent

    config = lr.ChatAgentConfig(
        llm=llm_cfg,
        system_message=f"""
        You will receive a city name, 
        and you must use the TOOL/FUNCTION `{CityTool.name()}` to generate/present
        information about the city.
        """,
    )

    agent = lr.ChatAgent(config)

    # (4) Enable the Tool for this agent --> this auto-inserts JSON instructions
    # and few-shot examples (specified in the tool defn above) into the system message
    agent.enable_message(CityTool)

    # (5) Create task specialized to return City object
    task: City | None = lr.Task(agent, interactive=False)[City]

    while True:
        city = Prompt.ask("Enter a city name")
        if city in ["q", "x"]:
            break
        result: City | None = task.run(city)
        if result:
            print(f"City Info: {result}")
        else:
            print("No valid city info found.")


if __name__ == "__main__":
    fire.Fire(app)