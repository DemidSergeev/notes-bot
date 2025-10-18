import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator

from src.core.application.ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort
from src.core.domain.models import Course, Subject, Note
from .models import Course as DbCourse
from src.core.domain.common.enums import CourseYear


class SqlModelCourseRepository(CourseRepositoryPort):
    def __init__(
            self,
            session_factory: Callable[[], Generator[Session, None, None]],
            subject_repository: SubjectRepositoryPort
        ):
        self._session_factory = session_factory
        self._subject_repository = subject_repository

    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        with self._session_factory() as session:
            session: Session

            db_course = session.get(DbCourse, course_id)

            if not db_course:
                return None

            subjects = self._get_subjects(db_course)

            return Course(
                id=db_course.id,
                year=CourseYear(db_course.year),
                subjects=subjects
            )

    def get_by_year(self, year: CourseYear) -> Course | None:
        with self._session_factory() as session:
            session: Session

            statement = select(DbCourse).where(DbCourse.year == year.value)
            db_course = session.exec(statement).first()

            if not db_course:
                return None

            subjects = self._get_subjects(db_course)

            return Course(id=db_course.id, year=year, subjects=subjects)

    def get_all(self) -> list[Course]:
        with self._session_factory() as session:
            session: Session

            statement = select(DbCourse)
            db_courses = session.exec(statement).all()

            courses = []
            for db_course in db_courses:
                subjects = self._get_subjects(db_course)

                course = Course(
                    id=db_course.id,
                    year=CourseYear(db_course.year),
                    subjects=subjects
                )
                courses.append(course)

            return courses
 
    def save(self, course: Course) -> None:
        with self._session_factory() as session:
            session: Session

            db_course = DbCourse(id=course.id, year=course.year.value)

            session.add(db_course)
            session.commit()

    def delete(self, course_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_course = session.get(DbCourse, course_id)

            if db_course:
                session.delete(db_course)
                session.commit()

    def _get_subjects(self, db_course: DbCourse) -> list[Subject]:
        subjects = [
            Subject(
                id=db_subject.id,
                name=db_subject.name,
                notes=[
                    Note(
                        id=db_note.id,
                        title=db_note.title,
                        price_rub=db_note.price_rub
                    )
                    for db_note in db_subject.notes
                ]
            )
            for db_subject in db_course.subjects
        ]

        return subjects