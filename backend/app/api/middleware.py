from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.core.context import set_request_id
from app.core.logging import log_event


def register_request_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(request_id)
        start = time.perf_counter()
        log_event(logging.INFO, "request_started", method=request.method, path=request.url.path)
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
        log_event(
            logging.INFO,
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
