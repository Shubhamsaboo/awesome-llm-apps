from typing_extensions import TypedDict, Optional
from typing import List, Literal, Annotated 
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class ImageState(TypedDict):
    message: Annotated[list, add_messages]
    refined_prompt: Optional[str]
    image_url: List[str]
    current_step: Literal["pending", "in_progress", "completed"]  
    error: Optional[str]
    message_type: str | None

# Validator Class
class MessageClassifier(BaseModel):
    message_type:Literal["image", "chat"] = Field(
        ...,
        description="Classify what the user wants is it an Image or just a chat"
    )