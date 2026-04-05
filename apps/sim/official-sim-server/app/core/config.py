import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    _default_sqlite = Path(__file__).resolve().parents[2] / "official_sim.db"
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_default_sqlite}",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    service_name: str = "official-sim-server"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"

    # Push notification (P1: official-sim -> domain-service)
    push_domain_service_url: Optional[str] = os.getenv("PUSH_DOMAIN_SERVICE_URL")
    push_timeout_s: float = float(os.getenv("PUSH_TIMEOUT_S", "3.0"))
    push_max_retries: int = int(os.getenv("PUSH_MAX_RETRIES", "2"))


settings = Settings()
