"""Tests for application configuration (Settings).

Validates default values, environment variable overrides,
and computed properties (database_url, database_url_sync).
"""


import pytest
from pydantic import ValidationError

from app.config import Settings


class TestSettingsDefaults:
    """Settings should have sensible defaults for development."""

    def test_api_defaults(self):
        s = Settings()
        assert s.API_HOST == "0.0.0.0"
        assert s.API_PORT == 8000
        assert s.DEBUG is True

    def test_postgres_defaults(self):
        s = Settings()
        assert s.POSTGRES_USER == "datlas"
        assert s.POSTGRES_DB == "datlas_db"
        assert s.POSTGRES_PORT == 5432

    def test_aws_defaults_none(self):
        s = Settings()
        assert s.AWS_ACCESS_KEY_ID is None
        assert s.AWS_SECRET_ACCESS_KEY is None
        assert s.S3_BUCKET is None

    def test_aws_region_default(self):
        s = Settings()
        assert s.AWS_REGION == "us-east-1"

    def test_extra_fields_ignored(self):
        """Unknown env vars should be ignored, not raise errors."""
        s = Settings(UNKNOWN_FIELD="should_be_ignored")
        assert not hasattr(s, "UNKNOWN_FIELD")


class TestDatabaseUrlProperty:
    """The database_url property constructs the async connection URL."""

    def test_default_database_url(self):
        s = Settings()
        url = s.database_url
        assert url.startswith("postgresql://")
        assert "datlas:datlas_secreto_2026" in url
        assert "@db:5432/datlas_db" in url

    def test_database_url_with_custom_values(self):
        s = Settings(
            POSTGRES_USER="admin",
            POSTGRES_PASSWORD="pass123",
            POSTGRES_DB="prod_db",
            POSTGRES_PORT=5433,
        )
        assert "admin:pass123" in s.database_url
        assert "@db:5433/prod_db" in s.database_url


class TestDatabaseUrlSync:
    """The sync URL points to localhost for Alembic migrations."""

    def test_sync_url_uses_localhost(self):
        s = Settings()
        assert "@localhost:" in s.database_url_sync
        assert "datlas_db" in s.database_url_sync

    def test_sync_url_differs_from_async(self):
        s = Settings()
        assert s.database_url_sync != s.database_url
        assert "localhost" in s.database_url_sync
        assert "db:" in s.database_url


class TestEnvVarOverride:
    """Environment variables should override defaults."""

    def test_override_api_port(self, monkeypatch):
        monkeypatch.setenv("API_PORT", "9000")
        s = Settings()
        assert s.API_PORT == 9000

    def test_override_debug(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "false")
        s = Settings()
        assert s.DEBUG is False

    def test_override_aws_region(self, monkeypatch):
        monkeypatch.setenv("AWS_REGION", "sa-east-1")
        s = Settings()
        assert s.AWS_REGION == "sa-east-1"

    def test_override_postgres_password(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_PASSWORD", "strong_pass")
        s = Settings()
        assert s.POSTGRES_PASSWORD == "strong_pass"
        assert "strong_pass" in s.database_url


class TestSettingsValidation:
    """Type coercion and validation edge cases."""

    def test_port_coerced_to_int(self):
        s = Settings(API_PORT="8001")  # str input
        assert s.API_PORT == 8001
        assert isinstance(s.API_PORT, int)

    def test_debug_coerced_from_str(self):
        s = Settings(DEBUG="false")
        assert s.DEBUG is False

    def test_invalid_port_type(self):
        with pytest.raises(ValidationError):
            Settings(API_PORT="not_a_number")
