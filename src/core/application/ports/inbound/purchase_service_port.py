import uuid
from typing import Protocol

from src.core.domain.models import Course, Subject, Note, Buyer, PurchaseReceipt
from src.core.domain.common.enums import CourseYear

class PurchaseServicePort(Protocol):
    def get_courses(self) -> list[Course]:
        raise NotImplementedError

    def get_subjects(self, course_year: CourseYear) -> list[Subject]:
        raise NotImplementedError

    def get_notes(self, subject_id: uuid.UUID) -> list[Note]:
        raise NotImplementedError

    def generate_purchase_receipt(self, note_id: uuid.UUID, buyer: Buyer) -> PurchaseReceipt:
        raise NotImplementedError