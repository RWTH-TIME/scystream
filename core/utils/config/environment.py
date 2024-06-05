from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_HOST: str = "localhost"
    DATABASE_NAME: str = "postgres"
    DATABASE_USER: str = "admin"
    DATABASE_PASSWORD: str = "admin"
    DATABASE_PORT: int = 5432

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", case_sensitive=True)


ENV = Settings()
