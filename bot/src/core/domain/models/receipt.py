from dataclasses import dataclass

from .base_model import BaseModel
from .note import Note


@dataclass
class Receipt(BaseModel):
    buyer_id: int
    buyer_name: str
    payment_credentials: str
    price_rub: int
    note: Note