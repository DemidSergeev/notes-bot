from collections.abc import Generator
from contextlib import contextmanager
from sqlmodel import create_engine, Session, SQLModel

from .config import settings
# Import of models is needed for SQLModel to generate tables from metadata
import src.adapters.outbound.persistence.models # noqa: F401


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