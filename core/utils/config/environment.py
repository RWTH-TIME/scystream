from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import List


class Settings(BaseSettings):
    DATABASE_HOST: str = "core-postgres"
    DATABASE_NAME: str = "core"
    DATABASE_USER: str = "core"
    DATABASE_PASSWORD: str = "core"
    DATABASE_PORT: int = 5432
    EMAIL_DOMAIN_WHITELIST: List[str] = ["time.rwth-aachen.de"]

    LOG_LEVEL: str = "INFO"

    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET: str = "secret"
    JWT_ACCESS_TOKEN_EXPIRE_MIN: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", case_sensitive=True)


ENV = Settings(_env_file=".env", _env_file_encoding="utf-8")
