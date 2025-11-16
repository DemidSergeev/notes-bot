import logging
import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator

from src.core.application.ports.outbound.persistence import PurchaseReceiptRepositoryPort
from src.core.domain.models import PurchaseReceipt, Note, User
from .models import (
    PurchaseReceipt as DbPurchaseReceipt,
)


logger = logging.getLogger(__name__)

class SqlModelPurchaseReceiptRepository(PurchaseReceiptRepositoryPort):
    def __init__(
            self,
            session_factory: Callable[[], Generator[Session, None, None]],
        ):
        self._session_factory = session_factory

    def get_by_id(self, purchase_receipt_id: uuid.UUID) -> PurchaseReceipt | None:
        with self._session_factory() as session:
            session: Session

            db_purchase_receipt = session.get(DbPurchaseReceipt, purchase_receipt_id)

            if not db_purchase_receipt:
                return None

            return self._create_domain_purchase_receipt(db_purchase_receipt)

    def get_by_buyer_id(self, buyer_id: int) -> PurchaseReceipt | None:
        with self._session_factory() as session:
            session: Session

            statement = select(DbPurchaseReceipt).where(DbPurchaseReceipt.buyer_id == buyer_id)
            db_purchase_receipt = session.exec(statement).first()

            if not db_purchase_receipt:
                return None

            return self._create_domain_purchase_receipt(db_purchase_receipt)
            
    def save(self, purchase_receipt: PurchaseReceipt) -> None:
        with self._session_factory() as session:
            session: Session

            db_purchase_receipt = DbPurchaseReceipt(
                id=purchase_receipt.id,
                buyer_id=purchase_receipt.buyer.external_id,
                buyer_name=purchase_receipt.buyer.name,
                payment_details=purchase_receipt.payment_details,
                note_id=purchase_receipt.note.id
            )

            session.add(db_purchase_receipt)
            session.commit()
            logger.debug("Purchase receipt (UUID %s) saved in DB", purchase_receipt.id)
            logger.debug(
                "Purchase receipt details: buyer %s (ext. ID %s), note %s (UUID %s)",
                purchase_receipt.buyer.name,
                purchase_receipt.buyer.external_id,
                purchase_receipt.note.title,
                purchase_receipt.note.id
            )

    def delete(self, purchase_receipt_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_purchase_receipt = session.get(DbPurchaseReceipt, purchase_receipt_id)

            if db_purchase_receipt:
                session.delete(db_purchase_receipt)
                session.commit()
                logger.debug("Purchase receipt (UUID %s) deleted from DB", db_purchase_receipt.id)

    def _create_domain_purchase_receipt(self, db_purchase_receipt: DbPurchaseReceipt) -> PurchaseReceipt:
        db_note = db_purchase_receipt.note
        note = Note(id=db_note.id, title=db_note.title, price_rub=db_note.price_rub)
        buyer = User(external_id=db_purchase_receipt.buyer_id, name=db_purchase_receipt.buyer_name)

        return PurchaseReceipt(
            id=db_purchase_receipt.id,
            note=note,
            buyer=buyer
        )