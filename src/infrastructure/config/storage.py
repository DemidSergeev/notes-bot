from time import sleep
from minio import Minio
from .settings import settings


sleep(1) # Костыль for minio container startup
client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
)
bucket = settings.MINIO_BUCKET

def create_bucket():
    found = client.bucket_exists(bucket)
    if not found:
        client.make_bucket(bucket)

def get_client() -> Minio:
    return client