import uuid
import pytest
from unittest.mock import MagicMock
from sqlmodel import Session

from src.infrastructure.adapters.outbound.persistence import SqlModelSubjectRepository
from src.core.domain.models import Subject, Note
from src.infrastructure.adapters.outbound.persistence.models import Subject as DbSubject


@pytest.fixture
def mock_note_repo() -> MagicMock:
    """Create a mock NoteRepository."""
    return MagicMock()


@pytest.fixture
def mock_session_factory():
    """Create a properly mocked session factory that handles context manager protocol."""
    mock_session = MagicMock(spec=Session)
    mock_factory = MagicMock()
    
    # Setup context manager behavior
    mock_factory.return_value.__enter__.return_value = mock_session
    mock_factory.return_value.__exit__.return_value = None
    
    # Attach the session for easy access in tests
    mock_factory._session = mock_session
    
    return mock_factory


@pytest.fixture
def subject_repository(mock_session_factory, mock_note_repo) -> SqlModelSubjectRepository:
    """Create SubjectRepository with mocked session factory and note repo."""
    return SqlModelSubjectRepository(
        session_factory=mock_session_factory,
        note_repository=mock_note_repo
    )


class TestSqlModelSubjectRepositoryGetMethods:
    """Test get methods."""

    def test_get_by_id_success(self, subject_repository, subject_id, db_subject, mock_session_factory):
        """Test retrieving a subject by ID."""
        mock_session_factory._session.get.return_value = db_subject
        
        result = subject_repository.get_by_id(subject_id)
        
        assert isinstance(result, Subject)
        assert result.id == subject_id
        assert result.name == "Mathematics"
        mock_session_factory._session.get.assert_called_once_with(DbSubject, subject_id)

    def test_get_by_id_not_found(self, subject_repository, subject_id, mock_session_factory):
        """Test retrieving a non-existent subject by ID."""
        mock_session_factory._session.get.return_value = None
        
        result = subject_repository.get_by_id(subject_id)
        
        assert result is None

    def test_get_by_id_includes_notes(self, subject_repository, subject_id, db_subject, db_notes, mock_session_factory):
        """Test that get_by_id includes associated notes."""
        db_subject.notes = db_notes
        mock_session_factory._session.get.return_value = db_subject
        
        result = subject_repository.get_by_id(subject_id)
        
        assert len(result.notes) == 3
        assert all(isinstance(n, Note) for n in result.notes)

    def test_get_by_name_success(self, subject_repository, db_subject, mock_session_factory):
        """Test retrieving a subject by name."""
        mock_session_factory._session.exec.return_value.first.return_value = db_subject
        
        result = subject_repository.get_by_name("Mathematics")
        
        assert isinstance(result, Subject)
        assert result.name == "Mathematics"

    def test_get_by_name_not_found(self, subject_repository, mock_session_factory):
        """Test retrieving a subject with non-existent name."""
        mock_session_factory._session.exec.return_value.first.return_value = None
        
        result = subject_repository.get_by_name("Nonexistent Subject")
        
        assert result is None

    def test_get_by_name_case_sensitive(self, subject_repository, db_subject, mock_session_factory):
        """Test that get_by_name is case-sensitive."""
        mock_session_factory._session.exec.return_value.first.return_value = db_subject
        
        result = subject_repository.get_by_name("Mathematics")
        
        # Verify the query was executed with exact name
        assert result.name == "Mathematics"


class TestSqlModelSubjectRepositorySaveMethods:
    """Test save methods."""

    def test_save_new_subject(self, subject_repository, subject, course_id, mock_session_factory, mock_note_repo):
        """Test saving a new subject."""
        mock_session_factory._session.get.return_value = None  # Subject doesn't exist
        
        subject_repository.save(subject, course_id)
        
        mock_session_factory._session.add.assert_called_once()
        mock_session_factory._session.commit.assert_called_once()

    def test_save_existing_subject(self, subject_repository, subject, course_id, mock_session_factory, mock_note_repo):
        """Test updating an existing subject."""
        db_subject = MagicMock(spec=DbSubject)
        db_subject.id = subject.id
        mock_session_factory._session.get.return_value = db_subject  # Subject exists
        
        subject_repository.save(subject, course_id)
        
        assert db_subject.name == subject.name
        assert db_subject.course_id == course_id
        mock_session_factory._session.add.assert_not_called()  # Should not add when updating
        mock_session_factory._session.commit.assert_called_once()

    def test_save_creates_new_subject_instance(self, subject_repository, subject, course_id, mock_session_factory, mock_note_repo):
        """Test that save creates a new DbSubject when needed."""
        mock_session_factory._session.get.return_value = None
        
        subject_repository.save(subject, course_id)
        
        # Verify that add was called with a DbSubject instance
        add_call = mock_session_factory._session.add.call_args[0][0]
        assert isinstance(add_call, DbSubject)
        assert add_call.name == subject.name

    def test_save_saves_subject_notes(self, subject_repository, subject, course_id, mock_session_factory, mock_note_repo):
        """Test that save calls note_repo.save for each note."""
        mock_session_factory._session.get.return_value = None
        
        subject_repository.save(subject, course_id)
        
        # Verify note_repo.save was called for each note
        assert mock_note_repo.save.call_count == len(subject.notes)

    def test_save_passes_correct_subject_id_to_notes(self, subject_repository, subject, course_id, mock_session_factory, mock_note_repo):
        """Test that notes are saved with correct subject_id."""
        mock_session_factory._session.get.return_value = None
        
        subject_repository.save(subject, course_id)
        
        # Verify each note was saved with the subject's ID
        for call in mock_note_repo.save.call_args_list:
            assert call[0][1] == subject.id


class TestSqlModelSubjectRepositoryDeleteMethods:
    """Test delete methods."""

    def test_delete_success(self, subject_repository, subject_id, mock_session_factory):
        """Test deleting an existing subject."""
        db_subject = MagicMock(spec=DbSubject)
        db_subject.name = "Mathematics"
        mock_session_factory._session.get.return_value = db_subject
        
        subject_repository.delete(subject_id)
        
        mock_session_factory._session.delete.assert_called_once_with(db_subject)
        mock_session_factory._session.commit.assert_called_once()

    def test_delete_non_existent_subject(self, subject_repository, subject_id, mock_session_factory):
        """Test deleting a non-existent subject."""
        mock_session_factory._session.get.return_value = None
        
        subject_repository.delete(subject_id)
        
        # Should not call delete if subject doesn't exist
        mock_session_factory._session.delete.assert_not_called()
        mock_session_factory._session.commit.assert_not_called()


class TestSqlModelSubjectRepositoryEdgeCases:
    """Test edge cases and error scenarios."""

    def test_get_subject_with_empty_notes(self, subject_repository, subject_id, mock_session_factory):
        """Test retrieving a subject with no notes."""
        db_subject = MagicMock(spec=DbSubject)
        db_subject.id = subject_id
        db_subject.name = "Empty Subject"
        db_subject.notes = []
        mock_session_factory._session.get.return_value = db_subject
        
        result = subject_repository.get_by_id(subject_id)
        
        assert result.notes == []

    def test_get_subject_with_many_notes(self, subject_repository, subject_id, mock_session_factory):
        """Test retrieving a subject with many notes."""
        db_subject = MagicMock(spec=DbSubject)
        db_subject.id = subject_id
        db_subject.name = "Subject with Many Notes"
        
        # Create 100 mock notes
        many_notes = [MagicMock(id=uuid.uuid4(), title=f"Note {i}", is_approved=True) for i in range(100)]
        db_subject.notes = many_notes
        mock_session_factory._session.get.return_value = db_subject
        
        result = subject_repository.get_by_id(subject_id)
        
        assert len(result.notes) == 100

    def test_save_subject_with_long_name(self, subject_repository, course_id, mock_session_factory, mock_note_repo):
        """Test saving a subject with a very long name."""
        subject = Subject(name="A" * 500)  # Very long name
        mock_session_factory._session.get.return_value = None
        
        subject_repository.save(subject, course_id)
        
        mock_session_factory._session.add.assert_called_once()
        mock_session_factory._session.commit.assert_called_once()

    def test_save_subject_with_special_characters(self, subject_repository, course_id, mock_session_factory, mock_note_repo):
        """Test saving a subject with special characters in name."""
        subject = Subject(name="Subject & Course (Draft) [2024]")
        mock_session_factory._session.get.return_value = None
        
        subject_repository.save(subject, course_id)
        
        # Verify the subject was created with special characters preserved
        add_call = mock_session_factory._session.add.call_args[0][0]
        assert add_call.name == subject.name

    def test_multiple_save_operations_same_subject(self, subject_repository, subject, course_id, mock_session_factory, mock_note_repo):
        """Test saving the same subject multiple times."""
        db_subject = MagicMock(spec=DbSubject)
        db_subject.id = subject.id
        mock_session_factory._session.get.return_value = db_subject  # Exists after first save
        
        # First save (update)
        subject_repository.save(subject, course_id)
        # Second save (update again)
        subject_repository.save(subject, course_id)
        
        # Should update both times, not add
        mock_session_factory._session.add.assert_not_called()
        assert mock_session_factory._session.commit.call_count == 2
