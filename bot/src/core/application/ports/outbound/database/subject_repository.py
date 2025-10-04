import uuid
from typing import Protocol

from src.core.domain.models import Subject


class SubjectRepository(Protocol):
    async def get_by_id(self, subject_id: uuid.UUID) -> Subject | None:
        raise NotImplementedError

    async def get_by_name(self, name: str) -> Subject | None:
        raise NotImplementedError

    async def save(self, subject: Subject) -> None:
        raise NotImplementedError

    async def delete(self, subject_id: uuid.UUID) -> None:
        raise NotImplementedError