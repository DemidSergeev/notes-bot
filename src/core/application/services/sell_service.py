import logging

from ..ports.inbound import SellServicePort
from ..ports.outbound.persistence import NoteRepositoryPort
from ..ports.outbound.storage import NoteStoragePort
from src.core.domain.models import Note

logger = logging.getLogger(__name__)


class SellService(SellServicePort):
    def __init__(self, note_repo: NoteRepositoryPort, note_storage: NoteStoragePort):
        self._note_repo = note_repo
        self._note_storage = note_storage

    def upload_note(self, title, price_rub, subject_id, file):
        note = Note(
            title=title,
            price_rub=price_rub
        )
        file.seek(0)
        self._note_repo.save(note, subject_id)
        self._note_storage.save(note, file)
        logger.debug("Note %s (UUID %s) uploaded", title, note.id)
