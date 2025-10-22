from __future__ import annotations

from typing import Final

from minio import Minio

from .config import Settings


_MINIO_SECURE: Final[bool] = False


def create_minio_client(settings: Settings) -> Minio:
    endpoint = str(settings.minio_endpoint)
    client = Minio(
        endpoint.replace("http://", "").replace("https://", ""),
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=endpoint.startswith("https"),
    )

    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)

    return client
