from typing import Literal
from typing_extensions import TypedDict
from copilotkit import CopilotKitState


class SchemaResult(TypedDict):
    format: Literal["csv", "json", "markdown_table", "plain_text", "empty"]
    columns: list[dict]
    rows: list[dict]
    row_count: int


class AgentState(CopilotKitState):
    schema_result: SchemaResult | None
    active_component: str | None
    last_transform: dict | None
