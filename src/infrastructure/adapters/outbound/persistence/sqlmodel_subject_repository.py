import logging
import uuid
from sqlmodel import Session, select
from typing import Callable, Generator

from src.core.application.ports.outbound.persistence import SubjectRepositoryPort, NoteRepositoryPort
from src.core.domain.models import Subject, Note
from .models import Subject as DbSubject


logger = logging.getLogger(__name__)

class SqlModelSubjectRepository(SubjectRepositoryPort):
    def __init__(self, session_factory: Callable[[], Generator[Session, None, None]], note_repository: NoteRepositoryPort):
        self._session_factory = session_factory
        self._note_repository = note_repository

    def get_by_id(self, subject_id: uuid.UUID) -> Subject | None:
        with self._session_factory() as session:
            session: Session

            db_subject = session.get(DbSubject, subject_id)

            if not db_subject:
                return None

            notes = self._get_notes(db_subject)

            return Subject(
                id=db_subject.id,
                name=db_subject.name,
                notes=notes
            )
        
    def get_by_name(self, name: str) -> Subject | None:
        with self._session_factory() as session:
            session: Session

            statement = select(DbSubject).where(DbSubject.name == name)
            db_subject = session.exec(statement).first()

            if not db_subject:
                return None

            notes = self._get_notes(db_subject)

            return Subject(
                id=db_subject.id,
                name=db_subject.name,
                notes=notes
            )
        
    def save(self, subject: Subject, course_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_subject = session.get(DbSubject, subject.id)
            if db_subject:
                db_subject.name = subject.name
                db_subject.course_id = course_id
                logger.debug("Subject %s (UUID %s) updated in DB", subject.name, subject.id)
            else:
                db_subject = DbSubject(
                    id=subject.id,
                    name=subject.name,
                    course_id=course_id
                )
                session.add(db_subject)
                logger.debug("Subject %s (UUID %s) added to DB", subject.name, subject.id)
            session.commit()

            for note in subject.notes:
                self._note_repository.save(note, subject.id)


    def delete(self, subject_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_subject = session.get(DbSubject, subject_id)

            if db_subject:
                session.delete(db_subject)
                session.commit()
                logger.debug("Subject %s (UUID %s) deleted from DB", db_subject.name, db_subject.id)


    def _get_notes(self, db_subject: DbSubject) -> list[Note]:
        notes = [
            Note(
                id=db_note.id,
                title=db_note.title,
            )
            for db_note in db_subject.notes
        ]

        return notes