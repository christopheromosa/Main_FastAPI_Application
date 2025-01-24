from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base,DeclarativeMeta
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgres://admin:admin!!23@localhost:5432/postgres_app_database"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base: DeclarativeMeta = declarative_base()
Base.metadata.create_all(bind=engine)
