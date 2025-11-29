import logging
import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator

from src.core.application.ports.outbound.persistence import NoteRepositoryPort
from src.core.domain.models import Note
from .models import Note as DbNote


logger = logging.getLogger(__name__)

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
                is_approved=db_note.is_approved
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
                is_approved=db_note.is_approved
            )

    def get_approved_by_subject_id(self, subject_id: uuid.UUID) -> list[Note]:
        with self._session_factory() as session:
            session: Session

            statement = select(DbNote).where(DbNote.is_approved.is_(True), DbNote.subject_id == subject_id)
            db_notes = session.exec(statement).all()
            logger.debug("Retrieved %d approved notes with subject_id %s from DB", len(db_notes), subject_id)

            return [
                Note(
                    id=db_note.id,
                    title=db_note.title,
                    is_approved=db_note.is_approved
                )
                for db_note in db_notes
            ]

    def get_not_approved(self) -> list[Note]:
        with self._session_factory() as session:
            session: Session

            statement = select(DbNote).where(DbNote.is_approved.is_(False))
            db_notes = session.exec(statement).all()
            logger.debug("Retrieved %d not approved notes from DB", len(db_notes))

            return [
                Note(
                    id=db_note.id,
                    title=db_note.title,
                    is_approved=db_note.is_approved
                )
                for db_note in db_notes
            ]

    def save(self, note: Note, subject_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_note = session.get(DbNote, note.id)
            if db_note:
                db_note.id = note.id
                db_note.title = note.title
                db_note.is_approved = note.is_approved
                if subject_id:
                    db_note.subject_id = subject_id
                logger.debug("Note %s (UUID %s) updated in DB", note.title, note.id)
            else:
                db_note = DbNote(
                    id=note.id,
                    title=note.title,
                    is_approved=note.is_approved,
                    subject_id=subject_id
                )
                session.add(db_note)
                logger.debug("Note %s (UUID %s) added to DB", note.title, note.id)

            session.commit()

    def delete(self, note_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_note = session.get(DbNote, note_id)

            if db_note:
                session.delete(db_note)
                session.commit()
                logger.debug("Note %s (UUID %s) deleted from DB", db_note.title, db_note.id)