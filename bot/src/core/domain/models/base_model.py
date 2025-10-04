import uuid
from dataclasses import dataclass, field

@dataclass
class BaseModel:
    id: uuid.UUID = field(default_factory=uuid.uuid4)