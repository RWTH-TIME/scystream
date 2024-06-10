from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_HOST: str = "core-postgres"
    DATABASE_NAME: str = "core"
    DATABASE_USER: str = "core"
    DATABASE_PASSWORD: str = "core"
    DATABASE_PORT: int = 5432

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", case_sensitive=True)
    
ENV = Settings(_env_file="src/.env", _env_file_encoding="utf-8")
