from datetime import date, datetime, time
from typing import Any

from dateutil import parser
from dateutil.relativedelta import relativedelta

LIST_FIELDS = {
    "attendees",
    "topics_discussed",
    "materials_shared",
    "samples_distributed",
    "follow_up_actions",
    "ai_suggested_followups",
}

TEXT_FIELDS = {"hcp_name", "interaction_type", "outcomes"}
VALID_SENTIMENTS = {"positive", "neutral", "negative", "unknown"}


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(text)
    return cleaned


def normalize_sentiment(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    if text in {"pos", "good", "favorable", "favourable", "happy"}:
        return "positive"
    if text in {"neg", "bad", "unfavorable", "unfavourable", "concerned"}:
        return "negative"
    if text in {"mixed", "ok", "okay"}:
        return "neutral"
    return text if text in VALID_SENTIMENTS else "unknown"


def normalize_date(value: Any, today: date | None = None) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    today = today or date.today()
    text = str(value).strip().lower()
    if text == "today":
        return today
    if text == "yesterday":
        return today - relativedelta(days=1)
    if text == "tomorrow":
        return today + relativedelta(days=1)
    try:
        return parser.parse(text, fuzzy=True, default=datetime.combine(today, time.min)).date()
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_time(value: Any) -> time | None:
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    try:
        parsed = parser.parse(str(value), fuzzy=True)
        return parsed.time().replace(second=0, microsecond=0)
    except (ValueError, TypeError, OverflowError):
        return None


def current_local_time() -> time:
    return datetime.now().time().replace(second=0, microsecond=0)


def normalize_patch(raw: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue
        if key in LIST_FIELDS:
            normalized[key] = normalize_list(value)
        elif key == "sentiment":
            normalized[key] = normalize_sentiment(value)
        elif key == "interaction_date":
            parsed_date = normalize_date(value)
            if parsed_date:
                normalized[key] = parsed_date
        elif key == "interaction_time":
            parsed_time = normalize_time(value)
            if parsed_time:
                normalized[key] = parsed_time
        elif key in TEXT_FIELDS:
            text = str(value).strip()
            if text:
                normalized[key] = text
        elif key == "status" and value in {"draft", "completed"}:
            normalized[key] = value
    return normalized


def compute_status(data: dict[str, Any]) -> str:
    required = [
        data.get("hcp_name"),
        data.get("interaction_date"),
        data.get("interaction_type"),
        data.get("sentiment") not in (None, "unknown"),
    ]
    has_detail = bool(data.get("topics_discussed") or data.get("materials_shared") or data.get("outcomes"))
    return "completed" if all(required) and has_detail else "draft"
