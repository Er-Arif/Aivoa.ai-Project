from datetime import date, time

from app.services.normalization import compute_status, normalize_patch
from app.tools.interaction_tools import _build_log_reply, _has_explicit_time, _mentions_today


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
