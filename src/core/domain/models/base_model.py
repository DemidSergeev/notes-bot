import uuid
from dataclasses import dataclass, field, KW_ONLY

from ..common.facades import uuid7


@dataclass
class BaseModel:
    # KW_ONLY gives ability to both generate ID automatically and set it manually.
    # This avoids errors with unexpected keyword argument 'id' and non-default argument following default argument 'id'
    _: KW_ONLY
    id: uuid.UUID = field(default_factory=uuid7)