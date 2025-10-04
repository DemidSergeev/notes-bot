from collections.abc import Generator
from contextlib import contextmanager
from typing import Protocol
from sqlmodel import create_engine, Session, SQLModel

from .config import settings
import src.core.domain.models  # noqa: F401

engine = create_engine(settings.POSTGRES_DSN, echo=True)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()