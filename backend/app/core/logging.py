import logging
import json
import sys

from app.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )


def log_event(level: int, event: str, **fields) -> None:
    payload = {"event": event, **fields}
    logging.getLogger("aivoa.crm").log(level, json.dumps(payload, default=str))
