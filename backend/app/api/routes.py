from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse, InteractionWithMessages
from app.schemas.interaction import InteractionPatch, InteractionRead
from app.services.chat_service import ChatApplicationService
from app.services.interaction_service import (
    create_interaction,
    get_interaction,
    get_interaction_with_messages,
    safe_patch_interaction,
)

router = APIRouter(prefix="/api/v1")


@router.post("/interaction", response_model=InteractionRead)
async def create_interaction_endpoint(session: AsyncSession = Depends(get_session)):
    return await create_interaction(session)


@router.get("/interaction/{interaction_id}", response_model=InteractionWithMessages)
async def get_interaction_endpoint(interaction_id: int, session: AsyncSession = Depends(get_session)):
    interaction = await get_interaction_with_messages(session, interaction_id)
    if not interaction:
        raise NotFoundError("Interaction not found", code="interaction_not_found")
    return {"interaction": interaction, "messages": sorted(interaction.messages, key=lambda msg: msg.created_at)}


@router.patch("/interaction/{interaction_id}", response_model=InteractionRead)
async def patch_interaction_endpoint(
    interaction_id: int,
    patch: InteractionPatch,
    session: AsyncSession = Depends(get_session),
):
    interaction = await get_interaction(session, interaction_id)
    if not interaction:
        raise NotFoundError("Interaction not found", code="interaction_not_found")
    updated, _ = await safe_patch_interaction(session, interaction, patch)
    return updated


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, session: AsyncSession = Depends(get_session)):
    return await ChatApplicationService(session).process_message(request)
