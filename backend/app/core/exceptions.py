from __future__ import annotations

from fastapi import status


class AppError(Exception):
    def __init__(self, message: str, *, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, code: str = "app_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", *, code: str = "not_found") -> None:
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, code=code)


class AIProcessingError(AppError):
    def __init__(self, message: str = "I couldn't fully understand that. Can you rephrase or provide more details?") -> None:
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="ai_processing_error")


class InfrastructureError(AppError):
    def __init__(
        self,
        message: str = "The service is temporarily unavailable. Please try again.",
        *,
        provider_status_code: int | None = None,
        provider_detail: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="infrastructure_error")
        self.provider_status_code = provider_status_code
        self.provider_detail = provider_detail


class ConfigurationError(AppError):
    def __init__(self, message: str = "AI configuration is missing or invalid.") -> None:
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="configuration_error")
