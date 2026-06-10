"""Storage service — abstract file storage with S3 and local backends.

Provides a pluggable storage layer so Datlas can persist uploaded
and processed CSV files to either local disk (dev/default) or AWS S3
(production). The backend is chosen based on settings.S3_BUCKET.

Usage:
    from app.services.storage import get_storage
    storage = get_storage()
    storage.upload("data.csv", b"...content...", folder="raw")
    content = storage.download("data.csv", folder="raw")
"""

from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

from app.config import settings


class StorageBackend(ABC):
    """Abstract interface for file storage operations."""

    @abstractmethod
    def upload(self, filename: str, content: bytes, folder: str = "raw") -> str:
        """Store a file and return its path/key."""
        ...

    @abstractmethod
    def download(self, filename: str, folder: str = "raw") -> bytes:
        """Retrieve file content by filename and folder."""
        ...

    @abstractmethod
    def exists(self, filename: str, folder: str = "raw") -> bool:
        """Check if a file exists in storage."""
        ...

    @abstractmethod
    def delete(self, filename: str, folder: str = "raw") -> None:
        """Remove a file from storage."""
        ...


class LocalStorage(StorageBackend):
    """Store files on the local filesystem.

    Used by default in development. Files go to data/raw/ and data/processed/.
    """

    def __init__(self, base_dir: str | Path = "data"):
        self.base_dir = Path(base_dir)

    def _path(self, filename: str, folder: str) -> Path:
        return self.base_dir / folder / filename

    def upload(self, filename: str, content: bytes, folder: str = "raw") -> str:
        path = self._path(filename, folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def download(self, filename: str, folder: str = "raw") -> bytes:
        path = self._path(filename, folder)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_bytes()

    def exists(self, filename: str, folder: str = "raw") -> bool:
        return self._path(filename, folder).exists()

    def delete(self, filename: str, folder: str = "raw") -> None:
        path = self._path(filename, folder)
        if path.exists():
            path.unlink()


class S3Storage(StorageBackend):
    """Store files in an AWS S3 bucket.

    Files are organized as: s3://<bucket>/<folder>/<filename>

    Requires settings.S3_BUCKET to be configured. Credentials are read
    from the standard AWS credential chain (env vars, ~/.aws/credentials,
    IAM role).
    """

    def __init__(self):
        import boto3

        self.bucket = settings.S3_BUCKET
        if not self.bucket:
            raise ValueError("S3_BUCKET must be configured to use S3 storage")

        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def _key(self, filename: str, folder: str) -> str:
        """Build the S3 object key: folder/filename."""
        return f"{folder}/{filename}"

    def upload(self, filename: str, content: bytes, folder: str = "raw") -> str:
        key = self._key(filename, folder)
        self.client.upload_fileobj(BytesIO(content), self.bucket, key)
        return f"s3://{self.bucket}/{key}"

    def download(self, filename: str, folder: str = "raw") -> bytes:
        key = self._key(filename, folder)
        buf = BytesIO()
        try:
            self.client.download_fileobj(self.bucket, key, buf)
        except self.client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File not found in S3: {key}") from e
            raise
        return buf.getvalue()

    def exists(self, filename: str, folder: str = "raw") -> bool:
        key = self._key(filename, folder)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.ClientError:
            return False

    def delete(self, filename: str, folder: str = "raw") -> None:
        key = self._key(filename, folder)
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_storage() -> StorageBackend:
    """Factory: return the configured storage backend.

    If S3_BUCKET is set → S3Storage.
    Otherwise → LocalStorage (default, backwards-compatible).
    """
    if settings.S3_BUCKET:
        return S3Storage()
    return LocalStorage()
