import uuid
from dataclasses import dataclass, field

from ..common.facades import uuid7


@dataclass
class BaseModel:
    id: uuid.UUID = field(default_factory=uuid7)