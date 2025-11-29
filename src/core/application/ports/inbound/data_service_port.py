import uuid
from typing import Protocol

from src.core.domain.models import Course, Subject, Note
from src.core.domain.common.enums import CourseYear


class DataServicePort(Protocol):
    # Get entities
    def get_courses(self) -> list[Course]:
        raise NotImplementedError

    def get_subjects(self, course_year: CourseYear) -> list[Subject]:
        raise NotImplementedError

    def get_notes(self, subject_id: uuid.UUID) -> list[Note]:
        raise NotImplementedError

    def get_approved_notes_by_subject_id(self, subject_id: uuid.UUID) -> list[Note]:
        raise NotImplementedError

    def get_not_approved_notes(self) -> list[Note]:
        raise NotImplementedError

    def get_note_file(self, note_id: uuid.UUID) -> str | None:
        raise NotImplementedError

    def get_note_url(self, note_id: uuid.UUID) -> str | None:
        raise NotImplementedError

    # Create/update entities
    def add_subject(self, course_year: CourseYear, name: str) -> Subject:
        raise NotImplementedError

    # Delete entities
    def delete_subject(self, subject_id: uuid.UUID) -> None:
        raise NotImplementedError

    def delete_note(self, note_id: uuid.UUID) -> None:
        raise NotImplementedError