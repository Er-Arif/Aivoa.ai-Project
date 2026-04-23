import logging

try:
    import langchain

    for _name, _value in {"debug": False, "verbose": False, "llm_cache": None}.items():
        if not hasattr(langchain, _name):
            setattr(langchain, _name, _value)
except ImportError:
    pass

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.core.logging import log_event
from app.models.hcp_interaction import HCPInteraction
from app.services.groq_client import GroqClient, LLMJsonError
from app.services.interaction_service import interaction_to_dict
from app.tools.interaction_tools import TOOLS, classify_tool, graceful_failure


class InteractionAgent:
    def __init__(self, session: AsyncSession, interaction: HCPInteraction) -> None:
        self.session = session
        self.interaction = interaction
        self.llm = GroqClient()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("tool_execution", self._tool_execution)
        graph.add_node("format_response", self._format_response)
        graph.add_edge(START, "classify_intent")
        graph.add_edge("classify_intent", "tool_execution")
        graph.add_edge("tool_execution", "format_response")
        graph.add_edge("format_response", END)
        return graph.compile()

    async def run(self, user_message: str) -> AgentState:
        initial: AgentState = {
            "user_message": user_message,
            "interaction_id": self.interaction.id,
            "current_form": interaction_to_dict(self.interaction),
        }
        return await self.graph.ainvoke(initial)

    async def _classify_intent(self, state: AgentState) -> AgentState:
        try:
            tool_name, confidence, raw, validated = await classify_tool(
                self.llm,
                state["user_message"],
                state["current_form"],
            )
            log_event(
                logging.INFO,
                "agent_tool_selected",
                interaction_id=state["interaction_id"],
                user_message=state["user_message"],
                selected_tool=tool_name,
                raw_llm_output=raw,
                validated_output=validated,
                confidence=confidence,
            )
            return {"tool_name": tool_name, "confidence": confidence}
        except (LLMJsonError, ValueError) as exc:
            log_event(logging.WARNING, "agent_classification_failed", interaction_id=state["interaction_id"], error=str(exc))
            return {"tool_name": "GracefulFailureTool", "confidence": 0.0}

    async def _tool_execution(self, state: AgentState) -> AgentState:
        if state.get("tool_name") == "GracefulFailureTool":
            result = graceful_failure()
        else:
            tool = TOOLS[state["tool_name"]]
            try:
                result = await tool.run(self.session, self.interaction, state["user_message"], self.llm)
            except (LLMJsonError, ValueError) as exc:
                log_event(logging.WARNING, "agent_tool_failed", interaction_id=state["interaction_id"], selected_tool=state["tool_name"], error=str(exc))
                result = graceful_failure()

        log_event(
            logging.INFO,
            "agent_tool_executed",
            interaction_id=state["interaction_id"],
            user_message=state["user_message"],
            selected_tool=state.get("tool_name"),
            raw_llm_output=result.raw_llm_output,
            validated_output=result.validated_output,
            confidence=result.confidence,
            db_write_result={"changed_fields": result.changed_fields},
        )
        tool_output = {**result.data, "confidence": result.confidence}
        return {
            "tool_output": tool_output,
            "history": result.history,
            "changed_fields": result.changed_fields,
            "confidence": result.confidence,
            "tool_explanation": result.explanation,
            "assistant_reply": result.assistant_reply,
        }

    async def _format_response(self, state: AgentState) -> AgentState:
        return state
