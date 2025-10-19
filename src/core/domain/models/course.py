from dataclasses import dataclass, field

from .base_model import BaseModel
from .subject import Subject
from ..common.enums import CourseYear


@dataclass
class Course(BaseModel):
    year: CourseYear
    subjects: list[Subject] = field(default_factory=list)