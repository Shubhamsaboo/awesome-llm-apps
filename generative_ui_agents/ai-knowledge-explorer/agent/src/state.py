from langchain.agents import AgentState as BaseAgentState
from typing import TypedDict, Literal


class Node(TypedDict):
    id: str
    label: str
    type: Literal["entity", "concept", "theme", "document", "module", "class", "function", "variable"]
    description: str
    detail: str
    sourceDocuments: list[str]


class Edge(TypedDict):
    id: str
    source: str
    target: str
    label: str
    weight: int


class Document(TypedDict):
    id: str
    name: str
    content: str
    status: Literal["uploaded", "processing", "extracted"]


class AgentState(BaseAgentState):
    documents: list[Document]
    nodes: list[Node]
    edges: list[Edge]
    selectedNodeId: str
    processingStatus: str
