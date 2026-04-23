from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://aivoa:aivoa@localhost:15432/aivoa_crm"
    groq_api_key: str = ""
    groq_model_primary: str = "gemma2-9b-it"
    groq_model_fallback: str = "llama-3.3-70b-versatile"
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8")


settings = Settings()
