from typing import Protocol

from src.core.domain.models import Course, Note, Buyer, PurchaseReceipt

class CourseCommandsPort(Protocol):
    def list_courses(self) -> list[Course]:
        raise NotImplementedError

    def submit_purchase_request(self, note: Note, buyer: Buyer) -> PurchaseReceipt:
        raise NotImplementedError