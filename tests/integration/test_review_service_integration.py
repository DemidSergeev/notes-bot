"""Integration tests for ReviewService with real PostgreSQL and MinIO."""

import uuid
import pytest
from io import BytesIO

from src.core.application.services import ReviewService
from src.core.domain.models import Course, Note, Subject
from src.core.domain.common.enums import CourseYear


class TestReviewServiceIntegration:
    """Integration tests for ReviewService with database and storage."""

    @pytest.fixture
    def review_service(self, note_repo, note_storage):
        """Create a ReviewService with real repositories."""
        return ReviewService(
            note_repo=note_repo,
            note_storage=note_storage
        )

    def _setup_note(self, course_repo, subject_repo, note_repo, course_year=CourseYear.ONE):
        """Helper method to create a complete note structure in the database."""
        # Create course
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=course_year, subjects=[])
        course_repo.save(course)

        # Create subject
        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Test Subject", notes=[])
        subject_repo.save(subject, course_id)

        # Create note
        note_id = uuid.uuid4()
        note = Note(id=note_id, title="Test Note for Review", is_approved=False)
        note_repo.save(note, subject_id)

        return note_id, subject_id, course_id

    # ========================================================================
    # Approval Tests
    # ========================================================================

    def test_approve_note(self, review_service, course_repo, subject_repo, note_repo):
        """Test approving a note."""
        # Setup
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)

        # Verify note is initially not approved
        note = note_repo.get_by_id(note_id)
        assert note.is_approved is False

        # Approve the note
        review_service.approve_note(note_id)

        # Verify note is now approved
        approved_note = note_repo.get_by_id(note_id)
        assert approved_note.is_approved is True
        assert approved_note.title == "Test Note for Review"

    def test_approve_nonexistent_note(self, review_service):
        """Test approving a note that doesn't exist."""
        nonexistent_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            review_service.approve_note(nonexistent_id)

    def test_approve_already_approved_note(self, review_service, course_repo, subject_repo, note_repo):
        """Test approving a note that's already approved."""
        # Setup with approved note
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Test Subject", notes=[])
        subject_repo.save(subject, course_id)

        note_id = uuid.uuid4()
        note = Note(id=note_id, title="Already Approved", is_approved=True)
        note_repo.save(note, subject_id)

        # Approve again (should not cause issues)
        review_service.approve_note(note_id)

        # Verify still approved
        result = note_repo.get_by_id(note_id)
        assert result.is_approved is True

    # ========================================================================
    # Rejection Tests
    # ========================================================================

    def test_reject_note(self, review_service, course_repo, subject_repo, note_repo, note_storage):
        """Test rejecting a note (which deletes it)."""
        # Setup and upload a file
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)
        
        # Upload a file for this note
        note = note_repo.get_by_id(note_id)
        file_content = b"Content that will be deleted"
        file = BytesIO(file_content)
        note_storage.save(note, file)

        # Verify file exists
        retrieved_content = note_storage.get_by_id(note_id)
        assert retrieved_content == file_content

        # Verify note exists
        existing_note = note_repo.get_by_id(note_id)
        assert existing_note is not None

        # Reject the note
        review_service.reject_note(note_id, "Poor quality content")

        # Verify note is deleted from database
        deleted_note = note_repo.get_by_id(note_id)
        assert deleted_note is None

        # Verify file is deleted from storage
        with pytest.raises(Exception):
            note_storage.get_by_id(note_id)

    def test_reject_nonexistent_note(self, review_service):
        """Test rejecting a note that doesn't exist."""
        nonexistent_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Note with id .* does not exist"):
            review_service.reject_note(nonexistent_id, "Spam")

    def test_reject_note_without_file(self, review_service, course_repo, subject_repo, note_repo):
        """Test rejecting a note that has no file in storage."""
        # Setup note WITHOUT uploading a file
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)

        # Verify note exists
        existing_note = note_repo.get_by_id(note_id)
        assert existing_note is not None

        # Reject the note (MinIO gracefully ignores deletion of non-existent objects)
        review_service.reject_note(note_id, "Incomplete")

        # Verify note is deleted from database
        deleted_note = note_repo.get_by_id(note_id)
        assert deleted_note is None

    # ========================================================================
    # Workflow Tests
    # ========================================================================

    def test_approval_workflow(self, review_service, course_repo, subject_repo, note_repo):
        """Test a typical approval workflow with multiple notes."""
        # Create multiple notes
        notes_data = []
        for i in range(3):
            note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)
            notes_data.append((note_id, subject_id))

        # Approve first two notes
        review_service.approve_note(notes_data[0][0])
        review_service.approve_note(notes_data[1][0])

        # Verify approval status
        note1 = note_repo.get_by_id(notes_data[0][0])
        note2 = note_repo.get_by_id(notes_data[1][0])
        note3 = note_repo.get_by_id(notes_data[2][0])

        assert note1.is_approved is True
        assert note2.is_approved is True
        assert note3.is_approved is False

    def test_reject_and_approve_workflow(self, review_service, course_repo, subject_repo, note_repo, note_storage):
        """Test a workflow that rejects some notes and approves others."""
        # Create notes
        notes_data = []
        for i in range(3):
            course_id = uuid.uuid4()
            course = Course(id=course_id, year=CourseYear.ONE, subjects=[])
            course_repo.save(course)

            subject_id = uuid.uuid4()
            subject = Subject(id=subject_id, name=f"Subject {i}", notes=[])
            subject_repo.save(subject, course_id)

            note_id = uuid.uuid4()
            note = Note(id=note_id, title=f"Note {i}", is_approved=False)
            note_repo.save(note, subject_id)

            notes_data.append((note_id, subject_id))

        # Approve first note
        review_service.approve_note(notes_data[0][0])

        # Reject second note (MinIO gracefully handles missing files)
        review_service.reject_note(notes_data[1][0], "Spam")

        # Verify states
        note1 = note_repo.get_by_id(notes_data[0][0])
        note2 = note_repo.get_by_id(notes_data[1][0])
        note3 = note_repo.get_by_id(notes_data[2][0])

        assert note1.is_approved is True
        assert note2 is None  # Deleted after rejection
        assert note3.is_approved is False

    # ========================================================================
    # Integration with Data Service Tests
    # ========================================================================

    def test_review_and_retrieve_approved_note(self, review_service, course_repo, subject_repo, note_repo):
        """Test reviewing a note and then retrieving it as approved."""
        # Setup
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)

        # Approve the note
        review_service.approve_note(note_id)

        # Retrieve approved notes for the subject
        approved_notes = note_repo.get_approved_by_subject_id(subject_id)

        assert len(approved_notes) == 1
        assert approved_notes[0].id == note_id
        assert approved_notes[0].is_approved is True

    def test_review_multiple_notes_in_subject(self, review_service, course_repo, subject_repo, note_repo):
        """Test reviewing multiple notes in a single subject."""
        # Setup: Create one subject with multiple notes
        course_id = uuid.uuid4()
        course = Course(id=course_id, year=CourseYear.TWO, subjects=[])
        course_repo.save(course)

        subject_id = uuid.uuid4()
        subject = Subject(id=subject_id, name="Review Test Subject", notes=[])
        subject_repo.save(subject, course_id)

        # Create multiple notes
        note_ids = []
        for i in range(5):
            note_id = uuid.uuid4()
            note = Note(id=note_id, title=f"Note {i}", is_approved=False)
            note_repo.save(note, subject_id)
            note_ids.append(note_id)

        # Approve first 3 notes
        for note_id in note_ids[:3]:
            review_service.approve_note(note_id)

        # Verify approved count
        approved = note_repo.get_approved_by_subject_id(subject_id)
        assert len(approved) == 3

        # Verify not approved count
        not_approved = note_repo.get_not_approved()
        assert len(not_approved) >= 2

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_approve_with_invalid_id_type(self, review_service):
        """Test approving with an invalid ID type."""
        # This should raise a DataError due to invalid UUID format in database query
        from sqlalchemy.exc import DataError
        with pytest.raises((ValueError, TypeError, AttributeError, DataError)):
            review_service.approve_note("not-a-uuid")

    def test_reject_with_missing_reason(self, review_service, course_repo, subject_repo, note_repo):
        """Test rejecting a note with an empty reason."""
        # Setup
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)

        # Reject with empty reason should still work (reason is just for logging)
        review_service.reject_note(note_id, "")
        
        # Verify note is deleted
        deleted_note = note_repo.get_by_id(note_id)
        assert deleted_note is None

    # ========================================================================
    # Storage Interaction Tests
    # ========================================================================

    def test_reject_note_with_file_cleanup(self, review_service, course_repo, subject_repo, note_repo, note_storage):
        """Test that rejecting a note properly cleans up the storage."""
        # Setup
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)

        # Create and store a file
        note = note_repo.get_by_id(note_id)
        file_content = b"Important lecture notes that will be deleted"
        file = BytesIO(file_content)
        note_storage.save(note, file)

        # Verify file exists before rejection
        stored_content = note_storage.get_by_id(note_id)
        assert stored_content == file_content

        # Reject note
        review_service.reject_note(note_id, "Plagiarism detected")

        # Verify both DB and storage are cleaned
        db_note = note_repo.get_by_id(note_id)
        assert db_note is None

        with pytest.raises(Exception):
            note_storage.get_by_id(note_id)

    def test_approve_note_preserves_file(self, review_service, course_repo, subject_repo, note_repo, note_storage):
        """Test that approving a note doesn't affect its stored file."""
        # Setup
        note_id, subject_id, _ = self._setup_note(course_repo, subject_repo, note_repo)

        # Create and store a file
        note = note_repo.get_by_id(note_id)
        file_content = b"Preserved lecture notes"
        file = BytesIO(file_content)
        note_storage.save(note, file)

        # Approve the note
        review_service.approve_note(note_id)

        # Verify file still exists
        stored_content = note_storage.get_by_id(note_id)
        assert stored_content == file_content

        # Verify note is approved
        approved_note = note_repo.get_by_id(note_id)
        assert approved_note.is_approved is True
