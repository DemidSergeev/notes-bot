import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator

from src.core.application.ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort
from src.core.domain.models import Course
from .models import Course as DBCourse
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

            db_course = session.get(DBCourse, course_id)

            if not db_course:
                return None

            subjects = [
                self._subject_repository.get_by_id(subject.id)
                for subject in db_course.subjects
            ]

            return Course(
                id=db_course.id,
                year=CourseYear(db_course.year),
                subjects=subjects
            )

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

    def get_all(self) -> list[Course]:
        with self._session_factory() as session:
            session: Session

            statement = select(DBCourse)
            db_courses = session.exec(statement).all()

            courses = []
            for db_course in db_courses:
                subjects = [
                    self._subject_repository.get_by_id(subject.id)
                    for subject in db_course.subjects
                ]

                course = Course(
                    id=db_course.id,
                    year=CourseYear(db_course.year),
                    subjects=subjects
                )
                courses.append(course)

            return courses
 
    def save(self, course: Course) -> None:
        # Save of subjects might be broken. Need testing
        with self._session_factory() as session:
            session: Session

            for subject in course.subjects:
                self._subject_repository.save(subject)

            db_course = DBCourse(id=course.id, year=course.year.value, subjects=course.subjects)

            session.add(db_course)
            session.commit()

    def delete(self, course_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_course = session.get(DBCourse, course_id)

            if db_course:
                session.delete(db_course)
                session.commit()