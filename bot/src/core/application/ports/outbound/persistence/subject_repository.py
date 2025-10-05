import uuid
from typing import Protocol

from src.core.domain.models import Subject


class SubjectRepository(Protocol):
    def get_by_id(self, subject_id: uuid.UUID) -> Subject | None:
        raise NotImplementedError

    def get_by_name(self, name: str) -> Subject | None:
        raise NotImplementedError

    def save(self, subject: Subject) -> None:
        raise NotImplementedError

    def delete(self, subject_id: uuid.UUID) -> None:
        raise NotImplementedError