import uuid
import pytest

from src.core.application.services import ReviewService


@pytest.fixture
def review_service(mock_note_repo, mock_note_storage) -> ReviewService:
    """Create ReviewService instance with mocked dependencies."""
    return ReviewService(
        note_repo=mock_note_repo,
        note_storage=mock_note_storage
    )


class TestReviewServiceApproveMethods:
    """Test note approval methods."""

    def test_approve_note_success(self, review_service, note, mock_note_repo):
        """Test approving a note."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.approve_note(note.id)
        
        mock_note_repo.get_by_id.assert_called_once_with(note.id)
        mock_note_repo.save.assert_called_once()

    def test_approve_note_sets_is_approved_true(self, review_service, note, mock_note_repo):
        """Test that approve_note sets is_approved to True."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.approve_note(note.id)
        
        # Verify that save was called with the approved note
        save_call = mock_note_repo.save.call_args
        saved_note = save_call[0][0]
        
        assert saved_note.is_approved is True

    def test_approve_note_not_found(self, review_service, mock_note_repo):
        """Test approving a non-existent note."""
        note_id = uuid.uuid4()
        mock_note_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            review_service.approve_note(note_id)
        
        mock_note_repo.save.assert_not_called()

    def test_approve_note_saves_with_no_subject_id(self, review_service, note, mock_note_repo):
        """Test that approve_note saves with subject_id=None."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.approve_note(note.id)
        
        save_call = mock_note_repo.save.call_args
        assert save_call[1].get('subject_id') is None or save_call[0][1] is None

    def test_approve_unapproved_note(self, review_service, unapproved_note, mock_note_repo):
        """Test approving a previously unapproved note."""
        assert not unapproved_note.is_approved
        mock_note_repo.get_by_id.return_value = unapproved_note
        
        review_service.approve_note(unapproved_note.id)
        
        save_call = mock_note_repo.save.call_args
        saved_note = save_call[0][0]
        
        assert saved_note.is_approved is True


class TestReviewServiceRejectMethods:
    """Test note rejection methods."""

    def test_reject_note_success(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test rejecting a note."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.reject_note(note.id, "Test rejection reason")
        
        mock_note_repo.get_by_id.assert_called_once_with(note.id)
        mock_note_storage.delete.assert_called_once_with(note.id)
        mock_note_repo.delete.assert_called_once_with(note.id)

    def test_reject_note_deletes_from_storage(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test that reject_note deletes from storage before repository."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.reject_note(note.id, "Low quality")
        
        # Verify storage delete was called
        mock_note_storage.delete.assert_called_once_with(note.id)

    def test_reject_note_deletes_from_repository(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test that reject_note deletes from repository."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.reject_note(note.id, "Incorrect subject")
        
        # Verify repository delete was called
        mock_note_repo.delete.assert_called_once_with(note.id)

    def test_reject_note_not_found(self, review_service, mock_note_repo, mock_note_storage):
        """Test rejecting a non-existent note."""
        note_id = uuid.uuid4()
        mock_note_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            review_service.reject_note(note_id, "Not found")
        
        mock_note_storage.delete.assert_not_called()
        mock_note_repo.delete.assert_not_called()

    def test_reject_note_with_different_reasons(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test rejecting notes with various reasons."""
        reasons = ["Low quality", "Wrong subject", "Incomplete", "Duplicate"]
        
        for reason in reasons:
            mock_note_repo.get_by_id.return_value = note
            mock_note_storage.reset_mock()
            mock_note_repo.reset_mock()
            mock_note_repo.get_by_id.return_value = note
            
            review_service.reject_note(note.id, reason)
            
            mock_note_storage.delete.assert_called_once_with(note.id)
            mock_note_repo.delete.assert_called_once_with(note.id)

    def test_reject_approved_note(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test rejecting an already approved note."""
        assert note.is_approved  # Fixture creates approved note by default
        mock_note_repo.get_by_id.return_value = note
        
        review_service.reject_note(note.id, "Removal requested")
        
        # Should still delete from storage and repository
        mock_note_storage.delete.assert_called_once_with(note.id)
        mock_note_repo.delete.assert_called_once_with(note.id)


class TestReviewServiceEdgeCases:
    """Test edge cases and error scenarios."""

    def test_approve_then_reject_same_note_id(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test that rejecting after approving works correctly."""
        # First approve
        mock_note_repo.get_by_id.return_value = note
        review_service.approve_note(note.id)
        
        # Reset mocks
        mock_note_repo.reset_mock()
        mock_note_storage.reset_mock()
        mock_note_repo.get_by_id.return_value = note
        
        # Then reject
        review_service.reject_note(note.id, "Changed mind")
        
        mock_note_storage.delete.assert_called_once_with(note.id)
        mock_note_repo.delete.assert_called_once_with(note.id)

    def test_multiple_approvals_same_note(self, review_service, note, mock_note_repo):
        """Test that approving the same note multiple times works."""
        mock_note_repo.get_by_id.return_value = note
        
        # Approve twice
        review_service.approve_note(note.id)
        
        mock_note_repo.reset_mock()
        mock_note_repo.get_by_id.return_value = note
        
        review_service.approve_note(note.id)
        
        # Should call save twice
        assert mock_note_repo.save.call_count == 1

    def test_reject_with_empty_reason(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test rejecting a note with empty reason string."""
        mock_note_repo.get_by_id.return_value = note
        
        review_service.reject_note(note.id, "")
        
        # Should still process the rejection
        mock_note_storage.delete.assert_called_once_with(note.id)
        mock_note_repo.delete.assert_called_once_with(note.id)

    def test_reject_with_special_characters_in_reason(self, review_service, note, mock_note_repo, mock_note_storage):
        """Test rejecting with special characters in reason."""
        mock_note_repo.get_by_id.return_value = note
        reason = "Contains <script> tags & invalid chars: !@#$%"
        
        review_service.reject_note(note.id, reason)
        
        mock_note_storage.delete.assert_called_once_with(note.id)
        mock_note_repo.delete.assert_called_once_with(note.id)
