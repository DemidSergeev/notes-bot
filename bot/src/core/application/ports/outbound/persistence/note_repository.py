import uuid
from typing import Protocol

from src.core.domain.models import Note


class NoteRepository(Protocol):
    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        raise NotImplementedError

    def get_by_title(self, title: str) -> Note | None:
        raise NotImplementedError

    def save(self, note: Note) -> None:
        raise NotImplementedError

    def delete(self, note_id: uuid.UUID) -> None:
        raise NotImplementedError