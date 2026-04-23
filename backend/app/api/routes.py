from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import InteractionAgent
from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse, InteractionWithMessages
from app.schemas.interaction import InteractionPatch, InteractionRead
from app.services.interaction_service import (
    add_chat_message,
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
        raise HTTPException(status_code=404, detail="Interaction not found")
    return {"interaction": interaction, "messages": sorted(interaction.messages, key=lambda msg: msg.created_at)}


@router.patch("/interaction/{interaction_id}", response_model=InteractionRead)
async def patch_interaction_endpoint(
    interaction_id: int,
    patch: InteractionPatch,
    session: AsyncSession = Depends(get_session),
):
    interaction = await get_interaction(session, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    updated, _ = await safe_patch_interaction(session, interaction, patch)
    return updated


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, session: AsyncSession = Depends(get_session)):
    interaction = await get_interaction(session, request.interaction_id) if request.interaction_id else None
    if not interaction:
        interaction = await create_interaction(session)

    await add_chat_message(session, interaction.id, "user", request.message)
    agent = InteractionAgent(session, interaction)
    state = await agent.run(request.message)

    refreshed = await get_interaction(session, interaction.id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="Interaction not found after agent execution")

    assistant_message = await add_chat_message(
        session,
        refreshed.id,
        "assistant",
        state["assistant_reply"],
        tool_name=state.get("tool_name"),
        confidence=state.get("confidence"),
    )
    return {
        "interaction": refreshed,
        "assistant_message": assistant_message,
        "tool_name": state.get("tool_name", "UnknownTool"),
        "tool_explanation": state.get("tool_explanation", ""),
        "confidence": state.get("confidence", 0.0),
        "changed_fields": state.get("changed_fields", []),
        "tool_output": state.get("tool_output", {}),
        "history": state.get("history"),
    }
