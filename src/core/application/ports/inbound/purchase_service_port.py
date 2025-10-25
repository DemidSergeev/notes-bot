import uuid
from typing import Protocol

from src.core.domain.models import Buyer, PurchaseReceipt


class PurchaseServicePort(Protocol):
    def generate_purchase_receipt(self, note_id: uuid.UUID, buyer: Buyer) -> PurchaseReceipt:
        raise NotImplementedError