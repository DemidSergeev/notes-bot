import uuid
from io import BytesIO
from typing import Protocol

from src.core.domain.models import Note


class NoteStoragePort(Protocol):
    def get_by_id(self, note_id: uuid.UUID) -> bytes | None:
        ...

    def get_url(self, note_id: uuid.UUID, note_title: str) -> str | None:
        ...

    def save(self, note: Note, file: BytesIO) -> None:
        ...
    
    def delete(self, note_id: uuid.UUID) -> None:
        ...