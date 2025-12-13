"""Integration tests for DataService with real PostgreSQL and MinIO."""

import uuid
import pytest
from io import BytesIO

from src.core.application.services import DataService
from src.core.domain.models import Course, Note, Subject
from src.core.domain.common.enums import CourseYear


class TestDataServiceIntegration:
    """Integration tests for DataService with database and storage."""

    @pytest.fixture
    def data_service(self, course_repo, subject_repo, note_repo, note_storage):
        """Create a DataService with real repositories."""
        return DataService(
            course_repo=course_repo,
            subject_repo=subject_repo,
            note_repo=note_repo,
            note_storage=note_storage
        )

    # ========================================================================
    # Course Operations Tests
    # ========================================================================

    def test_create_and_retrieve_course(self, course_repo, subject_repo):
        """Test creating and retrieving a course from the database."""
        course_id = uuid.uuid4()
        course = Course(
            id=course_id,
            year=CourseYear.ONE,
            subjects=[]
        )

        # Save the course
        course_repo.save(course)

        # Retrieve the course
        retrieved = course_repo.get_by_id(course_id)

        assert retrieved is not None
        assert retrieved.id == course_id
        assert retrieved.year == CourseYear.ONE
        assert retrieved.subjects == []

    def test_get_all_courses(self, course_repo):
        """Test retrieving all courses from the database."""
        # Create multiple courses
        courses = [
            Course(id=uuid.uuid4(), year=CourseYear.ONE, subjects=[]),
            Course(id=uuid.uuid4(), year=CourseYear.TWO, subjects=[]),
            Course(id=uuid.uuid4(), year=CourseYear.THREE, subjects=[]),
        ]

        for course in courses:
            course_repo.save(course)

        # Retrieve all courses
        all_courses = course_repo.get_all()

        assert len(all_courses) >= 3
        assert all(isinstance(c, Course) for c in all_courses)

    def test_get_course_by_year(self, course_repo):
        """Test retrieving a course by its year."""
        course_id = uuid.uuid4()
        course = Course(
            id=course_id,
            year=CourseYear.TWO,
            subjects=[]
        )
        course_repo.save(course)

        # Retrieve by year
        retrieved = course_repo.get_by_year(CourseYear.TWO)

        assert retrieved is not None
        assert retrieved.year == CourseYear.TWO
        assert retrieved.id == course_id

    # ========================================================================
    # Subject Operations Tests
    # ========================================================================

    def test_create_and_retrieve_subject(self, course_repo, subject_repo, note_repo):
        """Test creating and retrieving a subject with nested notes."""
        # Create a course first
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        # Create a subject
        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Mathematics", notes=[])
        subject_repo.save(subject, course_id)

        # Retrieve the subject
        retrieved = subject_repo.get_by_id(subject_id)

        assert retrieved is not None
        assert retrieved.id == subject_id
        assert retrieved.name == "Mathematics"

    def test_get_subjects_for_course(self, course_repo, subject_repo):
        """Test retrieving subjects associated with a course."""
        # Create a course
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        # Create subjects
        subjects = [
            Subject(id=uuid.uuid4(), name="Mathematics", notes=[]),
            Subject(id=uuid.uuid4(), name="Physics", notes=[]),
        ]
        for subject in subjects:
            subject_repo.save(subject, course_id)

        # Retrieve course with subjects
        retrieved_course = course_repo.get_by_id(course_id)

        assert retrieved_course is not None
        assert len(retrieved_course.subjects) == 2
        assert all(isinstance(s, Subject) for s in retrieved_course.subjects)

    # ========================================================================
    # Note Operations Tests
    # ========================================================================

    def test_create_and_retrieve_note(self, course_repo, subject_repo, note_repo):
        """Test creating and retrieving a note."""
        # Setup: Create course and subject
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        # Create note
        note_id = uuid.uuid4()
        note = Note(id=note_id, title="Calculus Basics", is_approved=False)
        note_repo.save(note, subject_id)

        # Retrieve note
        retrieved = note_repo.get_by_id(note_id)

        assert retrieved is not None
        assert retrieved.id == note_id
        assert retrieved.title == "Calculus Basics"
        assert retrieved.is_approved is False

    def test_get_notes_by_subject(self, course_repo, subject_repo, note_repo):
        """Test retrieving all notes in a subject."""
        # Setup: Create course and subject
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        # Create multiple notes
        notes = [
            Note(id=uuid.uuid4(), title="Calculus Notes", is_approved=True),
            Note(id=uuid.uuid4(), title="Algebra Notes", is_approved=False),
        ]
        for note in notes:
            note_repo.save(note, subject_id)

        # Retrieve notes via subject
        retrieved_subject = subject_repo.get_by_id(subject_id)

        assert retrieved_subject is not None
        assert len(retrieved_subject.notes) == 2

    def test_get_approved_notes(self, course_repo, subject_repo, note_repo):
        """Test retrieving only approved notes by subject."""
        # Setup: Create course and subject
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        # Create notes (some approved, some not)
        notes = [
            Note(id=uuid.uuid4(), title="Approved Note 1", is_approved=True),
            Note(id=uuid.uuid4(), title="Approved Note 2", is_approved=True),
            Note(id=uuid.uuid4(), title="Not Approved Note", is_approved=False),
        ]
        for note in notes:
            note_repo.save(note, subject_id)

        # Get approved notes
        approved = note_repo.get_approved_by_subject_id(subject_id)

        assert len(approved) == 2
        assert all(n.is_approved for n in approved)

    def test_get_not_approved_notes(self, course_repo, subject_repo, note_repo):
        """Test retrieving all not approved notes."""
        # Setup: Create courses and subjects with notes
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        # Create notes
        notes = [
            Note(id=uuid.uuid4(), title="Not Approved 1", is_approved=False),
            Note(id=uuid.uuid4(), title="Not Approved 2", is_approved=False),
            Note(id=uuid.uuid4(), title="Approved", is_approved=True),
        ]
        for note in notes:
            note_repo.save(note, subject_id)

        # Get not approved notes
        not_approved = note_repo.get_not_approved()

        assert len(not_approved) >= 2
        assert all(not n.is_approved for n in not_approved)

    def test_note_title_search(self, course_repo, subject_repo, note_repo):
        """Test retrieving a note by its title."""
        # Setup
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        # Create note
        note = Note(id=uuid.uuid4(), title="Unique Test Note Title", is_approved=False)
        note_repo.save(note, subject_id)

        # Retrieve by title
        retrieved = note_repo.get_by_title("Unique Test Note Title")

        assert retrieved is not None
        assert retrieved.title == "Unique Test Note Title"

    # ========================================================================
    # DataService Operations Tests
    # ========================================================================

    def test_data_service_get_courses(self, data_service, course_repo):
        """Test DataService.get_courses() returns all courses."""
        # Create and save some courses
        course1 = Course(id=uuid.uuid4(), year=CourseYear.ONE, subjects=[])
        course2 = Course(id=uuid.uuid4(), year=CourseYear.TWO, subjects=[])
        course_repo.save(course1)
        course_repo.save(course2)

        # Get courses via service
        courses = data_service.get_courses()

        assert len(courses) >= 2
        assert all(isinstance(c, Course) for c in courses)

    def test_data_service_get_subjects_for_course(self, data_service, course_repo, subject_repo):
        """Test DataService.get_subjects() for a specific course."""
        # Setup
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.TWO, subjects=[])
        course_repo.save(course)

        subjects = [
            Subject(id=uuid.uuid4(), name="Math", notes=[]),
            Subject(id=uuid.uuid4(), name="Physics", notes=[]),
        ]
        for subject in subjects:
            subject_repo.save(subject, course_id)

        # Get subjects via service
        retrieved_subjects = data_service.get_subjects(CourseYear.TWO)

        assert len(retrieved_subjects) == 2
        assert all(isinstance(s, Subject) for s in retrieved_subjects)

    def test_data_service_get_subjects_nonexistent_course(self, data_service):
        """Test DataService.get_subjects() with invalid course year."""
        with pytest.raises(ValueError, match="Course for year .* does not exist"):
            data_service.get_subjects(CourseYear.FOUR)

    def test_data_service_get_notes(self, data_service, course_repo, subject_repo, note_repo):
        """Test DataService.get_notes() for a specific subject."""
        # Setup
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        notes = [
            Note(id=uuid.uuid4(), title="Note 1", is_approved=True),
            Note(id=uuid.uuid4(), title="Note 2", is_approved=False),
        ]
        for note in notes:
            note_repo.save(note, subject_id)

        # Get notes via service
        retrieved_notes = data_service.get_notes(subject_id)

        assert len(retrieved_notes) == 2

    def test_data_service_get_note_by_id(self, data_service, course_repo, subject_repo, note_repo):
        """Test DataService.get_note_by_id()."""
        # Setup
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        note_id = uuid.uuid4()
        note = Note(id=note_id, title="Test Note", is_approved=True)
        note_repo.save(note, subject_id)

        # Get note via service
        retrieved = data_service.get_note_by_id(note_id)

        assert retrieved.id == note_id
        assert retrieved.title == "Test Note"

    def test_data_service_get_approved_notes_by_subject(self, data_service, course_repo, subject_repo, note_repo):
        """Test DataService.get_approved_notes_by_subject_id()."""
        # Setup
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        notes = [
            Note(id=uuid.uuid4(), title="Approved 1", is_approved=True),
            Note(id=uuid.uuid4(), title="Approved 2", is_approved=True),
            Note(id=uuid.uuid4(), title="Not Approved", is_approved=False),
        ]
        for note in notes:
            note_repo.save(note, subject_id)

        # Get approved notes via service
        approved = data_service.get_approved_notes_by_subject_id(subject_id)

        assert len(approved) == 2
        assert all(n.is_approved for n in approved)

    def test_data_service_get_not_approved_notes(self, data_service, course_repo, subject_repo, note_repo):
        """Test DataService.get_not_approved_notes()."""
        # Setup
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Math", notes=[])
        subject_repo.save(subject, course_id)

        notes = [
            Note(id=uuid.uuid4(), title="Not Approved 1", is_approved=False),
            Note(id=uuid.uuid4(), title="Not Approved 2", is_approved=False),
            Note(id=uuid.uuid4(), title="Approved", is_approved=True),
        ]
        for note in notes:
            note_repo.save(note, subject_id)

        # Get not approved notes via service
        not_approved = data_service.get_not_approved_notes()

        assert len(not_approved) >= 2
        assert all(not n.is_approved for n in not_approved)

    # ========================================================================
    # Storage Integration Tests
    # ========================================================================

    def test_note_file_storage_and_retrieval(self, note_storage, note_id):
        """Test saving and retrieving a note file from MinIO."""
        # Create a test note and file
        note = Note(id=note_id, title="Test Note", is_approved=False)
        file_content = b"This is test content for the note file."
        file = BytesIO(file_content)

        # Save file
        note_storage.save(note, file)

        # Retrieve file
        retrieved_content = note_storage.get_by_id(note_id)

        assert retrieved_content == file_content

    def test_note_file_deletion(self, note_storage, note_id):
        """Test deleting a note file from MinIO."""
        # Create and save a note file
        note = Note(id=note_id, title="Test Note", is_approved=False)
        file = BytesIO(b"Content to be deleted")
        note_storage.save(note, file)

        # Delete the file
        note_storage.delete(note_id)

        # Try to retrieve (should raise an error)
        with pytest.raises(Exception):
            note_storage.get_by_id(note_id)

    def test_get_note_presigned_url(self, note_storage, note_id):
        """Test generating a presigned URL for downloading a note."""
        # Create and save a note file
        note = Note(id=note_id, title="Test Note", is_approved=False)
        file = BytesIO(b"Content for URL generation")
        note_storage.save(note, file)

        # Get presigned URL
        url = note_storage.get_url(note_id, "test_note.pdf")

        assert url is not None
        assert isinstance(url, str)
        assert "http" in url

    # ========================================================================
    # End-to-End Tests
    # ========================================================================

    def test_end_to_end_note_creation_with_file(self, data_service, course_repo, subject_repo, note_repo, note_storage):
        """Test complete workflow: create course, subject, note, and upload file."""
        # Create course
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.THREE, subjects=[])
        course_repo.save(course)

        # Create subject
        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Advanced Mathematics", notes=[])
        subject_repo.save(subject, course_id)

        # Create note
        note_id = uuid.uuid4()
        note = Note(id=note_id, title="Advanced Calculus", is_approved=False)
        note_repo.save(note, subject_id)

        # Upload file
        file_content = b"Advanced calculus lecture notes"
        file = BytesIO(file_content)
        note_storage.save(note, file)

        # Retrieve and verify
        retrieved_note = data_service.get_note_by_id(note_id)
        assert retrieved_note.title == "Advanced Calculus"

        retrieved_file = data_service.get_note_file(note_id)
        assert retrieved_file == file_content
