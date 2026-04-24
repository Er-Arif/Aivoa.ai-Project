import json
import logging
import sys
from typing import Any

from app.core.config import settings
from app.core.context import get_request_id


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def log_event(level: int, event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "service": "aivoa-hcp-crm",
        "request_id": get_request_id(),
        **fields,
    }
    logging.getLogger("aivoa.crm").log(level, json.dumps(payload, default=str))
