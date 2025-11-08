__all__ = ["Course", "Subject", "Note", "PurchaseReceipt"]

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

    price_rub: int
    is_approved: bool = Field(default=False)

    subject_id: uuid.UUID = Field(foreign_key="subject.id", index=True)
    subject: Subject | None = Relationship(back_populates="notes")

    purchase_receipts: list["PurchaseReceipt"] = Relationship(back_populates="note", cascade_delete=True)


class PurchaseReceipt(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, index=True)
    buyer_id: int
    buyer_name: str
    payment_details: str

    note_id: uuid.UUID = Field(foreign_key="note.id", index=True)
    note: Note | None = Relationship(back_populates="purchase_receipts")