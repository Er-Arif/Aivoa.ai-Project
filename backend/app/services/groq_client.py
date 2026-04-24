import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ConfigurationError, InfrastructureError
from app.core.logging import log_event

import logging


class LLMJsonError(RuntimeError):
    pass


class GroqClient:
    def __init__(self) -> None:
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def json_completion(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], str, str]:
        attempts = [
            settings.groq_model_primary,
            settings.groq_model_primary,
            settings.groq_model_fallback,
        ]
        last_raw = ""
        for model in attempts:
            try:
                raw = await self._completion(model, system_prompt, user_prompt)
                log_event(logging.INFO, "llm_completion_received", model=model, raw_llm_output=raw)
            except ConfigurationError:
                raise
            except httpx.HTTPError as exc:
                last_raw = str(exc)
                log_event(logging.WARNING, "llm_http_error", model=model, error=str(exc))
                continue
            last_raw = raw
            try:
                parsed = json.loads(raw)
                return parsed, raw, model
            except json.JSONDecodeError:
                log_event(logging.WARNING, "invalid_llm_json", model=model, raw_llm_output=raw)
        raise LLMJsonError(last_raw or "LLM did not return valid JSON")

    async def _completion(self, model: str, system_prompt: str, user_prompt: str) -> str:
        if not settings.groq_api_key:
            raise ConfigurationError("Missing GROQ_API_KEY")
        payload = {
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(self.url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise InfrastructureError(f"Groq request failed with status {exc.response.status_code}") from exc
            except httpx.HTTPError as exc:
                raise InfrastructureError("Unable to reach Groq API") from exc
        return data["choices"][0]["message"]["content"].strip()
