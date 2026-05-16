"""Upload router — file ingestion endpoint.

Provides the POST /api/upload endpoint for uploading CSV files.
Validates file type, saves to disk, and returns basic dataset metadata.
"""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api", tags=["upload"])

DATA_DIR = Path("/app/data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and return dataset metadata.

    Args:
        file: The CSV file uploaded as multipart/form-data.

    Returns:
        dict: Dataset summary with filename, size, row/column count, and column names.

    Raises:
        HTTPException 400: If the file is not a .csv.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")

    content = await file.read()
    filepath = DATA_DIR / file.filename
    filepath.write_bytes(content)

    df = pd.read_csv(filepath)
    return {
        "filename": file.filename,
        "size_kb": round(len(content) / 1024, 2),
        "rows": len(df),
        "columns": len(df.columns),
        "col_names": list(df.columns),
        "status": "ok",
    }
