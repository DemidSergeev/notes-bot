from dataclasses import dataclass

from .base_model import BaseModel
from .subject import Subject
from ..common.enums import CourseYear


@dataclass
class Course(BaseModel):
    year: CourseYear
    subjects: list[Subject]