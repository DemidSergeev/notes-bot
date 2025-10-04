from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 4 таблицы — по одной на каждый курс (назовём курсы course_a..course_d)
class Course1(Base):
    __tablename__ = "course_1"
    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False, unique=True)
    has_note = Column(Boolean, nullable=False, default=False)
    pdf_filename = Column(String, nullable=True)

class Course2(Base):
    __tablename__ = "course_2"
    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False, unique=True)
    has_note = Column(Boolean, nullable=False, default=False)
    pdf_filename = Column(String, nullable=True)

class Course3(Base):
    __tablename__ = "course_3"
    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False, unique=True)
    has_note = Column(Boolean, nullable=False, default=False)
    pdf_filename = Column(String, nullable=True)

class Course4(Base):
    __tablename__ = "course_4"
    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False, unique=True)
    has_note = Column(Boolean, nullable=False, default=False)
    pdf_filename = Column(String, nullable=True)

# Таблица для курсовых работ; есть поле course (указывает, к какому курсу относится)
class Coursework(Base):
    __tablename__ = "coursework"
    id = Column(Integer, primary_key=True)
    course = Column(String, nullable=False)
    title = Column(String, nullable=False)
    pdf_filename = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint('course', 'title', name='uix_course_title'),)
