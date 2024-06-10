from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import List

class Settings(BaseSettings):
    DATABASE_HOST: str = "core-postgres"
    DATABASE_NAME: str = "core"
    DATABASE_USER: str = "core"
    DATABASE_PASSWORD: str = "core"
    DATABASE_PORT: int = 5432
    EMAIL_WHITELIST: List[str] = ["time.rwth-aachen.de"]

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", case_sensitive=True)
    
ENV = Settings(_env_file="src/.env", _env_file_encoding="utf-8")
