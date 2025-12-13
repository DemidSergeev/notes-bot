import uuid
from typing import Protocol

from src.core.domain.models import Note


class NoteRepositoryPort(Protocol):
    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        ...

    def get_by_title(self, title: str) -> Note | None:
        ...

    def get_approved_by_subject_id(self, subject_id: uuid.UUID) -> list[Note]:
        ...

    def get_not_approved(self) -> list[Note]:
        ...

    def save(self, note: Note, subject_id: uuid.UUID) -> None:
        ...

    def delete(self, note_id: uuid.UUID) -> None:
        ...