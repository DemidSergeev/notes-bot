from minio import Minio

from src.core.application.ports.outbound.storage import NoteStoragePort


class MinioNoteStorage(NoteStoragePort):
    def __init__(self, client: Minio, bucket: str):
        self._client = client
        self._bucket = bucket

    def get_by_id(self, note_id):
        try:
            response = self._client.get_object(bucket_name=self._bucket, object_name=str(note_id))
            return response.data
        finally:
            response.close()
            response.release_conn()

    def get_url(self, note_id):
        url = self._client.get_presigned_url(
            method="GET",
            bucket_name=self._bucket,
            object_name=str(note_id)
        )
        return url

    def save(self, note, file):
        result = self._client.put_object(
            bucket_name=self._bucket,
            object_name=str(note.id),
            data=file,
            length=len(file.getvalue()),
        )

    def delete(self, note_id):
        self._client.remove_object(
            bucket_name=self._bucket,
            object_name=str(note_id)
        )
