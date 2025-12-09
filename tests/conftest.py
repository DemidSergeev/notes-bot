import uuid
from io import BytesIO
from pytest import fixture
from unittest.mock import MagicMock, Mock

from src.core.domain.models import Course, Subject, Note, User
from src.core.domain.common.enums import CourseYear
from src.infrastructure.adapters.outbound.persistence.models import (
    Course as DbCourse,
    Subject as DbSubject,
    Note as DbNote,
)


# --- DOMAIN MODEL FIXTURES ---

@fixture
def note_id() -> uuid.UUID:
    return uuid.uuid4()

@fixture
def subject_id() -> uuid.UUID:
    return uuid.uuid4()

@fixture
def course_id() -> uuid.UUID:
    return uuid.uuid4()

@fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@fixture
def note(note_id) -> Note:
    """Create a domain Note instance."""
    return Note(
        id=note_id,
        title="Advanced Mathematics",
        is_approved=True,
    )

@fixture
def unapproved_note(note_id) -> Note:
    """Create an unapproved domain Note instance."""
    return Note(
        id=note_id,
        title="Physics Basics",
        is_approved=False,
    )

@fixture
def notes(note_id) -> list[Note]:
    """Create multiple Note instances."""
    return [
        Note(title="Calculus", is_approved=True),
        Note(title="Linear Algebra", is_approved=True),
        Note(title="Differential Equations", is_approved=False),
    ]

@fixture
def subject(subject_id, notes) -> Subject:
    """Create a domain Subject with notes."""
    return Subject(
        id=subject_id,
        name="Mathematics",
        notes=notes,
    )

@fixture
def subjects(notes) -> list[Subject]:
    """Create multiple Subject instances."""
    return [
        Subject(name="Mathematics", notes=notes[:2]),
        Subject(name="Physics", notes=notes[1:]),
        Subject(name="Chemistry", notes=[]),
    ]

@fixture
def course(course_id, subjects) -> Course:
    """Create a domain Course with subjects."""
    return Course(
        id=course_id,
        year=CourseYear.TWO,
        subjects=subjects,
    )

@fixture
def courses() -> list[Course]:
    """Create multiple Course instances."""
    return [
        Course(year=CourseYear.ONE, subjects=[]),
        Course(year=CourseYear.TWO, subjects=[]),
        Course(year=CourseYear.THREE, subjects=[]),
    ]

@fixture
def user(user_id) -> User:
    """Create a domain User instance."""
    return User(
        id=user_id,
        external_id=123456789,
        name="John Doe",
    )


# --- DATABASE MODEL FIXTURES ---

@fixture
def db_note(note_id, subject_id) -> DbNote:
    """Create a database Note model."""
    return DbNote(
        id=note_id,
        title="Advanced Mathematics",
        is_approved=True,
        subject_id=subject_id,
    )

@fixture
def db_notes(subject_id) -> list[DbNote]:
    """Create multiple database Note models."""
    return [
        DbNote(id=uuid.uuid4(), title="Calculus", is_approved=True, subject_id=subject_id),
        DbNote(id=uuid.uuid4(), title="Linear Algebra", is_approved=True, subject_id=subject_id),
        DbNote(id=uuid.uuid4(), title="Diff Eq", is_approved=False, subject_id=subject_id),
    ]

@fixture
def db_subject(subject_id, course_id, db_notes) -> DbSubject:
    """Create a database Subject model with notes."""
    subject = DbSubject(
        id=subject_id,
        name="Mathematics",
        course_id=course_id,
    )
    subject.notes = db_notes
    return subject

@fixture
def db_subjects(course_id) -> list[DbSubject]:
    """Create multiple database Subject models."""
    subjects = []
    for i in range(3):
        subject = DbSubject(
            id=uuid.uuid4(),
            name=f"Subject{i+1}",
            course_id=course_id,
        )
        subject.notes = []
        subjects.append(subject)
    return subjects

@fixture
def db_course(course_id, db_subjects) -> DbCourse:
    """Create a database Course model with subjects."""
    course = DbCourse(
        id=course_id,
        year=CourseYear.TWO.value,
    )
    course.subjects = db_subjects
    return course

@fixture
def db_courses() -> list[DbCourse]:
    """Create multiple database Course models."""
    courses = []
    for year in [1, 2, 3]:
        course = DbCourse(id=uuid.uuid4(), year=year)
        course.subjects = []
        courses.append(course)
    return courses


# --- MOCK REPOSITORY FIXTURES ---

@fixture
def mock_session_factory() -> Mock:
    """Create a mock session factory."""
    return MagicMock()

@fixture
def mock_note_repo() -> Mock:
    """Create a mock NoteRepositoryPort."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.get_by_title.return_value = None
    repo.get_approved_by_subject_id.return_value = []
    repo.get_not_approved.return_value = []
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo

@fixture
def mock_subject_repo() -> Mock:
    """Create a mock SubjectRepositoryPort."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.get_by_name.return_value = None
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo

@fixture
def mock_course_repo() -> Mock:
    """Create a mock CourseRepositoryPort."""
    repo = MagicMock()
    repo.get_by_id.return_value = None
    repo.get_by_year.return_value = None
    repo.get_all.return_value = []
    repo.save.return_value = None
    repo.delete.return_value = None
    return repo

@fixture
def mock_note_storage() -> Mock:
    """Create a mock NoteStoragePort."""
    storage = MagicMock()
    storage.get_by_id.return_value = None
    storage.get_url.return_value = None
    storage.save.return_value = None
    storage.delete.return_value = None
    return storage


# --- FILE/STREAM FIXTURES ---

@fixture
def pdf_file() -> BytesIO:
    """Create a mock PDF file."""
    file = BytesIO(b"%PDF-1.4\n%fake pdf content")
    file.seek(0)
    return file

@fixture
def text_file() -> BytesIO:
    """Create a mock text file."""
    file = BytesIO(b"Sample note content\nLine 2\nLine 3")
    file.seek(0)
    return file