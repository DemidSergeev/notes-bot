from collections.abc import Generator
from contextlib import contextmanager
from time import sleep
from sqlmodel import create_engine, Session, SQLModel, select

from .settings import settings
# Import of models is needed for SQLModel to generate tables from metadata
import src.infrastructure.adapters.outbound.persistence.models # noqa: F401


engine = create_engine(str(settings.POSTGRES_DSN), echo=False)

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
        from .wiring import course_repo
        from src.core.domain.models import Course, Subject, Note
        from src.core.domain.common.enums import CourseYear

        subjects_year_one = [
            Subject(name="Math", notes=[
                Note(title="Limits and derivatives", price_rub=99),
                Note(title="Linear equations", price_rub=79)
            ]),
            Subject(name="Science", notes=[
                Note(title="Physics Notes", price_rub=89)
            ]),
            Subject(name="History", notes=[
                Note(title="World War II Notes", price_rub=79)
            ]),
        ]
        course_year_one = Course(
            year=CourseYear.ONE,
            subjects=subjects_year_one
        )
        course_repo.save(course=course_year_one)

        subjects_year_two = [
            Subject(name="Algebra"),
            Subject(name="Biology"),
            Subject(name="World History"),
        ]
        course_year_two = Course(
            year=CourseYear.TWO,
            subjects=subjects_year_two
        )
        course_repo.save(course=course_year_two)

def has_initial_data() -> bool:
    with get_session() as session:
        session: Session

        statement = select(SQLModel.metadata.tables['course'])
        result = session.exec(statement).first()
        return result is not None