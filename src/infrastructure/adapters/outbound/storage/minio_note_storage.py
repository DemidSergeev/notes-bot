import logging
from minio import Minio

from src.core.application.ports.outbound.storage import NoteStoragePort


logger = logging.getLogger(__name__)

class MinioNoteStorage(NoteStoragePort):
    def __init__(self, client: Minio, bucket: str, url_signer_client: Minio):
        self._client = client
        self._bucket = bucket
        self._url_signer_client = url_signer_client

    def get_by_id(self, note_id):
        try:
            response = self._client.get_object(bucket_name=self._bucket, object_name=str(note_id))
            return response.data
        finally:
            response.close()
            response.release_conn()

    def get_url(self, note_id, note_title):
        headers = { 
            "response-content-disposition": f'attachment; filename="{note_title}"'
        }
        url = self._url_signer_client.get_presigned_url(
            method="GET",
            bucket_name=self._bucket,
            object_name=str(note_id),
            response_headers=headers
        )
        return url

    def save(self, note, file):
        length = len(file.getvalue())
        result = self._client.put_object(
            bucket_name=self._bucket,
            object_name=str(note.id),
            data=file,
            length=length
        )
        logger.debug("Note %s (UUID %s) saved in storage. File size = %.1f Kb", note.title, note.id, length / 1024)

    def delete(self, note_id):
        self._client.remove_object(
            bucket_name=self._bucket,
            object_name=str(note_id)
        )

        logger.debug("Note (UUID %s) deleted from storage", note_id)