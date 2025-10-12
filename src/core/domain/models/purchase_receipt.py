from dataclasses import dataclass

from .base_model import BaseModel
from .note import Note
from .buyer import Buyer


@dataclass
class PurchaseReceipt(BaseModel):
    buyer: Buyer
    payment_details: str
    note: Note