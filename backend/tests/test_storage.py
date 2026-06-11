"""Storage service tests — local and S3 backends.

Tests LocalStorage, S3Storage (via moto mock), and the get_storage()
factory function that selects the right backend based on settings.
"""

import boto3
import pytest
from app.services.storage import LocalStorage, S3Storage, get_storage
from moto import mock_aws

# ── LocalStorage tests ─────────────────────────────────────


class TestLocalStorage:
    """LocalStorage writes to a temp directory on disk."""

    @pytest.fixture
    def storage(self, tmp_path):
        return LocalStorage(base_dir=tmp_path)

    def test_upload_creates_file(self, storage):
        storage.upload("test.csv", b"a,b,c\n1,2,3", folder="raw")
        assert storage.exists("test.csv", folder="raw")

    def test_download_returns_content(self, storage):
        storage.upload("test.csv", b"hello,world\n1,2", folder="raw")
        content = storage.download("test.csv", folder="raw")
        assert content == b"hello,world\n1,2"

    def test_exists_returns_false_for_missing(self, storage):
        assert not storage.exists("noexiste.csv", folder="raw")

    def test_delete_removes_file(self, storage):
        storage.upload("test.csv", b"data", folder="raw")
        assert storage.exists("test.csv", folder="raw")
        storage.delete("test.csv", folder="raw")
        assert not storage.exists("test.csv", folder="raw")

    def test_delete_missing_does_not_raise(self, storage):
        storage.delete("noexiste.csv", folder="raw")  # should not raise

    def test_download_missing_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.download("noexiste.csv", folder="raw")

    def test_different_folders(self, storage):
        storage.upload("test.csv", b"raw-data", folder="raw")
        storage.upload("test.csv", b"processed-data", folder="processed")
        assert storage.download("test.csv", folder="raw") == b"raw-data"
        assert storage.download("test.csv", folder="processed") == b"processed-data"

    def test_upload_overwrites(self, storage):
        storage.upload("test.csv", b"v1", folder="raw")
        storage.upload("test.csv", b"v2", folder="raw")
        assert storage.download("test.csv", folder="raw") == b"v2"


# ── S3Storage tests (moto) ─────────────────────────────────


class TestS3Storage:
    """S3Storage tested against a mocked AWS S3 via moto."""

    @pytest.fixture(autouse=True)
    def _setup_s3(self, monkeypatch):
        """Configure settings for moto-based S3."""
        import app.config

        monkeypatch.setattr(app.config.settings, "S3_BUCKET", "datlas-test-bucket")
        monkeypatch.setattr(app.config.settings, "AWS_REGION", "us-east-1")
        monkeypatch.setattr(app.config.settings, "AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setattr(app.config.settings, "AWS_SECRET_ACCESS_KEY", "testing")

    @pytest.fixture
    def s3_storage(self):
        with mock_aws():
            # Create the test bucket
            client = boto3.client("s3", region_name="us-east-1")
            client.create_bucket(Bucket="datlas-test-bucket")
            yield S3Storage()

    def test_upload_and_download(self, s3_storage):
        s3_storage.upload("test.csv", b"col1,col2\n1,2", folder="raw")
        content = s3_storage.download("test.csv", folder="raw")
        assert content == b"col1,col2\n1,2"

    def test_exists_true_after_upload(self, s3_storage):
        s3_storage.upload("test.csv", b"data", folder="raw")
        assert s3_storage.exists("test.csv", folder="raw")

    def test_exists_false_for_missing(self, s3_storage):
        assert not s3_storage.exists("no-file.csv", folder="raw")

    def test_delete_removes_file(self, s3_storage):
        s3_storage.upload("test.csv", b"data", folder="raw")
        s3_storage.delete("test.csv", folder="raw")
        assert not s3_storage.exists("test.csv", folder="raw")

    def test_download_missing_raises(self, s3_storage):
        with pytest.raises(FileNotFoundError):
            s3_storage.download("noexiste.csv", folder="raw")

    def test_different_folders(self, s3_storage):
        s3_storage.upload("test.csv", b"raw", folder="raw")
        s3_storage.upload("test.csv", b"processed", folder="processed")
        assert s3_storage.download("test.csv", folder="raw") == b"raw"
        assert s3_storage.download("test.csv", folder="processed") == b"processed"

    def test_upload_returns_s3_uri(self, s3_storage):
        uri = s3_storage.upload("data.csv", b"x,y\n1,2", folder="raw")
        assert uri.startswith("s3://datlas-test-bucket/raw/data.csv")

    def test_s3_storage_requires_bucket(self):
        """S3Storage without S3_BUCKET set should raise ValueError."""
        import app.config

        original = app.config.settings.S3_BUCKET
        try:
            app.config.settings.S3_BUCKET = None
            with pytest.raises(ValueError, match="S3_BUCKET"):
                S3Storage()
        finally:
            app.config.settings.S3_BUCKET = original


# ── Factory tests ──────────────────────────────────────────


class TestGetStorage:
    """get_storage() returns the right backend based on settings."""

    def test_returns_local_when_no_s3_bucket(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.S3_BUCKET", None)
        storage = get_storage()
        assert isinstance(storage, LocalStorage)

    def test_returns_s3_when_bucket_configured(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.S3_BUCKET", "my-bucket")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        # S3Storage init will try to create a boto3 client (no actual call made)
        storage = get_storage()
        assert isinstance(storage, S3Storage)
