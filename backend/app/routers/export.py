"""Export router — file download and dataset listing endpoints.

Provides:
- GET /api/datasets — list all uploaded and processed datasets
- GET /api/download/{filename} — download a processed (or raw) file
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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


@router.get("/datasets")
async def list_datasets():
    """List all available datasets (raw + processed).

    Returns:
        dict: Lists of raw and processed CSV files with metadata.
    """
    raw_files = []
    if DATA_RAW.exists():
        for f in sorted(DATA_RAW.iterdir()):
            if f.suffix == ".csv":
                raw_files.append({"filename": f.name, "size_kb": round(f.stat().st_size / 1024, 2)})

    processed_files = []
    if DATA_PROCESSED.exists():
        for f in sorted(DATA_PROCESSED.iterdir()):
            if f.suffix == ".csv":
                processed_files.append({"filename": f.name, "size_kb": round(f.stat().st_size / 1024, 2)})

    return {"raw": raw_files, "processed": processed_files}


@router.get("/download/{filename:path}")
async def download_file(filename: str):
    """Download a processed or raw CSV file.

    Args:
        filename: Name of the file. Checks processed/ first, then raw/.

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
