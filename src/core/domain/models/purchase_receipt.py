from dataclasses import dataclass

from .base_model import BaseModel
from .note import Note
from .user import User


@dataclass
class PurchaseReceipt(BaseModel):
    buyer: User
    payment_details: str
    note: Note
