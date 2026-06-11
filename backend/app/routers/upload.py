"""Upload router — file ingestion endpoint.

Provides the POST /api/upload endpoint for uploading CSV files.
Validates file type, saves to disk and S3, persists metadata in PostgreSQL,
and returns basic dataset metadata.
"""

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.crud import create_dataset
from app.db.database import get_db
from app.schemas import UploadResponse
from app.services.file_resolver import DATA_RAW, store_file

router = APIRouter(prefix="/api", tags=["upload"])


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

    filepath = DATA_RAW / filename
    df = pd.read_csv(filepath)
    col_names = list(df.columns)
    size_kb = round(len(content) / 1024, 2)
    rows = len(df)
    columns = len(df.columns)

    # Persist metadata + contenido CSV en PostgreSQL (sobrevive deploys en Render)
    create_dataset(
        db,
        filename=filename,
        original_filename=filename,
        size_kb=size_kb,
        rows=rows,
        columns=columns,
        col_names=col_names,
        content=content,
    )

    return {
        "filename": filename,
        "size_kb": size_kb,
        "rows": rows,
        "columns": columns,
        "col_names": col_names,
        "status": "ok",
    }
