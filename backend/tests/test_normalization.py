from datetime import date, time
import json

from app.services.normalization import compute_status, normalize_patch
from app.services.groq_client import GroqClient, LLMJsonError
from app.tools.interaction_tools import _build_log_reply, _build_suggestion_reply, _extract_suggested_followups, _has_explicit_time, _mentions_today, LLMToolPayload
from app.core.exceptions import InfrastructureError


def test_normalize_patch_canonicalizes_date_time_sentiment_and_lists():
    normalized = normalize_patch(
        {
            "interaction_date": "today",
            "interaction_time": "7:36 PM",
            "sentiment": "good",
            "materials_shared": [" brochure ", "brochure", ""],
        }
    )

    assert normalized["interaction_date"] == date.today()
    assert normalized["interaction_time"] == time(19, 36)
    assert normalized["sentiment"] == "positive"
    assert normalized["materials_shared"] == ["brochure"]


def test_compute_status_requires_core_fields_and_detail():
    assert (
        compute_status(
            {
                "hcp_name": "Dr. Sharma",
                "interaction_date": date.today(),
                "interaction_type": "Meeting",
                "sentiment": "positive",
                "topics_discussed": ["efficacy"],
            }
        )
        == "completed"
    )

    assert compute_status({"hcp_name": "Dr. Sharma", "sentiment": "unknown"}) == "draft"


def test_today_detection_and_explicit_time_detection():
    assert _mentions_today("Today I met Dr. Sharma", {})
    assert _mentions_today("I met Dr. Sharma", {"interaction_date": "today"})
    assert not _has_explicit_time("Today I met Dr. Sharma", {})
    assert _has_explicit_time("Today I met Dr. Sharma at 7:36 PM", {})


def test_log_reply_includes_key_details():
    reply = _build_log_reply(
        {
            "hcp_name": "Dr. Sharma",
            "interaction_type": "Meeting",
            "interaction_date": "2026-04-24",
            "interaction_time": "19:36",
            "sentiment": "positive",
            "materials_shared": ["brochure"],
            "topics_discussed": ["OncBoost efficacy"],
        }
    )

    assert "Dr. Sharma" in reply
    assert "19:36" in reply
    assert "positive" in reply
    assert "brochure" in reply


def test_extract_suggested_followups_handles_multiple_shapes():
    payload = LLMToolPayload(fields={"ai_suggested_followups": ["Schedule follow-up meeting"]}, confidence=0.8)
    assert _extract_suggested_followups({}, payload) == ["Schedule follow-up meeting"]

    payload = LLMToolPayload(
        fields={
            "ai_suggested_followups": [
                {"action": "Schedule a call with Dr. Sharma", "due_date": "2026-04-27"},
                {"action": "Send efficacy deck", "owner": "sales team"},
            ]
        },
        confidence=0.8,
    )
    assert _extract_suggested_followups({}, payload) == [
        "Schedule a call with Dr. Sharma by 2026-04-27",
        "Send efficacy deck (sales team)",
    ]

    payload = LLMToolPayload(fields={}, confidence=0.8, reply="Send the efficacy deck")
    assert _extract_suggested_followups({"suggestions": ["Share blood test information"]}, payload) == ["Share blood test information"]
    assert _extract_suggested_followups({}, payload) == ["Send the efficacy deck"]


def test_build_suggestion_reply_lists_actions():
    assert "Schedule follow-up" in _build_suggestion_reply(["Schedule follow-up meeting"])
    assert "these next follow-up actions" in _build_suggestion_reply(["A", "B"])


async def _fake_completion_retry(self, model, system_prompt, user_prompt):
    if not hasattr(self, "_calls"):
        self._calls = []
    self._calls.append(model)
    if len(self._calls) < 3:
        raise InfrastructureError("provider failed", provider_status_code=400, provider_detail="bad request")
    return json.dumps({"tool_name": "LogInteractionTool", "confidence": 0.8})


async def _fake_completion_fail(self, model, system_prompt, user_prompt):
    raise InfrastructureError("provider failed", provider_status_code=400, provider_detail="bad request")


import pytest


@pytest.mark.asyncio
async def test_groq_client_retries_before_success(monkeypatch):
    monkeypatch.setattr(GroqClient, "_completion", _fake_completion_retry)
    client = GroqClient()

    parsed, _, model = await client.json_completion("system", "user")

    assert parsed["tool_name"] == "LogInteractionTool"
    assert model == "llama-3.3-70b-versatile"


@pytest.mark.asyncio
async def test_groq_client_raises_json_error_after_all_provider_failures(monkeypatch):
    monkeypatch.setattr(GroqClient, "_completion", _fake_completion_fail)
    client = GroqClient()

    with pytest.raises(LLMJsonError):
        await client.json_completion("system", "user")
