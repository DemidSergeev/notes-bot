import logging
from time import sleep
from minio import Minio

from .settings import settings


logger = logging.getLogger(__name__)

sleep(1) # Костыль for minio container startup
client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

url_signer_client = Minio(
    endpoint=settings.MINIO_EXTERNAL_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
    region="us-east-1"
)

bucket = settings.MINIO_BUCKET
def create_bucket():
    found = client.bucket_exists(bucket)
    logger.debug("Bucket '%s' already exists", bucket)
    if not found:
        client.make_bucket(bucket)
        logger.info("Bucket '%s' created", bucket)

def get_client() -> Minio:
    return client

def get_url_signer_client() -> Minio:
    return url_signer_client