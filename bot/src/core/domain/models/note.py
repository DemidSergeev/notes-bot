from dataclasses import dataclass
from pathlib import Path

from .base_model import BaseModel

@dataclass
class Note(BaseModel):
    title: str
    filename: Path