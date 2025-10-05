import uuid
from typing import Protocol

from src.core.domain.models import Receipt


class ReceiptRepository(Protocol):
    def get_by_id(self, check_id: uuid.UUID) -> Receipt | None:
        raise NotImplementedError

    def get_by_buyer_id(self, buyer_id: int) -> Receipt | None:
        raise NotImplementedError

    def save(self, check: Receipt) -> None:
        raise NotImplementedError

    def delete(self, check_id: uuid.UUID) -> None:
        raise NotImplementedError