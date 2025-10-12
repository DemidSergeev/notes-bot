import uuid
from typing import Protocol

from src.core.domain.models import PurchaseReceipt


class PurchaseReceiptRepositoryPort(Protocol):
    def get_by_id(self, check_id: uuid.UUID) -> PurchaseReceipt | None:
        raise NotImplementedError

    def get_by_buyer_id(self, buyer_id: int) -> PurchaseReceipt | None:
        raise NotImplementedError

    def save(self, purchase_receipt: PurchaseReceipt) -> None:
        raise NotImplementedError

    def delete(self, purchase_receipt_id: uuid.UUID) -> None:
        raise NotImplementedError