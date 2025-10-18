from dataclasses import dataclass

from .base_model import BaseModel

@dataclass
class Buyer(BaseModel):
    # id: uuid.UUID - should Buyer be persisted?
    external_id: int # BAD! Using int external_id leaks information about external system
    name: str