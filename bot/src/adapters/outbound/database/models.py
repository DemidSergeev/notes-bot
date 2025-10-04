import uuid
from sqlmodel import Field, Relationship, SQLModel


class Course(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    year: int
    subjects: list["Subject"] = Relationship(back_populates="course")


class Subject(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    name: str

    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)

    course: Course | None = Relationship(back_populates="subjects", cascade_delete=True)

    notes: list["Note"] = Relationship(back_populates="subject")

class Note(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    title: str

    subject_id: uuid.UUID = Field(foreign_key="subject.id", index=True)

    subject: Subject | None = Relationship(back_populates="notes", cascade_delete=True)