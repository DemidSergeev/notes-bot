import uuid
from sqlmodel import Session, select
from src.core.application.ports.outbound.database import SubjectRepository, NoteRepository
from src.core.domain.models import Subject
from .models import Subject as DBSubject


class SqlModelSubjectRepository(SubjectRepository):
    def __init__(self, session: Session, note_repository: NoteRepository):
        self.session = session
        self.note_repository = note_repository

    async def get_by_id(self, subject_id: uuid.UUID) -> Subject | None:
        db_subject = await self.session.get(DBSubject, subject_id)
        if not db_subject:
            return None
        notes = [
            await self.note_repository.get_by_id(note.id)
            for note in db_subject.notes
        ]
        return Subject(id=db_subject.id, name=db_subject.name, notes=notes)

    async def get_by_name(self, name):
        statement = select(DBSubject).where(DBSubject.name == name)
        db_subject = await self.session.exec(statement).first()
        if not db_subject:
            return None
        notes = [
            await self.note_repository.get_by_id(note.id)
            for note in db_subject.notes
        ]
        return Subject(id=db_subject.id, name=db_subject.name, notes=notes)

    async def save(self, subject: Subject) -> None:
        db_subject = DBSubject(id=subject.id, name=subject.name)
        self.session.add(db_subject)
        for note in subject.notes:
            await self.note_repository.save(note)
        await self.session.commit()

    async def delete(self, subject_id: uuid.UUID) -> None:
        db_subject = await self.session.get(DBSubject, subject_id)
        if db_subject:
            self.session.delete(db_subject)
            await self.session.commit()