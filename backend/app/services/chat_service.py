from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import InteractionAgent
from app.core.exceptions import NotFoundError
from app.core.logging import log_event
from app.schemas.chat import ChatRequest
from app.services.interaction_service import (
    add_chat_message,
    create_interaction,
    get_interaction,
)


class ChatApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def process_message(self, request: ChatRequest) -> dict:
        interaction = await self._get_or_create_interaction(request.interaction_id)
        await add_chat_message(self.session, interaction.id, "user", request.message)

        agent = InteractionAgent(self.session, interaction)
        state = await agent.run(request.message)

        refreshed = await get_interaction(self.session, interaction.id)
        if not refreshed:
            raise NotFoundError("Interaction not found after agent execution", code="interaction_missing_after_agent")

        assistant_message = await add_chat_message(
            self.session,
            refreshed.id,
            "assistant",
            state["assistant_reply"],
            tool_name=state.get("tool_name"),
            confidence=state.get("confidence"),
        )

        log_event(
            logging.INFO,
            "chat_request_processed",
            interaction_id=refreshed.id,
            selected_tool=state.get("tool_name"),
            changed_fields=state.get("changed_fields", []),
            history_count=len(state.get("history") or []),
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

    async def _get_or_create_interaction(self, interaction_id: int | None):
        if interaction_id is None:
            interaction = await create_interaction(self.session)
            log_event(logging.INFO, "interaction_created_for_chat_session", interaction_id=interaction.id)
            return interaction

        interaction = await get_interaction(self.session, interaction_id)
        if not interaction:
            raise NotFoundError("Interaction not found", code="interaction_not_found")
        return interaction
