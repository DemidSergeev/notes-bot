from ..ports.inbound import PurchaseServicePort
from .data import CourseService, PurchaseReceiptService
from ..ports.outbound import PaymentDetailsProviderPort


class PurchaseService(PurchaseServicePort):
    def __init__(
        self,
        course_service: CourseService,
        purchase_receipt_service: PurchaseReceiptService,
        payment_details_provider: PaymentDetailsProviderPort
    ):
        self._course_service = course_service
        self._purchase_receipt_service = purchase_receipt_service
        self._payment_details_provider = payment_details_provider

    def get_courses(self):
        return self._course_service.get_all()

    def generate_purchase_receipt(self, note, buyer):
        return self._purchase_receipt_service.create(note=note, buyer=buyer, payment_details=self._payment_details_provider.get())