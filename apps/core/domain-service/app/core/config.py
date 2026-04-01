from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    
    database_url: Optional[str] = None
    
    official_sim_base_url: str = "http://localhost:8001"
    
    default_provider_mode: str = "mock"
    odoo_provider_mode: str = "mock"
    odoo_base_url: str = "http://localhost:8069"
    odoo_db: str = "odoo"
    odoo_username: str = "admin"
    odoo_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
