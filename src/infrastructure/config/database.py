from collections.abc import Generator
from contextlib import contextmanager
from time import sleep
from sqlmodel import create_engine, Session, SQLModel

from .settings import settings
# Import of models is needed for SQLModel to generate tables from metadata
import src.infrastructure.adapters.outbound.persistence.models # noqa: F401


engine = create_engine(str(settings.POSTGRES_DSN), echo=True)

def create_db_and_tables() -> None:
    sleep(1) # Костыль for postgres container startup
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(engine)

    try:
        yield session
    finally:
        session.close()