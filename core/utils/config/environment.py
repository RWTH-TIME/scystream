from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import List


class Settings(BaseSettings):
    DEVELOPMENT: bool = False
    EXTERNAL_URL: str = "http://scystream"

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

    CATAPULTE_HOSTNAME: str = "catapulte"
    CATAPULTE_PORT: int = 3000
    CATAPULTE_SENDER: str = "mailing@scystream"
    CATAPULTE_SSL_ENABLED: bool = False

    TRUSTED_CBC_DOMAINS: List[str] = ["github.com"]
    MAX_CBC_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    DEFAULT_CB_CONFIG_S3_HOST: str = "data-minio"
    DEFAULT_CB_CONFIG_S3_PORT: str = "9001"
    DEFAULT_CB_CONFIG_S3_ACCESS_KEY: str = "access"
    DEFAULT_CB_CONFIG_S3_SECRET_KEY: str = "secret"
    DEFAULT_CB_CONFIG_S3_BUCKET_NAME: str = "data_tf_bucket"
    DEFAULT_CB_CONFIG_S3_FILE_PATH: str = "/"

    DEFAULT_CB_CONFIG_PG_USER: str = "postgres"
    DEFAULT_CB_CONFIG_PG_PASS: str = "postgres"
    DEFAULT_CB_CONFIG_PG_HOST: str = "data-postgres"
    DEFAULT_CB_CONFIG_PG_PORT: str = "5432"

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", case_sensitive=True
    )


ENV = Settings(_env_file=".env", _env_file_encoding="utf-8")
