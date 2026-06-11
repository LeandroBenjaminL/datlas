"""Pipeline router — automated upload → clean → explore in a single call.

All results are persisted in PostgreSQL for later retrieval.
File access uses tiered storage: local disk first, then PostgreSQL."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.crud import create_dataset, get_dataset_by_filename, save_analysis
from app.db.database import get_db
from app.schemas import PipelineResponse, PipelineRunRequest
from app.services.file_resolver import DATA_PROCESSED, DATA_RAW, ensure_file_local, store_file
from app.services.pipeline import PipelineService

router = APIRouter(prefix="/api", tags=["pipeline"])

pipeline = PipelineService(str(DATA_RAW), str(DATA_PROCESSED))


@router.post("/pipeline/upload", response_model=PipelineResponse)
async def pipeline_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV and run the full pipeline in one shot.

    Saves file to ephemeral disk, runs clean + explore, and persists
    everything in PostgreSQL.
    """
    filename = file.filename or "unnamed.csv"
    if not filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            400,
            f"El archivo ({size_mb:.1f}MB) excede el límite de {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Guardar en disco local
    store_file(filename, content, folder="raw")

    # Pipeline lo lee de disco (ya está en DATA_RAW tras store_file)
    try:
        result = pipeline.run(filename)
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e

    # Guardar cleaned en disco local
    processed_filename = f"clean_{filename}"
    processed_path = DATA_PROCESSED / processed_filename
    if processed_path.exists():
        with open(processed_path, "rb") as f:
            store_file(processed_filename, f.read(), folder="processed")

    # Persist dataset metadata + contenido CSV + pipeline report in PostgreSQL
    create_dataset(
        db,
        filename=filename,
        original_filename=filename,
        size_kb=result["upload_info"]["size_kb"],
        rows=result["upload_info"]["rows"],
        columns=result["upload_info"]["columns"],
        col_names=[],  # pipeline doesn't extract col_names explicitly
        content=content,
    )

    dataset = get_dataset_by_filename(db, filename)
    if dataset:
        save_analysis(db, dataset_id=dataset.id, analysis_type="pipeline", report=result)

    return result


@router.post("/pipeline/run", response_model=PipelineResponse)
async def pipeline_run(body: PipelineRunRequest, db: Session = Depends(get_db)):
    """Run the full pipeline on an already-uploaded file.

    Resolves the file via tiered storage: local first, then PostgreSQL.
    """
    try:
        ensure_file_local(body.filename, folder="raw", db=db)
    except FileNotFoundError:
        raise HTTPException(
            404,
            f"File {body.filename} not found. Upload it first via POST /api/upload",
        )

    try:
        result = pipeline.run(body.filename)
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e

    # Guardar cleaned en disco local
    processed_filename = f"clean_{body.filename}"
    processed_path = DATA_PROCESSED / processed_filename
    if processed_path.exists():
        with open(processed_path, "rb") as f:
            store_file(processed_filename, f.read(), folder="processed")

    # Persist pipeline report in PostgreSQL
    dataset = get_dataset_by_filename(db, body.filename)
    if dataset:
        save_analysis(db, dataset_id=dataset.id, analysis_type="pipeline", report=result)

    return result
