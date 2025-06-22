from pydantic import BaseModel
from typing import Callable

class Tool(BaseModel):
    name:str
    description:str
    function: Callable
    params: dict

class ToolResult(BaseModel):
    is_success: bool
    content: str | None = None
    error: str | None = None