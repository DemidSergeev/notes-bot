import uuid
from src.core.application.ports.outbound.persistence import NoteRepositoryPort, SubjectRepositoryPort
from src.core.domain.models import Note


class NoteService:
    def __init__(self, note_repo: NoteRepositoryPort, subject_repo: SubjectRepositoryPort):
        self._note_repo = note_repo
        self._subject_repo = subject_repo

    def create(self, title: str, price_rub: int, subject_id: uuid.UUID) -> Note:
        if not self._subject_repo.get_by_id(subject_id):
            raise ValueError(f"Subject with id {subject_id} does not exist.")
        
        note = Note(
            title=title,
            price_rub=price_rub
        )
        self._note_repo.save(note, subject_id)
        return note

    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        return self._note_repo.get_by_id(note_id)

    def get_by_title(self, title: str) -> Note | None:
        return self._note_repo.get_by_title(title)

    def delete(self, note_id: uuid.UUID) -> None:
        self._note_repo.delete(note_id)

    