import logging
from collections.abc import Generator
from contextlib import contextmanager
from time import sleep
from sqlmodel import create_engine, Session, SQLModel

from .settings import settings
# Import of models is needed for SQLModel to generate tables from metadata
import src.infrastructure.adapters.outbound.persistence.models # noqa: F401


logger = logging.getLogger(__name__)

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
    from .wiring import course_repo
    from src.core.domain.models import Course
    from src.core.domain.common.enums import CourseYear

    for year in CourseYear:
        existing_course = course_repo.get_by_year(year)
        if existing_course is None:
            new_course = Course(year=year)
            course_repo.save(course=new_course)
            logging.debug("Course %d created", year.value)