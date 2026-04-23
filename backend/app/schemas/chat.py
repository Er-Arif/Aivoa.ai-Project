from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.interaction import InteractionHistoryItem, InteractionRead


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    interaction_id: int | None = None


class ChatMessageRead(BaseModel):
    id: int
    interaction_id: int
    role: Literal["user", "assistant"]
    content: str
    tool_name: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    interaction: InteractionRead
    assistant_message: ChatMessageRead
    tool_name: str
    tool_explanation: str
    confidence: float
    changed_fields: list[str]
    tool_output: dict[str, Any]
    history: list[InteractionHistoryItem] | None = None


class InteractionWithMessages(BaseModel):
    interaction: InteractionRead
    messages: list[ChatMessageRead]
