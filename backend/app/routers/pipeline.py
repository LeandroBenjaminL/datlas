"""Pipeline router — automated upload → clean → explore in a single call."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import PipelineResponse, PipelineRunRequest
from app.services.pipeline import PipelineService

router = APIRouter(prefix="/api", tags=["pipeline"])

try:
    DATA_RAW = Path("/app/data/raw")
    DATA_PROCESSED = Path("/app/data/processed")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    pipeline = PipelineService(str(DATA_RAW), str(DATA_PROCESSED))
except (OSError, PermissionError):
    DATA_RAW = Path("data/raw")
    DATA_PROCESSED = Path("data/processed")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    pipeline = PipelineService(str(DATA_RAW), str(DATA_PROCESSED))


@router.post("/pipeline/upload", response_model=PipelineResponse)
async def pipeline_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")

    content = await file.read()
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    try:
        result = pipeline.run(file.filename, raw_bytes=content)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e


@router.post("/pipeline/run", response_model=PipelineResponse)
async def pipeline_run(body: PipelineRunRequest):
    raw_path = DATA_RAW / body.filename
    if not raw_path.exists():
        raise HTTPException(404, f"File {body.filename} not found. Upload it first via POST /api/upload")

    try:
        result = pipeline.run(body.filename)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e
