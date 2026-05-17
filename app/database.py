from sqlmodel import SQLModel, Session, create_engine

from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=True if settings.APP_ENV == "development" else False,
)


def create_db_and_tables() -> None:
    """
    Create database tables.

    For this prototype, SQLModel creates tables directly.
    In a production system, migrations with Alembic would be preferred.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency for database sessions.

    It opens a database session for each request and closes it automatically.
    """
    with Session(engine) as session:
        yield session