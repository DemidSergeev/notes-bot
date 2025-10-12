from typing import Protocol

from src.core.domain.models import Course, Note, Buyer, PurchaseReceipt

class PurchaseServicePort(Protocol):
    def get_courses(self) -> list[Course]:
        raise NotImplementedError

    def generate_purchase_receipt(self, note: Note, buyer: Buyer) -> PurchaseReceipt:
        raise NotImplementedError