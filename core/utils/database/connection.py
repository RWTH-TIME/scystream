from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.config.environment import ENV

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{ENV.DATABASE_USER}:{ENV.DATABASE_PASSWORD}"
    f"@{ENV.DATABASE_HOST}:{ENV.DATABASE_PORT}/{ENV.DATABASE_NAME}"
)


# db connection
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
