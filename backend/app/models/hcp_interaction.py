from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Integer, String, Text, Time, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HCPInteraction(Base):
    __tablename__ = "hcp_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcp_name: Mapped[str | None] = mapped_column(String(255), index=True)
    interaction_type: Mapped[str | None] = mapped_column(String(80))
    interaction_date: Mapped[date | None] = mapped_column(Date)
    interaction_time: Mapped[time | None] = mapped_column(Time)
    attendees: Mapped[list[str]] = mapped_column(JSONB, default=list)
    topics_discussed: Mapped[list[str]] = mapped_column(JSONB, default=list)
    materials_shared: Mapped[list[str]] = mapped_column(JSONB, default=list)
    samples_distributed: Mapped[list[str]] = mapped_column(JSONB, default=list)
    sentiment: Mapped[str] = mapped_column(String(20), default="unknown")
    outcomes: Mapped[str | None] = mapped_column(Text)
    follow_up_actions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    ai_suggested_followups: Mapped[list[str]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages = relationship("ChatMessage", back_populates="interaction", cascade="all, delete-orphan")
