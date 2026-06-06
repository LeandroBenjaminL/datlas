"""Export router — file download and dataset listing endpoints.

Provides:
- GET /api/datasets — list all uploaded and processed datasets (from PostgreSQL)
- GET /api/download/{filename} — download a processed (or raw) file
- GET /api/datasets/{dataset_id}/analyses — get analysis history for a dataset
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.crud import get_analyses, get_dataset_by_id, list_datasets
from app.db.database import get_db
from app.schemas import DatasetInfo, DatasetsResponse

router = APIRouter(prefix="/api", tags=["export"])

try:
    DATA_RAW = Path("/app/data/raw")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED = Path("/app/data/processed")
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    DATA_RAW = Path("data/raw")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED = Path("data/processed")
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


@router.get("/datasets", response_model=DatasetsResponse)
async def list_datasets_endpoint(db: Session = Depends(get_db)):
    """List all available datasets from PostgreSQL metadata.

    Returns datasets ordered by upload time (newest first).

    Returns:
        DatasetsResponse: Lists of raw and processed datasets.
    """
    datasets = list_datasets(db)
    raw_files: list[DatasetInfo] = []
    processed_files: list[DatasetInfo] = []

    for ds in datasets:
        info = DatasetInfo(filename=ds.filename, size_kb=ds.size_kb)
        if ds.status == "cleaned":
            processed_files.append(info)
        else:
            raw_files.append(info)

    return DatasetsResponse(raw=raw_files, processed=processed_files)


@router.get("/datasets/{dataset_id}/analyses")
async def dataset_analyses(dataset_id: int, db: Session = Depends(get_db)):
    """Return all analysis reports for a dataset.

    Args:
        dataset_id: The dataset primary key.

    Returns:
        list: Analysis results ordered by creation time (newest first).

    Raises:
        HTTPException 404: If the dataset does not exist.
    """
    dataset = get_dataset_by_id(db, dataset_id)
    if not dataset:
        raise HTTPException(404, f"Dataset {dataset_id} not found")

    analyses = get_analyses(db, dataset_id)
    return {
        "dataset_id": dataset_id,
        "filename": dataset.filename,
        "analyses": [
            {
                "id": a.id,
                "type": a.analysis_type,
                "report": a.report,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ],
    }


@router.get("/download/{filename:path}")
async def download_file(filename: str):
    """Download a processed or raw CSV file.

    Checks processed/ first, then raw/. Files are ephemeral in production —
    download them during the active session.

    Args:
        filename: Name of the file.

    Returns:
        FileResponse: The CSV file as a download.

    Raises:
        HTTPException 404: If the file is not found.
    """
    processed_path = DATA_PROCESSED / filename
    raw_path = DATA_RAW / filename

    if processed_path.exists():
        return FileResponse(
            str(processed_path),
            media_type="text/csv",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    elif raw_path.exists():
        return FileResponse(
            str(raw_path),
            media_type="text/csv",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        raise HTTPException(404, f"File {filename} not found")
