import uuid
from typing import Protocol

from src.core.domain.models import Course
from src.core.domain.common.enums import CourseYear


class CourseRepositoryPort(Protocol):
    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        raise NotImplementedError

    def get_by_year(self, year: CourseYear) -> Course | None:
        raise NotImplementedError

    def get_all(self) -> list[Course]:
        raise NotImplementedError

    def save(self, course: Course) -> None:
        raise NotImplementedError

    def delete(self, course_id: uuid.UUID) -> None:
        raise NotImplementedError