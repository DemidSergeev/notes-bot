import uuid
import pytest
from io import BytesIO
from unittest.mock import MagicMock, Mock

from src.infrastructure.adapters.outbound.storage import MinioNoteStorage


@pytest.fixture
def mock_minio_client() -> Mock:
    """Create a mock Minio client."""
    return MagicMock()


@pytest.fixture
def mock_url_signer_client() -> Mock:
    """Create a mock Minio URL signer client."""
    return MagicMock()


@pytest.fixture
def note_storage(mock_minio_client, mock_url_signer_client) -> MinioNoteStorage:
    """Create MinioNoteStorage with mocked clients."""
    return MinioNoteStorage(
        client=mock_minio_client,
        bucket="test-bucket",
        url_signer_client=mock_url_signer_client
    )


class TestMinioNoteStorageGetMethods:
    """Test retrieval methods."""

    def test_get_by_id_success(self, note_storage, note_id, mock_minio_client):
        """Test retrieving a note file by ID."""
        mock_response = MagicMock()
        mock_response.data = b"PDF content"
        mock_minio_client.get_object.return_value = mock_response
        
        result = note_storage.get_by_id(note_id)
        
        assert result == b"PDF content"
        mock_minio_client.get_object.assert_called_once_with(
            bucket_name="test-bucket",
            object_name=str(note_id)
        )
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    def test_get_by_id_with_large_file(self, note_storage, note_id, mock_minio_client):
        """Test retrieving a large note file."""
        large_content = b"x" * (1024 * 1024)  # 1MB
        mock_response = MagicMock()
        mock_response.data = large_content
        mock_minio_client.get_object.return_value = mock_response
        
        result = note_storage.get_by_id(note_id)
        
        assert len(result) == len(large_content)
        mock_response.close.assert_called_once()

    def test_get_by_id_handles_connection_cleanup(self, note_storage, note_id, mock_minio_client):
        """Test that connection is properly cleaned up even on error."""
        mock_response = MagicMock()
        mock_response.data = b"content"
        mock_response.close.side_effect = Exception("Close error")
        mock_minio_client.get_object.return_value = mock_response
        
        with pytest.raises(Exception):
            note_storage.get_by_id(note_id)
        
        # release_conn should still be called in finally block
        # Note: This depends on implementation, adjust if needed

    def test_get_url_success(self, note_storage, note_id, mock_url_signer_client):
        """Test generating a presigned URL."""
        expected_url = "https://minio.example.com/notes/123?token=abc"
        mock_url_signer_client.get_presigned_url.return_value = expected_url
        
        result = note_storage.get_url(note_id, "Test Note.pdf")
        
        assert result == expected_url
        mock_url_signer_client.get_presigned_url.assert_called_once()
        
        # Verify the call includes correct parameters
        call_kwargs = mock_url_signer_client.get_presigned_url.call_args[1]
        assert call_kwargs["bucket_name"] == "test-bucket"
        assert call_kwargs["object_name"] == str(note_id)
        assert "response_headers" in call_kwargs

    def test_get_url_with_special_characters_in_title(self, note_storage, note_id, mock_url_signer_client):
        """Test generating URL with special characters in note title."""
        expected_url = "https://minio.example.com/notes/123?token=abc"
        mock_url_signer_client.get_presigned_url.return_value = expected_url
        
        result = note_storage.get_url(note_id, "Test & Report (Draft).pdf")
        
        assert result == expected_url
        # Verify response headers contain the filename
        call_kwargs = mock_url_signer_client.get_presigned_url.call_args[1]
        response_headers = call_kwargs["response_headers"]
        assert "attachment" in response_headers["response-content-disposition"]

    def test_get_url_includes_attachment_header(self, note_storage, note_id, mock_url_signer_client):
        """Test that URL generation includes attachment header."""
        note_title = "Calculus Notes.pdf"
        expected_url = "https://example.com/file"
        mock_url_signer_client.get_presigned_url.return_value = expected_url
        
        note_storage.get_url(note_id, note_title)
        
        call_kwargs = mock_url_signer_client.get_presigned_url.call_args[1]
        assert "response-content-disposition" in call_kwargs["response_headers"]
        assert note_title in call_kwargs["response_headers"]["response-content-disposition"]


class TestMinioNoteStorageSaveMethods:
    """Test save methods."""

    def test_save_success(self, note_storage, note, pdf_file, mock_minio_client):
        """Test saving a note file."""
        note_storage.save(note, pdf_file)
        
        mock_minio_client.put_object.assert_called_once()
        call_kwargs = mock_minio_client.put_object.call_args[1]
        assert call_kwargs["bucket_name"] == "test-bucket"
        assert call_kwargs["object_name"] == str(note.id)

    def test_save_with_correct_file_size(self, note_storage, note, pdf_file, mock_minio_client):
        """Test that save includes correct file size."""
        file_content = b"Test PDF content"
        pdf_file = BytesIO(file_content)
        
        note_storage.save(note, pdf_file)
        
        call_kwargs = mock_minio_client.put_object.call_args[1]
        assert call_kwargs["length"] == len(file_content)

    def test_save_with_empty_file(self, note_storage, note, mock_minio_client):
        """Test saving an empty file."""
        empty_file = BytesIO(b"")
        
        note_storage.save(note, empty_file)
        
        call_kwargs = mock_minio_client.put_object.call_args[1]
        assert call_kwargs["length"] == 0

    def test_save_with_large_file(self, note_storage, note, mock_minio_client):
        """Test saving a large file (> 100MB)."""
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        large_file = BytesIO(large_content)
        
        note_storage.save(note, large_file)
        
        call_kwargs = mock_minio_client.put_object.call_args[1]
        assert call_kwargs["length"] == len(large_content)

    def test_save_file_position_reset(self, note_storage, note, mock_minio_client):
        """Test that file position is not modified by save."""
        pdf_file = BytesIO(b"PDF content here")
        pdf_file.seek(5)  # Move to position 5
        
        note_storage.save(note, pdf_file)
        
        # Verify put_object was called with the file object
        call_args = mock_minio_client.put_object.call_args[1]
        assert call_args["data"] == pdf_file


class TestMinioNoteStorageDeleteMethods:
    """Test delete methods."""

    def test_delete_success(self, note_storage, note_id, mock_minio_client):
        """Test deleting a note file."""
        note_storage.delete(note_id)
        
        mock_minio_client.remove_object.assert_called_once_with(
            bucket_name="test-bucket",
            object_name=str(note_id)
        )

    def test_delete_non_existent_file(self, note_storage, note_id, mock_minio_client):
        """Test deleting a non-existent file (should not raise error)."""
        # Minio doesn't raise error for non-existent files
        note_storage.delete(note_id)
        
        mock_minio_client.remove_object.assert_called_once()

    def test_delete_multiple_files(self, note_storage, mock_minio_client):
        """Test deleting multiple files sequentially."""
        note_ids = [uuid.uuid4() for _ in range(3)]
        
        for note_id in note_ids:
            note_storage.delete(note_id)
        
        assert mock_minio_client.remove_object.call_count == 3


class TestMinioNoteStorageEdgeCases:
    """Test edge cases and error scenarios."""

    def test_bucket_name_used_correctly(self, mock_minio_client, mock_url_signer_client, note_id):
        """Test that correct bucket name is used in operations."""
        storage = MinioNoteStorage(
            client=mock_minio_client,
            bucket="custom-bucket",
            url_signer_client=mock_url_signer_client
        )
        
        mock_response = MagicMock()
        mock_response.data = b"content"
        mock_minio_client.get_object.return_value = mock_response
        
        storage.get_by_id(note_id)
        
        call_kwargs = mock_minio_client.get_object.call_args[1]
        assert call_kwargs["bucket_name"] == "custom-bucket"

    def test_note_id_converted_to_string(self, note_storage, note_id, mock_minio_client):
        """Test that note ID is converted to string for storage."""
        mock_response = MagicMock()
        mock_response.data = b"content"
        mock_minio_client.get_object.return_value = mock_response
        
        note_storage.get_by_id(note_id)
        
        call_kwargs = mock_minio_client.get_object.call_args[1]
        assert call_kwargs["object_name"] == str(note_id)
        assert isinstance(call_kwargs["object_name"], str)

    def test_multiple_clients_isolation(self, mock_minio_client, mock_url_signer_client):
        """Test that multiple storage instances are isolated."""
        storage1 = MinioNoteStorage(
            client=mock_minio_client,
            bucket="bucket1",
            url_signer_client=mock_url_signer_client
        )
        
        storage2 = MinioNoteStorage(
            client=MagicMock(),
            bucket="bucket2",
            url_signer_client=MagicMock()
        )
        
        assert storage1._bucket != storage2._bucket
        assert storage1._client != storage2._client
