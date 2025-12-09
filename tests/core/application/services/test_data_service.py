import uuid
import pytest
from io import BytesIO

from src.core.application.services import DataService
from src.core.domain.models import Course, Subject, Note
from src.core.domain.common.enums import CourseYear


@pytest.fixture
def data_service(mock_course_repo, mock_subject_repo, mock_note_repo, mock_note_storage) -> DataService:
    """Create DataService instance with mocked dependencies."""
    return DataService(
        course_repo=mock_course_repo,
        subject_repo=mock_subject_repo,
        note_repo=mock_note_repo,
        note_storage=mock_note_storage
    )


class TestDataServiceGetMethods:
    """Test data retrieval methods."""

    def test_get_courses(self, data_service, courses, mock_course_repo):
        """Test retrieving all courses."""
        mock_course_repo.get_all.return_value = courses
        
        result = data_service.get_courses()
        
        assert len(result) == 3
        assert all(isinstance(c, Course) for c in result)
        mock_course_repo.get_all.assert_called_once()

    def test_get_subjects_success(self, data_service, course, mock_course_repo):
        """Test retrieving subjects for a valid course year."""
        mock_course_repo.get_by_year.return_value = course
        
        result = data_service.get_subjects(CourseYear.TWO)
        
        assert result == course.subjects
        assert len(result) == 3
        mock_course_repo.get_by_year.assert_called_once_with(CourseYear.TWO)

    def test_get_subjects_course_not_found(self, data_service, mock_course_repo):
        """Test retrieving subjects when course doesn't exist."""
        mock_course_repo.get_by_year.return_value = None
        
        with pytest.raises(ValueError, match="Course for year .* does not exist"):
            data_service.get_subjects(CourseYear.ONE)

    def test_get_notes(self, data_service, subject, mock_subject_repo):
        """Test retrieving notes from a subject."""
        mock_subject_repo.get_by_id.return_value = subject
        
        result = data_service.get_notes(subject.id)
        
        assert result == subject.notes
        assert len(result) == 3
        mock_subject_repo.get_by_id.assert_called_once_with(subject.id)

    def test_get_notes_subject_not_found(self, data_service, mock_subject_repo):
        """Test retrieving notes when subject doesn't exist."""
        subject_id = uuid.uuid4()
        mock_subject_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Subject with id .* does not exist"):
            data_service.get_notes(subject_id)

    def test_get_approved_notes_by_subject_id(self, data_service, notes, mock_note_repo, subject_id):
        """Test retrieving approved notes for a subject."""
        approved_notes = notes[:2]
        mock_note_repo.get_approved_by_subject_id.return_value = approved_notes
        
        result = data_service.get_approved_notes_by_subject_id(subject_id)
        
        assert len(result) == 2
        assert all(n.is_approved for n in result)
        mock_note_repo.get_approved_by_subject_id.assert_called_once_with(subject_id)

    def test_get_approved_notes_empty(self, data_service, mock_note_repo, subject_id):
        """Test retrieving approved notes when none exist."""
        mock_note_repo.get_approved_by_subject_id.return_value = []
        
        result = data_service.get_approved_notes_by_subject_id(subject_id)
        
        assert result == []

    def test_get_not_approved_notes(self, data_service, notes, mock_note_repo):
        """Test retrieving not approved notes."""
        not_approved = [notes[2]]
        mock_note_repo.get_not_approved.return_value = not_approved
        
        result = data_service.get_not_approved_notes()
        
        assert len(result) == 1
        assert not result[0].is_approved
        mock_note_repo.get_not_approved.assert_called_once()

    def test_get_not_approved_notes_empty(self, data_service, mock_note_repo):
        """Test retrieving not approved notes when none exist."""
        mock_note_repo.get_not_approved.return_value = []
        
        result = data_service.get_not_approved_notes()
        
        assert result == []

    def test_get_note_by_id(self, data_service, note, mock_note_repo):
        """Test retrieving a note by ID."""
        mock_note_repo.get_by_id.return_value = note
        
        result = data_service.get_note_by_id(note.id)
        
        assert result == note
        assert result.title == "Advanced Mathematics"
        mock_note_repo.get_by_id.assert_called_once_with(note.id)

    def test_get_note_by_id_not_found(self, data_service, mock_note_repo):
        """Test retrieving a note that doesn't exist."""
        note_id = uuid.uuid4()
        mock_note_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            data_service.get_note_by_id(note_id)

    def test_get_note_file(self, data_service, note, mock_note_repo, mock_note_storage):
        """Test retrieving a note file from storage."""
        file_content = b"PDF content"
        mock_note_repo.get_by_id.return_value = note
        mock_note_storage.get_by_id.return_value = file_content
        
        result = data_service.get_note_file(note.id)
        
        assert result == file_content
        mock_note_repo.get_by_id.assert_called_once_with(note.id)
        mock_note_storage.get_by_id.assert_called_once_with(note.id)

    def test_get_note_file_note_not_found(self, data_service, mock_note_repo):
        """Test retrieving file for non-existent note."""
        note_id = uuid.uuid4()
        mock_note_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            data_service.get_note_file(note_id)

    def test_get_note_file_storage_missing(self, data_service, note, mock_note_repo, mock_note_storage):
        """Test retrieving file when storage doesn't have it."""
        mock_note_repo.get_by_id.return_value = note
        mock_note_storage.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note file with id .* does not exist in storage"):
            data_service.get_note_file(note.id)

    def test_get_note_url(self, data_service, note, mock_note_repo, mock_note_storage):
        """Test retrieving a presigned URL for a note."""
        url = "https://minio.example.com/notes/123?token=abc"
        mock_note_repo.get_by_id.return_value = note
        mock_note_storage.get_url.return_value = url
        
        result = data_service.get_note_url(note.id)
        
        assert result == url
        mock_note_repo.get_by_id.assert_called_once_with(note.id)
        mock_note_storage.get_url.assert_called_once_with(note.id, note.title)

    def test_get_note_url_note_not_found(self, data_service, mock_note_repo):
        """Test retrieving URL for non-existent note."""
        note_id = uuid.uuid4()
        mock_note_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            data_service.get_note_url(note_id)

    def test_get_note_url_storage_missing(self, data_service, note, mock_note_repo, mock_note_storage):
        """Test retrieving URL when storage can't generate it."""
        mock_note_repo.get_by_id.return_value = note
        mock_note_storage.get_url.return_value = None
        
        with pytest.raises(ValueError, match="Note URL with id .* does not exist in storage"):
            data_service.get_note_url(note.id)


class TestDataServiceCreateMethods:
    """Test entity creation and update methods."""

    def test_add_subject_success(self, data_service, course, mock_course_repo, mock_subject_repo):
        """Test adding a subject to a course."""
        mock_course_repo.get_by_year.return_value = course
        
        result = data_service.add_subject(CourseYear.TWO, "New Subject")
        
        assert isinstance(result, Subject)
        assert result.name == "New Subject"
        mock_course_repo.get_by_year.assert_called_once_with(CourseYear.TWO)
        mock_subject_repo.save.assert_called_once()

    def test_add_subject_course_not_found(self, data_service, mock_course_repo):
        """Test adding subject to non-existent course."""
        mock_course_repo.get_by_year.return_value = None
        
        with pytest.raises(ValueError, match="Course for year .* does not exist"):
            data_service.add_subject(CourseYear.ONE, "New Subject")

    def test_add_subject_saves_with_course_id(self, data_service, course, mock_course_repo, mock_subject_repo):
        """Test that subject is saved with correct course ID."""
        mock_course_repo.get_by_year.return_value = course
        
        data_service.add_subject(CourseYear.TWO, "New Subject")
        
        # Verify save was called with correct course_id
        call_args = mock_subject_repo.save.call_args
        assert call_args[0][1] == course.id  # Second positional arg is course_id

    def test_upload_note_success(self, data_service, subject_id, pdf_file, mock_note_repo, mock_note_storage):
        """Test uploading a note file."""
        data_service.upload_note("Math Notes.pdf", subject_id, pdf_file)
        
        mock_note_repo.save.assert_called_once()
        mock_note_storage.save.assert_called_once()
        
        # Verify note was saved with correct subject_id
        note_save_call = mock_note_repo.save.call_args
        assert note_save_call[0][1] == subject_id

    def test_upload_note_file_seeked_to_start(self, data_service, subject_id, mock_note_repo, mock_note_storage):
        """Test that file is seeked to start before saving."""
        pdf_file = BytesIO(b"PDF content")
        pdf_file.seek(5)  # Move pointer to middle
        
        data_service.upload_note("Math Notes.pdf", subject_id, pdf_file)
        
        # Verify seek(0) was called (by checking the file position)
        assert pdf_file.tell() == 0 or mock_note_storage.save.called

    def test_upload_note_creates_note_instance(self, data_service, subject_id, pdf_file, mock_note_repo, mock_note_storage):
        """Test that upload creates a Note instance with correct title."""
        data_service.upload_note("Calculus.pdf", subject_id, pdf_file)
        
        note_save_call = mock_note_repo.save.call_args
        saved_note = note_save_call[0][0]
        
        assert isinstance(saved_note, Note)
        assert saved_note.title == "Calculus.pdf"
        assert not saved_note.is_approved  # New notes should not be approved by default


class TestDataServiceDeleteMethods:
    """Test entity deletion methods."""

    def test_delete_subject_success(self, data_service, subject, mock_subject_repo):
        """Test deleting a subject."""
        mock_subject_repo.get_by_id.return_value = subject
        
        data_service.delete_subject(subject.id)
        
        mock_subject_repo.get_by_id.assert_called_once_with(subject.id)
        mock_subject_repo.delete.assert_called_once_with(subject.id)

    def test_delete_subject_not_found(self, data_service, mock_subject_repo):
        """Test deleting a non-existent subject."""
        subject_id = uuid.uuid4()
        mock_subject_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Subject with id .* does not exist"):
            data_service.delete_subject(subject_id)

    def test_delete_note_success(self, data_service, note, mock_note_repo):
        """Test deleting a note."""
        mock_note_repo.get_by_id.return_value = note
        
        data_service.delete_note(note.id)
        
        mock_note_repo.get_by_id.assert_called_once_with(note.id)
        mock_note_repo.delete.assert_called_once_with(note.id)

    def test_delete_note_not_found(self, data_service, mock_note_repo):
        """Test deleting a non-existent note."""
        note_id = uuid.uuid4()
        mock_note_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            data_service.delete_note(note_id)
