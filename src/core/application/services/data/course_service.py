import uuid
from src.core.application.ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort
from src.core.domain.models import Course, Subject
from src.core.domain.common.enums import CourseYear


class CourseService:
    def __init__(self, course_repo: CourseRepositoryPort, subject_repo: SubjectRepositoryPort):
        self._course_repo = course_repo
        self._subject_repo = subject_repo

    def create(self, year: CourseYear, subjects: list[Subject] = []) -> Course:
        course = Course(
            year=year,
            subjects=subjects
        )

        self._course_repo.save(course)
        for subject in subjects:
            self._subject_repo.save(subject, course.id)

        return course

    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        return self._course_repo.get_by_id(course_id)
    
    def get_by_year(self, year: CourseYear) -> list[Course]:
        return self._course_repo.get_by_year(year)
    
    def get_all(self) -> list[Course]:
        return self._course_repo.get_all()

    def delete(self, course_id: uuid.UUID) -> None:
        self._course_repo.delete(course_id)