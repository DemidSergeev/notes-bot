from ..ports.inbound import SellServicePort
from ..ports.outbound.persistence import NoteRepositoryPort
from ..ports.outbound.storage import NoteStoragePort


class SellService(SellServicePort):
    def __init__(self, note_repo: NoteRepositoryPort, note_storage: NoteStoragePort):
        self._note_repo = note_repo
        self._note_storage = note_storage

    def upload_note(self, note, subject_id, file):
        self._note_repo.save(note, subject_id)
        self._note_storage.save(note, file)