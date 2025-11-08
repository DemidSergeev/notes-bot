from dataclasses import dataclass

from .base_model import BaseModel


@dataclass
class Note(BaseModel):
    title: str
    price_rub: int
    is_approved: bool = False