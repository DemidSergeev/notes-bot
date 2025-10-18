import uuid
from sqlmodel import Session, select
from typing import Callable, Generator

from src.core.application.ports.outbound.persistence import SubjectRepositoryPort, NoteRepositoryPort
from src.core.domain.models import Subject, Note
from .models import Subject as DbSubject


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

            db_subject = DbSubject(
                id=subject.id,
                name=subject.name,
                course_id=course_id
            )

            session.add(db_subject)
            session.commit()

    def delete(self, subject_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session

            db_subject = session.get(DbSubject, subject_id)

            if db_subject:
                session.delete(db_subject)
                session.commit()


    def _get_notes(self, db_subject: DbSubject) -> list[Note]:
        notes = [
            Note(
                id=db_note.id,
                title=db_note.title,
                price_rub=db_note.price_rub
            )
            for db_note in db_subject.notes
        ]

        return notes