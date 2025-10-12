from dataclasses import dataclass

from .base_model import BaseModel

@dataclass
class Buyer(BaseModel):
    external_id: int # BAD! Using int external_id leaks information about external system
    name: str