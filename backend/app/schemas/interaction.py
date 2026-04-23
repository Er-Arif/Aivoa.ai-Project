from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Sentiment = Literal["positive", "neutral", "negative", "unknown"]
InteractionStatus = Literal["draft", "completed"]


class InteractionBase(BaseModel):
    hcp_name: str | None = None
    interaction_type: str | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    attendees: list[str] = Field(default_factory=list)
    topics_discussed: list[str] = Field(default_factory=list)
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    sentiment: Sentiment = "unknown"
    outcomes: str | None = None
    follow_up_actions: list[str] = Field(default_factory=list)
    ai_suggested_followups: list[str] = Field(default_factory=list)
    status: InteractionStatus = "draft"


class InteractionPatch(BaseModel):
    hcp_name: str | None = None
    interaction_type: str | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    attendees: list[str] | None = None
    topics_discussed: list[str] | None = None
    materials_shared: list[str] | None = None
    samples_distributed: list[str] | None = None
    sentiment: Sentiment | None = None
    outcomes: str | None = None
    follow_up_actions: list[str] | None = None
    ai_suggested_followups: list[str] | None = None
    status: InteractionStatus | None = None


class InteractionRead(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InteractionHistoryItem(BaseModel):
    id: int
    hcp_name: str | None
    interaction_type: str | None
    interaction_date: date | None
    sentiment: Sentiment
    topics_discussed: list[str]
    outcomes: str | None
    follow_up_actions: list[str]

    model_config = ConfigDict(from_attributes=True)
