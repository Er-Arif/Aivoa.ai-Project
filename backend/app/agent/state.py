from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_message: str
    interaction_id: int
    current_form: dict[str, Any]
    tool_name: str
    tool_output: dict[str, Any]
    assistant_reply: str
    history: list[dict[str, Any]]
    changed_fields: list[str]
    confidence: float
    tool_explanation: str
