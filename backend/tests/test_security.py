"""Security tests — authentication, rate limiting, and file size limits."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def public_client(app_with_db):
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAuthMiddleware:
    @pytest.fixture(autouse=True)
    def _enable_auth(self, monkeypatch):
        import app.config
        monkeypatch.setattr(app.config.settings, "API_KEY", "test-secret-key-2026")

    @pytest.mark.asyncio
    async def test_public_paths_no_auth_required(self, public_client):
        for path in ("/", "/docs", "/health"):
            r = await public_client.get(path)
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_protected_path_without_key_returns_401(self, public_client):
        r = await public_client.post("/api/clean/analyze", json={"filename": "test.csv"})
        assert r.status_code == 401
        assert "X-API-Key" in r.json()["detail"]

    @pytest.mark.asyncio
    async def test_protected_path_with_invalid_key_returns_401(self, public_client):
        r = await public_client.post(
            "/api/clean/analyze",
            json={"filename": "test.csv"},
            headers={"X-API-Key": "wrong"},
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_path_with_valid_key_succeeds(self, public_client):
        csv_path = Path(__file__).parent / "data" / "test.csv"
        r = await public_client.post(
            "/api/upload",
            files={"file": ("test.csv", csv_path.read_bytes(), "text/csv")},
            headers={"X-API-Key": "test-secret-key-2026"},
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_accessible_with_auth(self, public_client):
        for path in ("/docs", "/openapi.json"):
            r = await public_client.get(path)
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_explore_requires_auth(self, public_client):
        r = await public_client.post("/api/explore/analyze", json={"filename": "test.csv"})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_pipeline_run_requires_auth(self, public_client):
        r = await public_client.post("/api/pipeline/run", json={"filename": "test.csv"})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_datasets_list_requires_auth(self, public_client):
        r = await public_client.get("/api/datasets")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_download_requires_auth(self, public_client):
        r = await public_client.get("/api/download/test.csv")
        assert r.status_code == 401


class TestNoAuthMode:
    @pytest.fixture(autouse=True)
    def _ensure_no_auth(self, monkeypatch):
        import app.config
        monkeypatch.setattr(app.config.settings, "API_KEY", "")

    @pytest.mark.asyncio
    async def test_upload_works_without_auth(self, public_client):
        csv_path = Path(__file__).parent / "data" / "test.csv"
        r = await public_client.post("/api/upload", files={"file": ("test.csv", csv_path.read_bytes(), "text/csv")})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_clean_analyze_works_without_auth(self, public_client):
        r = await public_client.post("/api/clean/analyze", json={"filename": "test.csv"})
        assert r.status_code != 401

    @pytest.mark.asyncio
    async def test_health_shows_auth_disabled(self, public_client):
        r = await public_client.get("/")
        assert r.status_code == 200
        assert r.json()["auth"] == "disabled"


class TestFileSizeLimits:
    @pytest.mark.asyncio
    async def test_small_csv_accepted(self, public_client):
        csv_path = Path(__file__).parent / "data" / "test.csv"
        r = await public_client.post("/api/upload", files={"file": ("small.csv", csv_path.read_bytes(), "text/csv")})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_oversized_csv_rejected(self, public_client, monkeypatch):
        import app.config
        monkeypatch.setattr(app.config.settings, "MAX_UPLOAD_SIZE_MB", 0)
        monkeypatch.setattr(app.config.settings, "API_KEY", "")
        csv_path = Path(__file__).parent / "data" / "test.csv"
        r = await public_client.post("/api/upload", files={"file": ("big.csv", csv_path.read_bytes(), "text/csv")})
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_pipeline_upload_size_limit(self, public_client, monkeypatch):
        import app.config
        monkeypatch.setattr(app.config.settings, "MAX_UPLOAD_SIZE_MB", 0)
        monkeypatch.setattr(app.config.settings, "API_KEY", "")
        csv_path = Path(__file__).parent / "data" / "test.csv"
        r = await public_client.post(
            "/api/pipeline/upload",
            files={"file": ("big.csv", csv_path.read_bytes(), "text/csv")},
        )
        assert r.status_code == 400


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_returns_db_status(self, public_client):
        r = await public_client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "database" in data
        assert "auth" in data
        assert data["version"] == "0.2.0"

    @pytest.mark.asyncio
    async def test_dedicated_health_endpoint(self, public_client):
        r = await public_client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("healthy", "degraded")
