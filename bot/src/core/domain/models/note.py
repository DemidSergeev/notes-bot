from dataclasses import dataclass

from .base_model import BaseModel

@dataclass
class Note(BaseModel):
    title: str