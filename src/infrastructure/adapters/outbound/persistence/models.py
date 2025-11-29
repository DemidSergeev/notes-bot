__all__ = ["Course", "Subject", "Note"]

import uuid
from sqlmodel import Field, Relationship, SQLModel


class Course(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    year: int

    subjects: list["Subject"] = Relationship(back_populates="course", cascade_delete=True)


class Subject(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    name: str

    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    course: Course | None = Relationship(back_populates="subjects")

    notes: list["Note"] = Relationship(back_populates="subject", cascade_delete=True)


class Note(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    title: str

    is_approved: bool = Field(default=False)

    subject_id: uuid.UUID = Field(foreign_key="subject.id", index=True)
    subject: Subject | None = Relationship(back_populates="notes")
