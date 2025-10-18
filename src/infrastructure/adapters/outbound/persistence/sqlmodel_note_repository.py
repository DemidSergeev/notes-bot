import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator

from src.core.application.ports.outbound.persistence import NoteRepositoryPort
from src.core.domain.models import Note
from .models import Note as DbNote


class SqlModelNoteRepository(NoteRepositoryPort):
    def __init__(
            self,
            session_factory: Callable[[], Generator[Session, None, None]],
        ):
        self._session_factory = session_factory

    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        with self._session_factory() as session:
            session: Session

            db_note = session.get(DbNote, note_id)

            if not db_note:
                return None

            return Note(
                id=db_note.id,
                title=db_note.title,
                price_rub=db_note.price_rub
            ) 

    def get_by_title(self, title: str) -> Note | None:
        with self._session_factory() as session:
            session: Session

            statement = select(DbNote).where(DbNote.title == title)
            db_note = session.exec(statement).first()

            if not db_note:
                return None

            return Note(
                id=db_note.id,
                title=db_note.title,
                price_rub=db_note.price_rub
            )
 
    def save(self, note: Note) -> None:
        with self._session_factory() as session:
            session: Session

            db_note = DbNote(id=note.id, title=note.title, price_rub=note.price_rub)

            session.add(db_note)
            session.commit()

    def delete(self, note_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_note = session.get(DbNote, note_id)

            if db_note:
                session.delete(db_note)
                session.commit()