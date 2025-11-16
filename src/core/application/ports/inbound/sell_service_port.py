import uuid
from io import BytesIO
from typing import Protocol


class SellServicePort(Protocol):
    def upload_note(self, title: str, price_rub: int, subject_id: uuid.UUID, file: BytesIO):
        raise NotImplementedError