from io import BytesIO
import uuid
from typing import Protocol

from src.core.domain.models import Course, Subject, Note
from src.core.domain.common.enums import CourseYear


class DataServicePort(Protocol):
    # Get entities
    def get_courses(self) -> list[Course]:
        ...

    def get_subjects(self, course_year: CourseYear) -> list[Subject]:
        ...

    def get_notes(self, subject_id: uuid.UUID) -> list[Note]:
        ...

    def get_approved_notes_by_subject_id(self, subject_id: uuid.UUID) -> list[Note]:
        ...

    def get_not_approved_notes(self) -> list[Note]:
        ...

    def get_note_by_id(self, note_id: uuid.UUID) -> Note | None:
        ...

    def get_note_file(self, note_id: uuid.UUID) -> str | None:
        ...

    def get_note_url(self, note_id: uuid.UUID) -> str | None:
        ...

    # Create/update entities
    def add_subject(self, course_year: CourseYear, name: str) -> Subject:
        ...

    def upload_note(self, title: str, subject_id: uuid.UUID, file: BytesIO) -> None:
        ...

    # Delete entities
    def delete_subject(self, subject_id: uuid.UUID) -> None:
        ...

    def delete_note(self, note_id: uuid.UUID) -> None:
        ...