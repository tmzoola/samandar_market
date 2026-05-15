from abc import ABC, abstractmethod
from io import BytesIO

import anyio
from core.config import settings
from core.exceptions import CustomValidationException
from minio import Minio
from minio.error import S3Error

PERSON_IMG_BUCKET_NAME = "xs-auth"


class FileStorage(ABC):
    @abstractmethod
    async def upload_file_from_buffer(
        self,
        bucket_name: str,
        file_name: str,
        buf: BytesIO,
        content_type: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def download_file(self, bucket_name: str, file_name: str) -> BytesIO:
        pass


class MinioClient(FileStorage):
    def __init__(self):
        self.client = Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

    async def _ensure_bucket(self, bucket_name: str):
        exists = await anyio.to_thread.run_sync(self.client.bucket_exists, bucket_name)
        if not exists:
            await anyio.to_thread.run_sync(self.client.make_bucket, bucket_name)

    async def setup_buckets(self):
        await self._ensure_bucket(PERSON_IMG_BUCKET_NAME)

    def upload_file_from_buffer(self, bucket_name, file_name, buf, content_type=None):
        if not content_type:
            content_type = "application/octet-stream"

        result = self.client.put_object(
            bucket_name,
            file_name,
            buf,
            len(buf.getvalue()),
            content_type=content_type,
        )
        return result

    async def download_file(self, bucket_name, file_name):
        try:
            return await anyio.to_thread.run_sync(
                self.client.get_object,
                bucket_name,
                file_name,
            )
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise CustomValidationException(
                    detail=f"File {file_name} not found in bucket {bucket_name}"
                )
            raise CustomValidationException(
                detail=f"Failed to download file {file_name} from bucket {bucket_name}: {e}"
            )


minio_client = MinioClient()
