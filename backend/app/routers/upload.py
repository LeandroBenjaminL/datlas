"""Upload router — file ingestion endpoint.

Provides the POST /api/upload endpoint for uploading CSV files.
Validates file type, saves to ephemeral disk, persists metadata in PostgreSQL,
and returns basic dataset metadata.
"""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.crud import create_dataset
from app.db.database import get_db
from app.schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])

try:
    DATA_DIR = Path("/app/data/raw")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    DATA_DIR = Path("data/raw")
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file, persist metadata in PostgreSQL, return summary.

    The raw CSV is saved to ephemeral disk for immediate processing.
    In production (Render), the file will be lost on the next deploy —
    download it while the session is active.

    Args:
        file: The CSV file uploaded as multipart/form-data.

    Returns:
        UploadResponse: Dataset summary with filename, size, row/column count,
                        and column names.

    Raises:
        HTTPException 400: If the file is not a .csv.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")

    content = await file.read()
    filepath = DATA_DIR / file.filename
    filepath.write_bytes(content)

    df = pd.read_csv(filepath)
    col_names = list(df.columns)
    size_kb = round(len(content) / 1024, 2)
    rows = len(df)
    columns = len(df.columns)

    # Persist metadata in PostgreSQL
    create_dataset(
        db,
        filename=file.filename,
        original_filename=file.filename,
        size_kb=size_kb,
        rows=rows,
        columns=columns,
        col_names=col_names,
    )

    return {
        "filename": file.filename,
        "size_kb": size_kb,
        "rows": rows,
        "columns": columns,
        "col_names": col_names,
        "status": "ok",
    }
