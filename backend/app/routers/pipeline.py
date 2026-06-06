"""Pipeline router — automated upload → clean → explore in a single call.

All results are persisted in PostgreSQL for later retrieval."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.crud import create_dataset, get_dataset_by_filename, save_analysis
from app.db.database import get_db
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
async def pipeline_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV and run the full pipeline in one shot.

    Saves file to ephemeral disk, runs clean + explore, and persists
    everything in PostgreSQL.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")

    content = await file.read()
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    try:
        result = pipeline.run(file.filename, raw_bytes=content)
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e

    # Persist dataset metadata + pipeline report in PostgreSQL
    create_dataset(
        db,
        filename=file.filename,
        original_filename=file.filename,
        size_kb=result["upload_info"]["size_kb"],
        rows=result["upload_info"]["rows"],
        columns=result["upload_info"]["columns"],
        col_names=[],  # pipeline doesn't extract col_names explicitly
    )

    dataset = get_dataset_by_filename(db, file.filename)
    if dataset:
        save_analysis(db, dataset_id=dataset.id, analysis_type="pipeline", report=result)

    return result


@router.post("/pipeline/run", response_model=PipelineResponse)
async def pipeline_run(body: PipelineRunRequest, db: Session = Depends(get_db)):
    """Run the full pipeline on an already-uploaded file."""
    raw_path = DATA_RAW / body.filename
    if not raw_path.exists():
        raise HTTPException(404, f"File {body.filename} not found. Upload it first via POST /api/upload")

    try:
        result = pipeline.run(body.filename)
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e

    # Persist pipeline report in PostgreSQL
    dataset = get_dataset_by_filename(db, body.filename)
    if dataset:
        save_analysis(db, dataset_id=dataset.id, analysis_type="pipeline", report=result)

    return result
