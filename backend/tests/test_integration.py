"""Integration tests — real API calls via httpx with test database."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

FIXTURE_DIR = Path(__file__).parent / "data"


@pytest.fixture
async def client(app_with_db):
    """Async HTTP client bound to the FastAPI app with DB overrides."""
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("healthy", "degraded", "online")


@pytest.mark.asyncio
async def test_upload(client):
    csv_path = FIXTURE_DIR / "test.csv"
    r = await client.post("/api/upload", files={"file": ("test.csv", csv_path.read_bytes(), "text/csv")})
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test.csv"
    assert data["rows"] == 10
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_clean_analyze(client):
    r = await client.post("/api/clean/analyze", json={"filename": "test.csv"})
    assert r.status_code == 200
    data = r.json()
    assert "report" in data
    assert "nulls" in data["report"]
    assert "outliers" in data["report"]


@pytest.mark.asyncio
async def test_clean_apply(client):
    r = await client.post(
        "/api/clean/apply",
        json={
            "filename": "test.csv",
            "fixes": {"fill_nulls": {"edad": "median"}, "remove_duplicates": True},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "cleaning_result" in data
    assert len(data["cleaning_result"]["applied_fixes"]) >= 2


@pytest.mark.asyncio
async def test_explore(client):
    r = await client.post("/api/explore/analyze", json={"filename": "test.csv"})
    assert r.status_code == 200
    data = r.json()
    assert "report" in data
    assert "profile" in data["report"]


@pytest.mark.asyncio
async def test_datasets(client):
    r = await client.get("/api/datasets")
    assert r.status_code == 200
    data = r.json()
    assert "raw" in data
    assert "processed" in data


@pytest.mark.asyncio
async def test_dataset_analyses(client):
    """New endpoint: GET /api/datasets/{id}/analyses."""
    # First ensure a dataset exists
    csv_path = FIXTURE_DIR / "test.csv"
    await client.post("/api/upload", files={"file": ("test.csv", csv_path.read_bytes(), "text/csv")})

    r = await client.get("/api/datasets/1/analyses")
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test.csv"
    assert "analyses" in data


@pytest.mark.asyncio
async def test_dataset_analyses_not_found(client):
    r = await client.get("/api/datasets/999/analyses")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_pipeline_upload(client):
    csv_path = FIXTURE_DIR / "test.csv"
    r = await client.post(
        "/api/pipeline/upload",
        files={"file": ("test.csv", csv_path.read_bytes(), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "upload_info" in data
    assert "clean_report" in data
    assert "explore_report" in data


@pytest.mark.asyncio
async def test_pipeline_run(client):
    r = await client.post("/api/pipeline/run", json={"filename": "test.csv"})
    assert r.status_code == 200
    data = r.json()
    assert "upload_info" in data
    assert "cleaning_result" in data


@pytest.mark.asyncio
async def test_download(client):
    r = await client.get("/api/download/test.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


@pytest.mark.asyncio
async def test_upload_rejects_non_csv(client):
    r = await client.post("/api/upload", files={"file": ("bad.txt", b"a,b,c\n1,2,3", "text/plain")})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_clean_nonexistent(client):
    r = await client.post("/api/clean/analyze", json={"filename": "noexiste.csv"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_pipeline_nonexistent(client):
    r = await client.post("/api/pipeline/run", json={"filename": "noexiste.csv"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_download_nonexistent(client):
    r = await client.get("/api/download/noexiste.csv")
    assert r.status_code == 404
