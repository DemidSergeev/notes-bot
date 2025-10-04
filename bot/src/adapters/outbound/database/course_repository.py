import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator
from src.core.application.ports.outbound.database import CourseRepository, SubjectRepository
from src.core.domain.models import Course
from src.core.domain.common.enums import CourseYear
from .models import Course as DBCourse


class SqlModelCourseRepository(CourseRepository):
    def __init__(self, session_factory: Callable[[], Generator[Session, None, None]], subject_repository: SubjectRepository):
        self._session_factory = session_factory
        self._subject_repository = subject_repository

    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        with self._session_factory() as session:
            session: Session
            db_course = session.get(DBCourse, course_id)
            if not db_course:
                return None
            subjects = [
                self._subject_repository.get_by_id(subject.id)
                for subject in db_course.subjects
            ]
            return Course(id=db_course.id, year=CourseYear(db_course.year), subjects=subjects)

    def get_by_year(self, year: CourseYear) -> Course | None:
        with self._session_factory() as session:
            session: Session
            statement = select(DBCourse).where(DBCourse.year == year.value)
            db_course = session.exec(statement).first()
            if not db_course:
                return None
            subjects = [
                self._subject_repository.get_by_id(subject.id)
                for subject in db_course.subjects
            ]
            return Course(id=db_course.id, year=year, subjects=subjects)

    def save(self, course: Course) -> None:
        # Save of subjects might be broken. Need testing
        with self._session_factory() as session:
            session: Session
            for subject in course.subjects:
                self._subject_repository.save(subject)
            db_subjects = [
                self.subject_repository.get_by_id(subject.id)
                for subject in course.subjects
            ]
            db_course = DBCourse(id=course.id, year=course.year.value, subjects=db_subjects)
            session.add(db_course)
            session.commit()

    def delete(self, course_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session
            db_course = session.get(DBCourse, course_id)
            if db_course:
                session.delete(db_course)
                session.commit()