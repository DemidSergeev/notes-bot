from dataclasses import dataclass

from .base_model import BaseModel

@dataclass
class User(BaseModel):
    # id: uuid.UUID - should User be persisted?
    external_id: int # BAD! Using int external_id leaks information about external system
    name: str