import uuid
from typing import Protocol


class ReviewServicePort(Protocol):
    def approve_note(self, note_id: uuid.UUID) -> None:
        ...

    def reject_note(self, note_id: uuid.UUID, reason: str) -> None:
        ...