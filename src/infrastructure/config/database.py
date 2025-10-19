from collections.abc import Generator
from contextlib import contextmanager
from time import sleep
from sqlmodel import create_engine, Session, SQLModel, select

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

def init_database() -> None:
    create_db_and_tables()
    if not has_initial_data():
        from .wiring import course_service
        from src.core.domain.models import Subject
        from src.core.domain.common.enums import CourseYear

        subjects_year_one = [
            Subject(name="Math"),
            Subject(name="Science"),
            Subject(name="History"),
        ]
        course_service.create(subjects=subjects_year_one, year=CourseYear.ONE)
        subjects_year_two = [
            Subject(name="Algebra"),
            Subject(name="Biology"),
            Subject(name="World History"),
        ]
        course_service.create(subjects=subjects_year_two, year=CourseYear.TWO)

def has_initial_data() -> bool:
    with get_session() as session:
        session: Session

        statement = select(SQLModel.metadata.tables['course'])
        result = session.exec(statement).first()
        return result is not None