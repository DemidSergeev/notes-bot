import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator
from src.core.application.ports.outbound.persistence import NoteRepository
from src.core.domain.models import Note
from .models import Note as DBNote


class SqlModelNoteRepository(NoteRepository):
    def __init__(self, session_factory: Callable[[], Generator[Session, None, None]]):
        self._session_factory = session_factory

    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        with self._session_factory() as session:
            session: Session

            db_note = session.get(DBNote, note_id)

            if not db_note:
                return None

            return Note(id=db_note.id, title=db_note.title)

    def get_by_title(self, title: str) -> Note | None:
        with self._session_factory() as session:
            session: Session

            statement = select(DBNote).where(DBNote.title == title)
            db_note = session.exec(statement).first()

            if not db_note:
                return None

            return Note(id=db_note.id, title=db_note.title)

    def save(self, note: Note) -> None:
        with self._session_factory() as session:
            session: Session

            db_note = DBNote(id=note.id, title=note.title)

            session.add(db_note)
            session.commit()

    def delete(self, note_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_note = session.get(DBNote, note_id)

            if db_note:
                session.delete(db_note)

            session.commit()