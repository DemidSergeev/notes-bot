import uuid
from ..ports.outbound.persistence import CourseRepository, SubjectRepository, NoteRepository, ReceiptRepository
from src.core.domain.common.enums import CourseYear
from src.core.domain.models import Course, Receipt

class BuyNotesService:
    def __init__(
        self,
        course_repository: CourseRepository,
        subject_repository: SubjectRepository,
        note_repository: NoteRepository,
        receipt_repository: ReceiptRepository,
    ):
        self._course_repository = course_repository
        self._subject_repository = subject_repository
        self._note_repository = note_repository
        self._receipt_repository = receipt_repository

    def get_courses(self) -> list[Course]:
        """Return courses list"""
        courses = []

        for year in CourseYear:
            course = self._course_repository.get_by_year(year)
            if course:
                courses.append(course)

        return courses

    def create_purchase_receipt(self, buyer_id: int, buyer_name: str, payment_credentials: str, price_rub: int, note_id: uuid.UUID) -> Receipt | None:
        """Create and return a receipt for purchasing note"""
        note = self._note_repository.get_by_id(note_id)

        if not note:
            # Handle note not found
            return None

        # Save receipt
        receipt = Receipt(buyer_id=buyer_id, buyer_name=buyer_name, payment_credentials=payment_credentials, price_rub=price_rub, note=note)
        self._receipt_repository.save(receipt)
        return receipt