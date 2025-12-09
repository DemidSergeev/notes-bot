import pytest
from unittest.mock import MagicMock
from sqlmodel import Session

from src.infrastructure.adapters.outbound.persistence import SqlModelNoteRepository
from src.core.domain.models import Note
from src.infrastructure.adapters.outbound.persistence.models import Note as DbNote


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
def note_repository(mock_session_factory) -> SqlModelNoteRepository:
    """Create NoteRepository with mocked session factory."""
    return SqlModelNoteRepository(session_factory=mock_session_factory)


class TestSqlModelNoteRepositoryGetMethods:
    """Test get methods."""

    def test_get_by_id_success(self, note_repository, db_note, mock_session_factory):
        """Test retrieving a note by ID."""
        mock_session_factory._session.get.return_value = db_note
        
        result = note_repository.get_by_id(db_note.id)
        
        assert isinstance(result, Note)
        assert result.id == db_note.id
        assert result.title == db_note.title
        mock_session_factory._session.get.assert_called_once_with(DbNote, db_note.id)

    def test_get_by_id_not_found(self, note_repository, note_id, mock_session_factory):
        """Test retrieving a non-existent note by ID."""
        mock_session_factory._session.get.return_value = None
        
        result = note_repository.get_by_id(note_id)
        
        assert result is None

    def test_get_by_title_success(self, note_repository, db_note, mock_session_factory):
        """Test retrieving a note by title."""
        mock_session_factory._session.exec.return_value.first.return_value = db_note
        
        result = note_repository.get_by_title(db_note.title)
        
        assert isinstance(result, Note)
        assert result.title == db_note.title
        assert result.id == db_note.id

    def test_get_by_title_not_found(self, note_repository, mock_session_factory):
        """Test retrieving a note with non-existent title."""
        mock_session_factory._session.exec.return_value.first.return_value = None
        
        result = note_repository.get_by_title("Nonexistent Title")
        
        assert result is None

    def test_get_approved_by_subject_id_success(self, note_repository, subject_id, db_notes, mock_session_factory):
        """Test retrieving approved notes by subject ID."""
        approved_notes = [db_notes[0], db_notes[1]]  # First two are approved
        mock_session_factory._session.exec.return_value.all.return_value = approved_notes
        
        result = note_repository.get_approved_by_subject_id(subject_id)
        
        assert len(result) == 2
        assert all(isinstance(n, Note) for n in result)
        assert all(n.is_approved for n in result)

    def test_get_approved_by_subject_id_empty(self, note_repository, subject_id, mock_session_factory):
        """Test retrieving approved notes when none exist."""
        mock_session_factory._session.exec.return_value.all.return_value = []
        
        result = note_repository.get_approved_by_subject_id(subject_id)
        
        assert result == []

    def test_get_not_approved_success(self, note_repository, db_notes, mock_session_factory):
        """Test retrieving not approved notes."""
        not_approved = [db_notes[2]]  # Last one is not approved
        mock_session_factory._session.exec.return_value.all.return_value = not_approved
        
        result = note_repository.get_not_approved()
        
        assert len(result) == 1
        assert not result[0].is_approved

    def test_get_not_approved_empty(self, note_repository, mock_session_factory):
        """Test retrieving not approved notes when none exist."""
        mock_session_factory._session.exec.return_value.all.return_value = []
        
        result = note_repository.get_not_approved()
        
        assert result == []


class TestSqlModelNoteRepositorySaveMethods:
    """Test save methods."""

    def test_save_new_note(self, note_repository, note, subject_id, mock_session_factory):
        """Test saving a new note."""
        mock_session_factory._session.get.return_value = None  # Note doesn't exist
        
        note_repository.save(note, subject_id)
        
        mock_session_factory._session.add.assert_called_once()
        mock_session_factory._session.commit.assert_called_once()

    def test_save_existing_note(self, note_repository, note, subject_id, mock_session_factory):
        """Test updating an existing note."""
        db_note = MagicMock(spec=DbNote)
        db_note.id = note.id
        mock_session_factory._session.get.return_value = db_note  # Note exists
        
        note_repository.save(note, subject_id)
        
        assert db_note.title == note.title
        assert db_note.is_approved == note.is_approved
        assert db_note.subject_id == subject_id
        mock_session_factory._session.add.assert_not_called()  # Should not add when updating
        mock_session_factory._session.commit.assert_called_once()

    def test_save_creates_new_note_instance(self, note_repository, note, subject_id, mock_session_factory):
        """Test that save creates a new DbNote when needed."""
        mock_session_factory._session.get.return_value = None
        
        note_repository.save(note, subject_id)
        
        # Verify that add was called with a DbNote instance
        add_call = mock_session_factory._session.add.call_args[0][0]
        assert isinstance(add_call, DbNote)
        assert add_call.title == note.title
        assert add_call.subject_id == subject_id

    def test_save_with_none_subject_id(self, note_repository, note, mock_session_factory):
        """Test saving a note with None subject_id."""
        db_note = MagicMock(spec=DbNote)
        mock_session_factory._session.get.return_value = db_note
        
        note_repository.save(note, subject_id=None)
        
        # subject_id should not be updated if None
        mock_session_factory._session.commit.assert_called_once()

    def test_save_note_with_special_title(self, note_repository, subject_id, mock_session_factory):
        """Test saving a note with special characters in title."""
        special_note = Note(title="Test & Note (2024) [Draft].pdf", is_approved=False)
        mock_session_factory._session.get.return_value = None
        
        note_repository.save(special_note, subject_id)
        
        add_call = mock_session_factory._session.add.call_args[0][0]
        assert add_call.title == special_note.title


class TestSqlModelNoteRepositoryDeleteMethods:
    """Test delete methods."""

    def test_delete_success(self, note_repository, note_id, mock_session_factory):
        """Test deleting an existing note."""
        db_note = MagicMock(spec=DbNote)
        db_note.title = "Test Note"
        mock_session_factory._session.get.return_value = db_note
        
        note_repository.delete(note_id)
        
        mock_session_factory._session.delete.assert_called_once_with(db_note)
        mock_session_factory._session.commit.assert_called_once()

    def test_delete_non_existent_note(self, note_repository, note_id, mock_session_factory):
        """Test deleting a non-existent note."""
        mock_session_factory._session.get.return_value = None
        
        note_repository.delete(note_id)
        
        # Should not call delete if note doesn't exist
        mock_session_factory._session.delete.assert_not_called()
        mock_session_factory._session.commit.assert_not_called()


class TestSqlModelNoteRepositoryEdgeCases:
    """Test edge cases and error scenarios."""

    def test_note_conversion_preserves_data(self, note_repository, db_note, mock_session_factory):
        """Test that domain Note is created correctly from DbNote."""
        mock_session_factory._session.get.return_value = db_note
        
        result = note_repository.get_by_id(db_note.id)
        
        assert result.id == db_note.id
        assert result.title == db_note.title
        assert result.is_approved == db_note.is_approved

    def test_save_multiple_times_same_id(self, note_repository, note, subject_id, mock_session_factory):
        """Test saving the same note multiple times."""
        db_note = MagicMock(spec=DbNote)
        db_note.id = note.id
        mock_session_factory._session.get.return_value = db_note
        
        # First save
        note_repository.save(note, subject_id)
        # Second save
        note_repository.save(note, subject_id)
        
        # Should update both times, not add
        mock_session_factory._session.add.assert_not_called()
        assert mock_session_factory._session.commit.call_count == 2

    def test_list_conversion_to_notes(self, note_repository, db_notes, subject_id, mock_session_factory):
        """Test that list of DbNote converts correctly to list of Note."""
        mock_session_factory._session.exec.return_value.all.return_value = db_notes
        
        result = note_repository.get_approved_by_subject_id(subject_id)
        
        assert len(result) == len(db_notes)
        assert all(isinstance(n, Note) for n in result)
        assert [n.id for n in result] == [db.id for db in db_notes]
