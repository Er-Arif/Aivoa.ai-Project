from datetime import date
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hcp_interaction import HCPInteraction
from app.services.groq_client import GroqClient, LLMJsonError
from app.services.interaction_service import fetch_history, interaction_to_dict, update_interaction
from app.services.normalization import current_local_time, normalize_date, normalize_time
from app.tools.base import ToolResult

INTERACTION_FIELDS = [
    "hcp_name",
    "interaction_type",
    "interaction_date",
    "interaction_time",
    "attendees",
    "topics_discussed",
    "materials_shared",
    "samples_distributed",
    "sentiment",
    "outcomes",
    "follow_up_actions",
    "ai_suggested_followups",
]


class LLMToolPayload(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reply: str | None = None


def tool_payload_from_json(parsed: dict[str, Any]) -> LLMToolPayload:
    if isinstance(parsed.get("fields"), dict):
        return LLMToolPayload.model_validate(parsed)
    fields = {key: value for key, value in parsed.items() if key in INTERACTION_FIELDS}
    return LLMToolPayload(
        fields=fields,
        confidence=float(parsed.get("confidence", 0.6)),
        reply=parsed.get("reply"),
    )


class IntentPayload(BaseModel):
    tool_name: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


def _schema_instruction() -> str:
    return (
        "Return STRICT JSON only. Valid field keys are: "
        + ", ".join(INTERACTION_FIELDS)
        + ". Array fields must be arrays of strings. confidence must be 0 to 1."
    )


def _mentions_today(message: str, patch: dict[str, Any]) -> bool:
    lowered = message.lower()
    raw_date = patch.get("interaction_date")
    normalized_date = normalize_date(raw_date) if raw_date is not None else None
    return "today" in lowered or normalized_date == date.today()


def _has_explicit_time(message: str, patch: dict[str, Any]) -> bool:
    if normalize_time(patch.get("interaction_time")) is not None:
        return True
    lowered = message.lower()
    time_markers = ["am", "pm", " a.m", " p.m", ":"]
    return any(marker in lowered for marker in time_markers)


def _build_log_reply(data: dict[str, Any]) -> str:
    details: list[str] = []
    if data.get("hcp_name"):
        details.append(f"logged the interaction for {data['hcp_name']}")
    else:
        details.append("logged the interaction")
    if data.get("interaction_type"):
        details.append(f"type: {data['interaction_type']}")
    if data.get("interaction_date"):
        details.append(f"date: {data['interaction_date']}")
    if data.get("interaction_time"):
        details.append(f"time: {data['interaction_time']}")
    if data.get("sentiment") and data["sentiment"] != "unknown":
        details.append(f"sentiment: {data['sentiment']}")
    if data.get("materials_shared"):
        details.append(f"materials shared: {', '.join(data['materials_shared'])}")
    if data.get("topics_discussed"):
        details.append(f"topics: {', '.join(data['topics_discussed'])}")
    return "I've " + "; ".join(details) + "."


async def classify_tool(llm: GroqClient, user_message: str, current_form: dict[str, Any]) -> tuple[str, float, str, dict[str, Any]]:
    system_prompt = (
        "You classify CRM assistant messages into exactly one primary tool. "
        "Allowed tools: LogInteractionTool, EditInteractionTool, SummarizeInteractionTool, "
        "FetchHCPHistoryTool, SuggestNextActionTool. Return JSON with tool_name and confidence."
    )
    user_prompt = f"Current form: {current_form}\nUser message: {user_message}"
    parsed, raw, _ = await llm.json_completion(system_prompt, user_prompt)
    payload = IntentPayload.model_validate(parsed)
    allowed = {
        "LogInteractionTool",
        "EditInteractionTool",
        "SummarizeInteractionTool",
        "FetchHCPHistoryTool",
        "SuggestNextActionTool",
    }
    tool_name = payload.tool_name if payload.tool_name in allowed else "LogInteractionTool"
    return tool_name, payload.confidence, raw, payload.model_dump()


class LogInteractionTool:
    name = "LogInteractionTool"
    explanation = "I've logged this interaction by extracting key details from your message."

    async def run(self, session: AsyncSession, interaction: HCPInteraction, user_message: str, llm: GroqClient) -> ToolResult:
        system_prompt = (
            "Extract structured CRM interaction fields from the user message. "
            "Infer interaction_type as Meeting if appropriate. Convert dates/times only if explicit or relative. "
            + _schema_instruction()
        )
        parsed, raw, _ = await llm.json_completion(system_prompt, user_message)
        payload = tool_payload_from_json(parsed)
        patch = {key: value for key, value in payload.fields.items() if key in INTERACTION_FIELDS}
        if _mentions_today(user_message, patch) and not _has_explicit_time(user_message, patch):
            patch["interaction_time"] = current_local_time()
        updated, changed = await update_interaction(session, interaction, patch)
        updated_dict = interaction_to_dict(updated)
        return ToolResult(
            data=updated_dict,
            changed_fields=changed,
            confidence=payload.confidence,
            explanation=self.explanation,
            assistant_reply=_build_log_reply(updated_dict),
            raw_llm_output=raw,
            validated_output=payload.model_dump(),
        )


class EditInteractionTool:
    name = "EditInteractionTool"
    explanation = "I updated only the fields mentioned in your correction."

    async def run(self, session: AsyncSession, interaction: HCPInteraction, user_message: str, llm: GroqClient) -> ToolResult:
        current = interaction_to_dict(interaction)
        system_prompt = (
            "Update only fields explicitly mentioned in the correction. "
            "Return only changed fields inside fields. Never return a full replacement object. "
            + _schema_instruction()
        )
        parsed, raw, _ = await llm.json_completion(system_prompt, f"Current form: {current}\nCorrection: {user_message}")
        payload = tool_payload_from_json(parsed)
        patch = {key: value for key, value in payload.fields.items() if key in INTERACTION_FIELDS}
        updated, changed = await update_interaction(session, interaction, patch)
        return ToolResult(
            data=interaction_to_dict(updated),
            changed_fields=changed,
            confidence=payload.confidence,
            explanation=self.explanation,
            assistant_reply="I updated the interaction based on your correction while preserving untouched fields.",
            raw_llm_output=raw,
            validated_output=payload.model_dump(),
        )


class SummarizeInteractionTool:
    name = "SummarizeInteractionTool"
    explanation = "I summarized the current interaction from the saved CRM details."

    async def run(self, session: AsyncSession, interaction: HCPInteraction, user_message: str, llm: GroqClient) -> ToolResult:
        current = interaction_to_dict(interaction)
        system_prompt = "Generate a concise CRM summary. Return JSON only with fields: summary, confidence."
        parsed, raw, _ = await llm.json_completion(system_prompt, f"Interaction: {current}")
        summary = str(parsed.get("summary", "No summary available.")).strip()
        confidence = float(parsed.get("confidence", 0.7))
        return ToolResult(
            data={"summary": summary},
            confidence=max(0.0, min(1.0, confidence)),
            explanation=self.explanation,
            assistant_reply=summary,
            raw_llm_output=raw,
            validated_output={"summary": summary, "confidence": confidence},
        )


class FetchHCPHistoryTool:
    name = "FetchHCPHistoryTool"
    explanation = "I retrieved previous interactions for this HCP without changing the current form."

    async def run(self, session: AsyncSession, interaction: HCPInteraction, user_message: str, llm: GroqClient) -> ToolResult:
        current = interaction_to_dict(interaction)
        system_prompt = "Extract the HCP name to search history for. Return JSON only with fields: hcp_name, confidence."
        parsed, raw, _ = await llm.json_completion(system_prompt, f"Current form: {current}\nUser message: {user_message}")
        hcp_name = str(parsed.get("hcp_name") or current.get("hcp_name") or "").strip()
        confidence = float(parsed.get("confidence", 0.7))
        records = await fetch_history(session, hcp_name, exclude_id=interaction.id) if hcp_name else []
        history = [
            {
                "id": record.id,
                "hcp_name": record.hcp_name,
                "interaction_type": record.interaction_type,
                "interaction_date": record.interaction_date.isoformat() if record.interaction_date else None,
                "sentiment": record.sentiment,
                "topics_discussed": record.topics_discussed or [],
                "outcomes": record.outcomes,
                "follow_up_actions": record.follow_up_actions or [],
            }
            for record in records
        ]
        reply = f"I found {len(history)} previous interaction(s) for {hcp_name or 'this HCP'}."
        return ToolResult(
            data={"searched_hcp": hcp_name},
            history=history,
            confidence=max(0.0, min(1.0, confidence)),
            explanation=self.explanation,
            assistant_reply=reply,
            raw_llm_output=raw,
            validated_output={"hcp_name": hcp_name, "confidence": confidence},
        )


class SuggestNextActionTool:
    name = "SuggestNextActionTool"
    explanation = "I suggested follow-ups based on the saved interaction context."

    async def run(self, session: AsyncSession, interaction: HCPInteraction, user_message: str, llm: GroqClient) -> ToolResult:
        current = interaction_to_dict(interaction)
        system_prompt = (
            "Recommend practical next CRM follow-up actions. "
            "Return JSON only with fields: fields, confidence where fields.ai_suggested_followups is an array of strings."
        )
        parsed, raw, _ = await llm.json_completion(system_prompt, f"Interaction: {current}")
        payload = tool_payload_from_json(parsed)
        suggestions = payload.fields.get("ai_suggested_followups", [])
        updated, changed = await update_interaction(session, interaction, {"ai_suggested_followups": suggestions})
        reply = "I suggested the next best follow-up actions based on this interaction."
        return ToolResult(
            data=interaction_to_dict(updated),
            changed_fields=changed,
            confidence=payload.confidence,
            explanation=self.explanation,
            assistant_reply=reply,
            raw_llm_output=raw,
            validated_output=payload.model_dump(),
        )


TOOLS = {
    "LogInteractionTool": LogInteractionTool(),
    "EditInteractionTool": EditInteractionTool(),
    "SummarizeInteractionTool": SummarizeInteractionTool(),
    "FetchHCPHistoryTool": FetchHCPHistoryTool(),
    "SuggestNextActionTool": SuggestNextActionTool(),
}


def graceful_failure() -> ToolResult:
    return ToolResult(
        data={},
        confidence=0.0,
        explanation="I need a clearer instruction before I can safely update the CRM record.",
        assistant_reply="I couldn't fully understand that. Can you rephrase or provide more details?",
        validated_output={"error": "invalid_llm_json"},
    )
