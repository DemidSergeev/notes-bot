import uuid
from src.core.application.ports.outbound.persistence import PurchaseReceiptRepositoryPort
from src.core.domain.models import PurchaseReceipt, Note, Buyer


class PurchaseReceiptService:
    def __init__(self, purchase_receipt_repo: PurchaseReceiptRepositoryPort):
        self._purchase_receipt_repo = purchase_receipt_repo

    def create(self, note: Note, buyer: Buyer, payment_details: str) -> PurchaseReceipt:
        purchase_receipt = PurchaseReceipt(
            note=note,
            buyer=buyer,
            payment_details=payment_details
        )

        self._purchase_receipt_repo.save(purchase_receipt)
        return purchase_receipt

    def get_by_id(self, purchase_receipt_id: uuid.UUID) -> PurchaseReceipt | None:
        return self._purchase_receipt_repo.get_by_id(purchase_receipt_id)
    
    def get_by_buyer_id(self, buyer_id: int) -> PurchaseReceipt | None:
        return self._purchase_receipt_repo.get_by_buyer_id(buyer_id)
    
    def delete(self, purchase_receipt_id: uuid.UUID) -> None:
        self._purchase_receipt_repo.delete(purchase_receipt_id)