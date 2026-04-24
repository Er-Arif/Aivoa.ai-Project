from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import InfrastructureError
from app.core.logging import log_event
from app.models.chat_message import ChatMessage
from app.models.hcp_interaction import HCPInteraction
from app.schemas.interaction import InteractionPatch
from app.services.normalization import compute_status, normalize_patch

import logging


def interaction_to_dict(interaction: HCPInteraction) -> dict[str, Any]:
    return {
        "id": interaction.id,
        "hcp_name": interaction.hcp_name,
        "interaction_type": interaction.interaction_type,
        "interaction_date": interaction.interaction_date.isoformat() if interaction.interaction_date else None,
        "interaction_time": interaction.interaction_time.strftime("%H:%M") if interaction.interaction_time else None,
        "attendees": interaction.attendees or [],
        "topics_discussed": interaction.topics_discussed or [],
        "materials_shared": interaction.materials_shared or [],
        "samples_distributed": interaction.samples_distributed or [],
        "sentiment": interaction.sentiment,
        "outcomes": interaction.outcomes,
        "follow_up_actions": interaction.follow_up_actions or [],
        "ai_suggested_followups": interaction.ai_suggested_followups or [],
        "status": interaction.status,
    }


async def create_interaction(session: AsyncSession) -> HCPInteraction:
    interaction = HCPInteraction(
        attendees=[],
        topics_discussed=[],
        materials_shared=[],
        samples_distributed=[],
        follow_up_actions=[],
        ai_suggested_followups=[],
        sentiment="unknown",
        status="draft",
    )
    session.add(interaction)
    try:
        await session.commit()
        await session.refresh(interaction)
    except SQLAlchemyError as exc:
        await session.rollback()
        log_event(logging.ERROR, "interaction_create_failed", error=str(exc))
        raise InfrastructureError("Unable to create interaction.") from exc
    log_event(logging.INFO, "interaction_created", interaction_id=interaction.id)
    return interaction


async def get_interaction(session: AsyncSession, interaction_id: int) -> HCPInteraction | None:
    result = await session.execute(select(HCPInteraction).where(HCPInteraction.id == interaction_id))
    return result.scalar_one_or_none()


async def get_interaction_with_messages(session: AsyncSession, interaction_id: int) -> HCPInteraction | None:
    result = await session.execute(
        select(HCPInteraction)
        .where(HCPInteraction.id == interaction_id)
        .options(selectinload(HCPInteraction.messages))
    )
    return result.scalar_one_or_none()


async def update_interaction(session: AsyncSession, interaction: HCPInteraction, patch: dict[str, Any]) -> tuple[HCPInteraction, list[str]]:
    normalized = normalize_patch(patch)
    current = interaction_to_dict(interaction)
    merged = {**current, **normalized}
    normalized["status"] = compute_status(merged)
    changed_fields = [key for key, value in normalized.items() if current.get(key) != value]
    for key, value in normalized.items():
        setattr(interaction, key, value)
    try:
        await session.commit()
        await session.refresh(interaction)
    except SQLAlchemyError as exc:
        await session.rollback()
        log_event(logging.ERROR, "interaction_update_failed", interaction_id=interaction.id, error=str(exc))
        raise InfrastructureError("Unable to update interaction.") from exc
    log_event(logging.INFO, "interaction_updated", interaction_id=interaction.id, changed_fields=changed_fields)
    return interaction, changed_fields


async def safe_patch_interaction(session: AsyncSession, interaction: HCPInteraction, patch: InteractionPatch) -> tuple[HCPInteraction, list[str]]:
    return await update_interaction(session, interaction, patch.model_dump(exclude_unset=True))


async def add_chat_message(
    session: AsyncSession,
    interaction_id: int,
    role: str,
    content: str,
    tool_name: str | None = None,
    confidence: float | None = None,
) -> ChatMessage:
    message = ChatMessage(
        interaction_id=interaction_id,
        role=role,
        content=content,
        tool_name=tool_name,
        confidence=confidence,
    )
    session.add(message)
    try:
        await session.commit()
        await session.refresh(message)
    except SQLAlchemyError as exc:
        await session.rollback()
        log_event(logging.ERROR, "chat_message_persist_failed", interaction_id=interaction_id, role=role, error=str(exc))
        raise InfrastructureError("Unable to save chat message.") from exc
    log_event(logging.INFO, "chat_message_persisted", interaction_id=interaction_id, message_id=message.id, role=role, tool_name=tool_name)
    return message


async def fetch_history(session: AsyncSession, hcp_name: str, exclude_id: int | None = None) -> list[HCPInteraction]:
    stmt = select(HCPInteraction).where(HCPInteraction.hcp_name.ilike(f"%{hcp_name}%"))
    if exclude_id:
        stmt = stmt.where(HCPInteraction.id != exclude_id)
    stmt = stmt.order_by(HCPInteraction.interaction_date.desc().nullslast(), HCPInteraction.created_at.desc()).limit(10)
    try:
        result = await session.execute(stmt)
    except SQLAlchemyError as exc:
        log_event(logging.ERROR, "interaction_history_query_failed", hcp_name=hcp_name, exclude_id=exclude_id, error=str(exc))
        raise InfrastructureError("Unable to fetch HCP history.") from exc
    records = list(result.scalars().all())
    log_event(logging.INFO, "interaction_history_fetched", hcp_name=hcp_name, exclude_id=exclude_id, result_count=len(records))
    return records
