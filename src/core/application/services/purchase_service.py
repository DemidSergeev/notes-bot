from ..ports.inbound import PurchaseServicePort
from ..ports.outbound.persistence import CourseRepositoryPort, SubjectRepositoryPort, NoteRepositoryPort, PurchaseReceiptRepositoryPort
from ..ports.outbound import PaymentDetailsProviderPort
from src.core.domain.models import PurchaseReceipt


class PurchaseService(PurchaseServicePort):
    def __init__(
        self,
        course_repo: CourseRepositoryPort,
        subject_repo: SubjectRepositoryPort,
        note_repo: NoteRepositoryPort,
        purchase_receipt_repo: PurchaseReceiptRepositoryPort,
        payment_details_provider: PaymentDetailsProviderPort
    ):
        self._course_repo = course_repo
        self._subject_repo = subject_repo
        self._note_repo = note_repo
        self._purchase_receipt_repo = purchase_receipt_repo
        self._payment_details_provider = payment_details_provider

    def get_courses(self):
        return self._course_repo.get_all()

    def get_subjects(self, course_year):
        course = self._course_repo.get_by_year(course_year)

        if not course:
            raise ValueError(f"Course for year {course_year} does not exist.")

        return course.subjects

    def get_notes(self, subject_id):
        subject = self._subject_repo.get_by_id(subject_id)

        if not subject:
            raise ValueError(f"Subject with id {subject_id} does not exist.")

        return subject.notes

    def generate_purchase_receipt(self, note_id, buyer):
        note = self._note_repo.get_by_id(note_id)

        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")

        purchase_receipt = PurchaseReceipt(
            note=note,
            payment_details=self._payment_details_provider.get(),
            buyer=buyer
        )

        self._purchase_receipt_repo.save(purchase_receipt)

        return purchase_receipt