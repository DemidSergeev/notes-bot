import uuid
from typing import Protocol

from src.core.domain.models import Course
from src.core.domain.common.enums import CourseYear


class CourseRepository(Protocol):
    async def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        raise NotImplementedError

    async def get_by_year(self, year: CourseYear) -> Course | None:
        raise NotImplementedError

    async def save(self, course: Course) -> None:
        raise NotImplementedError

    async def delete(self, course_id: uuid.UUID) -> None:
        raise NotImplementedError