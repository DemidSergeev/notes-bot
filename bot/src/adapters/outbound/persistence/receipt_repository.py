import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator
from src.core.application.ports.outbound.persistence import ReceiptRepository, NoteRepository
from src.core.domain.models import Receipt
from .models import Receipt as DBReceipt


class SqlModelReceiptRepository(ReceiptRepository):
    def __init__(self, session_factory: Callable[[], Generator[Session, None, None]], note_repository: NoteRepository):
        self._session_factory = session_factory
        self._note_repository = note_repository

    def get_by_id(self, receipt_id: uuid.UUID) -> Receipt | None:
        with self._session_factory() as session:
            session: Session

            db_receipt = session.get(DBReceipt, receipt_id)
            if not db_receipt:
                return None

            note = self._note_repository.get_by_id(db_receipt.note.id)

            return Receipt(
                id=db_receipt.id,
                buyer_id=db_receipt.buyer_id,
                buyer_name=db_receipt.buyer_name,
                payment_credentials=db_receipt.payment_credentials,
                price_rub=db_receipt.price_rub,
                note=note
                )

    def get_by_buyer_id(self, buyer_id: int) -> Receipt | None:
        with self._session_factory() as session:
            session: Session

            statement = select(DBReceipt).where(DBReceipt.buyer_id == buyer_id)
            db_receipt = session.exec(statement).first()
            if not db_receipt:
                return None

            note = self._note_repository.get_by_id(db_receipt.note.id)

            return Receipt(
                id=db_receipt.id,
                buyer_id=db_receipt.buyer_id,
                buyer_name=db_receipt.buyer_name,
                payment_credentials=db_receipt.payment_credentials,
                price_rub=db_receipt.price_rub,
                note=note
            )

    def save(self, receipt: Receipt) -> None:
        # Save of receipts might be broken. Need testing
        with self._session_factory() as session:
            session: Session

            db_receipt = DBReceipt(
                id=receipt.id,
                buyer_id=receipt.buyer_id,
                buyer_name=receipt.buyer_name,
                payment_credentials=receipt.payment_credentials,
                price_rub=receipt.price_rub,
                note=receipt.note
            )
            session.add(db_receipt)
            session.commit()

    def delete(self, receipt_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_receipt = session.get(DBReceipt, receipt_id)
            if db_receipt:
                session.delete(db_receipt)
                session.commit()