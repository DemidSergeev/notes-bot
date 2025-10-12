from ..ports.inbound import PurchaseServicePort
from ..ports.outbound.persistence import (
    CourseRepositoryPort,
    NoteRepositoryPort,
    PurchaseReceiptRepositoryPort
)
from ..ports.outbound import PaymentDetailsProviderPort
from src.core.domain.models import PurchaseReceipt


class PurchaseService(PurchaseServicePort):
    def __init__(
            self,
            course_repo: CourseRepositoryPort,
            note_repo: NoteRepositoryPort,
            purchase_receipt_repo: PurchaseReceiptRepositoryPort,
            payment_details_provider: PaymentDetailsProviderPort
    ):
        self._course_repo = course_repo
        self._note_repo = note_repo
        self._purchase_receipt_repo = purchase_receipt_repo
        self._payment_details_provider = payment_details_provider

    def get_courses(self):
        return self._course_repo.get_all()

    def generate_purchase_receipt(self, note, buyer):
        purchase_receipt = PurchaseReceipt(
            note=note,
            buyer=buyer,
            payment_details=self._payment_details_provider.get(),
        )

        self._purchase_receipt_repo.save(purchase_receipt)
        return purchase_receipt