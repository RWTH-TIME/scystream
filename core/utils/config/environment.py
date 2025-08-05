from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEVELOPMENT: bool = False
    EXTERNAL_URL: str = "http://scystream"

    DATABASE_HOST: str = "core-postgres"
    DATABASE_NAME: str = "core"
    DATABASE_USER: str = "core"
    DATABASE_PASSWORD: str = "core"
    DATABASE_PORT: int = 5432
    EMAIL_DOMAIN_WHITELIST: list[str] = ["time.rwth-aachen.de"]

    LOG_LEVEL: str = "INFO"

    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET: str = "secret"
    JWT_ACCESS_TOKEN_EXPIRE_MIN: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CATAPULTE_HOSTNAME: str = "catapulte"
    CATAPULTE_PORT: int = 3000
    CATAPULTE_SENDER: str = "mailing@scystream"
    CATAPULTE_SSL_ENABLED: bool = False

    # This has to reach the internal minio, provided by the defaults
    EXTERNAL_URL_DATA_S3: str = "http://localhost:9000"

    CB_NETWORK_MODE: str = "scystream_data_processing"

    DEFAULT_CB_CONFIG_S3_HOST: str = "http://data-minio"
    DEFAULT_CB_CONFIG_S3_PORT: str = "9000"
    DEFAULT_CB_CONFIG_S3_ACCESS_KEY: str = "minioadmin"
    DEFAULT_CB_CONFIG_S3_SECRET_KEY: str = "minioadmin"
    DEFAULT_CB_CONFIG_S3_BUCKET_NAME: str = "data"
    DEFAULT_CB_CONFIG_S3_FILE_PATH: str = "/"

    DEFAULT_CB_CONFIG_PG_USER: str = "postgres"
    DEFAULT_CB_CONFIG_PG_PASS: str = "postgres"
    DEFAULT_CB_CONFIG_PG_HOST: str = "data-postgres"
    DEFAULT_CB_CONFIG_PG_PORT: str = "5432"

    AIRFLOW_HOST: str = "http://localhost:3333"
    AIRFLOW_USER: str = "airflow"
    AIRFLOW_PASS: str = "airflow"
    AIRFLOW_DAG_DIR: str = "../airflow-dags"

    WORKFLOW_TEMPLATE_REPO: str = (
        "git@git.rwth-aachen.de:tim-institute/pipeline-templates.git"
    )

    KEYCLOAK_SERVER_URL: str = "http://keycloak"
    KEYCLOAK_REALM: str = "scystream"
    KEYCLOAK_CLIENT_ID: str = "scystream-core"
    KEYCLOAK_CLIENT_SECRET: str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    KEYCLOAK_REDIRECT_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


ENV = Settings()
