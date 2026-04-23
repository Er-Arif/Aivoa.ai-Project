from datetime import date, time

from app.services.normalization import compute_status, normalize_patch


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
