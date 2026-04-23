from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat_message import ChatMessage
from app.models.hcp_interaction import HCPInteraction
from app.schemas.interaction import InteractionPatch
from app.services.normalization import compute_status, normalize_patch


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
    await session.commit()
    await session.refresh(interaction)
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
    await session.commit()
    await session.refresh(interaction)
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
    await session.commit()
    await session.refresh(message)
    return message


async def fetch_history(session: AsyncSession, hcp_name: str, exclude_id: int | None = None) -> list[HCPInteraction]:
    stmt = select(HCPInteraction).where(HCPInteraction.hcp_name.ilike(f"%{hcp_name}%"))
    if exclude_id:
        stmt = stmt.where(HCPInteraction.id != exclude_id)
    stmt = stmt.order_by(HCPInteraction.interaction_date.desc().nullslast(), HCPInteraction.created_at.desc()).limit(10)
    result = await session.execute(stmt)
    return list(result.scalars().all())
