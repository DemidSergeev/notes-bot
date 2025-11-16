import logging

from ..ports.inbound import PurchaseServicePort
from ..ports.outbound.persistence import NoteRepositoryPort, PurchaseReceiptRepositoryPort
from ..ports.outbound import PaymentDetailsProviderPort
from src.core.domain.models import PurchaseReceipt


logger = logging.getLogger(__name__)

class PurchaseService(PurchaseServicePort):
    def __init__(
        self,
        note_repo: NoteRepositoryPort,
        purchase_receipt_repo: PurchaseReceiptRepositoryPort,
        payment_details_provider: PaymentDetailsProviderPort
    ):
        self._note_repo = note_repo
        self._purchase_receipt_repo = purchase_receipt_repo
        self._payment_details_provider = payment_details_provider

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
        logger.debug("Purchase receipt for buyer %s (ext. ID %s) and note %s (UUID %s) generated", buyer.name, buyer.external_id, note.title, note.id)

        return purchase_receipt