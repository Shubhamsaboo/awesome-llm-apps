from typing import Literal
from typing_extensions import TypedDict
from copilotkit import CopilotKitState


class QueryResult(TypedDict):
    sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    result_type: Literal["table", "single_row", "aggregate"]


class PendingMutation(TypedDict):
    mutation_id: str
    sql: str
    params: list
    table: str
    row_id: int
    changes: list[dict]
    description: str


class AgentState(CopilotKitState):
    query_result: QueryResult | None
    pending_mutation: PendingMutation | None
    schema_context: str
