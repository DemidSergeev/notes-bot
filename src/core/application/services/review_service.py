import logging

from ..ports.inbound import ReviewServicePort
from ..ports.outbound.persistence import NoteRepositoryPort
from ..ports.outbound.storage import NoteStoragePort


logger = logging.getLogger(__name__)

class ReviewService(ReviewServicePort):
    def __init__(
        self, 
        note_repo: NoteRepositoryPort,
        note_storage: NoteStoragePort,
    ):
        self.note_repo = note_repo
        self.note_storage = note_storage

    def approve_note(self, note_id) -> None:
        note = self.note_repo.get_by_id(note_id)
        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")
        
        note.is_approved = True
        self.note_repo.save(note, subject_id=None)  # subject_id is not updated
        logging.debug("Note %s (UUID %s) approved", note.title, note.id)

    def reject_note(self, note_id, reason: str) -> None:
        note = self.note_repo.get_by_id(note_id)
        if not note:
            raise ValueError(f"Note with id {note_id} does not exist.")

        self.note_storage.delete(note.id)
        self.note_repo.delete(note.id)
        logging.debug("Note %s (UUID %s) rejected and deleted", note.title, note.id)