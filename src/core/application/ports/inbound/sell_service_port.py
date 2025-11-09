import uuid
from typing import Protocol

from src.core.domain.models import Note


class SellServicePort(Protocol):
    def upload_note(self, title: str, price_rub: int, subject_id: uuid.UUID, file: bytes):
        raise NotImplementedError