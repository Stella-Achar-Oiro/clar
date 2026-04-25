from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    langsmith_api_key: str = ""
    langsmith_project: str = "clar-production"
    clerk_jwks_url: str = ""
    environment: str = "development"
    log_level: str = "INFO"
    max_file_size_mb: int = 10
    report_session_ttl_minutes: int = 30


settings = Settings()
