import uuid
from sqlmodel import Session, select
from src.core.application.ports.outbound.database import NoteRepository
from src.core.domain.models import Note
from .models import Note as DBNote


class SqlModelNoteRepository(NoteRepository):
    def __init__(self, session: Session):
        self.session = session

    async def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        db_note = await self.session.get(DBNote, note_id)
        if not db_note:
            return None
        return Note(id=db_note.id, title=db_note.title)

    async def get_by_title(self, title: str) -> Note | None:
        statement = select(DBNote).where(DBNote.title == title)
        db_note = await self.session.exec(statement).first()
        if not db_note:
            return None
        return Note(id=db_note.id, title=db_note.title)

    async def save(self, note: Note) -> None:
        db_note = DBNote(id=note.id, title=note.title)
        self.session.add(db_note)
        await self.session.commit()

    async def delete(self, note_id: uuid.UUID) -> None:
        db_note = await self.session.get(DBNote, note_id)
        if db_note:
            self.session.delete(db_note)
            await self.session.commit()