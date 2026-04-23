from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    changed_fields: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str
    assistant_reply: str
    raw_llm_output: str | None = None
    validated_output: dict[str, Any] = Field(default_factory=dict)
