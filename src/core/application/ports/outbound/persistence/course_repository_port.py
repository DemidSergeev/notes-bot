import uuid
from typing import Protocol

from src.core.domain.models import Course
from src.core.domain.common.enums import CourseYear


class CourseRepositoryPort(Protocol):
    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        ...

    def get_by_year(self, year: CourseYear) -> Course | None:
        ...

    def get_all(self) -> list[Course]:
        ...

    def save(self, course: Course) -> None:
        ...

    def delete(self, course_id: uuid.UUID) -> None:
        ...