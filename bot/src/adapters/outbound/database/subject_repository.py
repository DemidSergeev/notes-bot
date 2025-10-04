import uuid
from sqlmodel import Session, select
from collections.abc import Callable, Generator
from src.core.application.ports.outbound.database import SubjectRepository, NoteRepository
from src.core.domain.models import Subject
from src.infrastructure.database import SessionFactory
from .models import Subject as DBSubject


class SqlModelSubjectRepository(SubjectRepository):
    def __init__(self, session_factory: Callable[[], Generator[Session, None, None]], note_repository: NoteRepository):
        self._session_factory = session_factory
        self._note_repository = note_repository

    def get_by_id(self, subject_id: uuid.UUID) -> Subject | None:
        with self._session_factory() as session:
            session: Session
            db_subject = session.get(DBSubject, subject_id)
            if not db_subject:
                return None
            notes = [
                self._note_repository.get_by_id(note.id)
                for note in db_subject.notes
        ]
        return Subject(id=db_subject.id, name=db_subject.name, notes=notes)

    def get_by_name(self, name):
        with self._session_factory() as session:
            session: Session
            statement = select(DBSubject).where(DBSubject.name == name)
            db_subject = session.exec(statement).first()
            if not db_subject:
                return None
            notes = [
                self._note_repository.get_by_id(note.id)
            for note in db_subject.notes
        ]
        return Subject(id=db_subject.id, name=db_subject.name, notes=notes)

    def save(self, subject: Subject) -> None:
        # Save of notes might be broken. Need testing
        with self._session_factory() as session:
            session: Session
            for note in subject.notes:
                self._note_repository.save(note)
            db_notes = [
                self._note_repository.get_by_id(note.id)
                for note in subject.notes
            ]
            db_subject = DBSubject(id=subject.id, name=subject.name, notes=db_notes)
            session.add(db_subject)
            session.commit()

    def delete(self, subject_id: uuid.UUID) -> None:
        with self._session_factory() as session:
            session: Session
            db_subject = session.get(DBSubject, subject_id)
            if db_subject:
                session.delete(db_subject)
            session.commit()