from dataclasses import dataclass, field

from .base_model import BaseModel
from .note import Note


@dataclass
class Subject(BaseModel):
    name: str
    notes: list[Note] = field(default_factory=list)
