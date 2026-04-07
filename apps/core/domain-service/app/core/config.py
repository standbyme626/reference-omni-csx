from enum import Enum
from typing import List, Optional

from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True

    database_url: Optional[str] = None

    official_sim_base_url: str = "http://localhost:8001"
    official_sim_enable_mock_fallback: bool = False

    default_provider_mode: str = "official_sim"
    odoo_provider_mode: str = "real"
    odoo_base_url: str = "http://localhost:8069"
    odoo_db: str = "odoo"
    odoo_username: str = "admin"
    odoo_api_key: str = ""

    push_domain_service_url: str = "http://localhost:8000/api/push-events"

    cors_origins: List[str] = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
