from dataclasses import dataclass

from .base_model import BaseModel
from .note import Note


@dataclass
class Subject(BaseModel):
    name: str
    notes: list[Note]