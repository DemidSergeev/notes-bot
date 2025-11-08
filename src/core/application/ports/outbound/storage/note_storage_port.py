import uuid
from typing import Protocol

from src.core.domain.models import Note


class NoteStoragePort(Protocol):
    def get_by_id(note_id: uuid.UUID) -> bytes | None:
        raise NotImplementedError

    def get_url(note_id: uuid.UUID) -> str | None:
        raise NotImplementedError

    def save(note: Note, file: bytes) -> None:
        raise NotImplementedError
    
    def delete(note_id: uuid.UUID) -> None:
        raise NotImplementedError