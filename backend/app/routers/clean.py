"""Clean router — data analysis and cleaning endpoints.

Provides POST /api/clean/analyze to detect data quality issues
and POST /api/clean/apply to apply configurable fixes on an uploaded dataset.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas import (
    CleanAnalyzeRequest,
    CleanAnalyzeResponse,
    CleanApplyRequest,
    CleanApplyResponse,
)
from app.services.cleaner import DataCleaner

router = APIRouter(prefix="/api", tags=["clean"])

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


@router.post("/clean/analyze", response_model=CleanAnalyzeResponse)
async def analyze(body: CleanAnalyzeRequest):
    """Analyze a dataset and detect data quality issues.

    Scans the file for null values, outliers (IQR method), duplicate rows,
    and type mismatches. Returns a structured report with per-column findings.

    Args:
        filename: Name of the CSV file already uploaded via POST /api/upload.

    Returns:
        dict: Report with original shape, nulls, outliers, duplicates, and type analysis.

    Raises:
        HTTPException 404: If the file does not exist in data/raw/.
        HTTPException 400: If the file is not a .csv.
    """
    filepath = DATA_RAW / body.filename
    if not filepath.exists():
        raise HTTPException(404, f"File {body.filename} not found. Upload it first via POST /api/upload")
    if not filepath.suffix == ".csv":
        raise HTTPException(400, "Only .csv files supported")

    cleaner = DataCleaner(str(filepath))
    report = cleaner.analyze()

    return {
        "filename": body.filename,
        "report": report,
        "message": "Analysis complete. Call POST /api/clean/apply to apply fixes.",
    }


@router.post("/clean/apply", response_model=CleanApplyResponse)
async def apply_cleaning(body: CleanApplyRequest):
    """Apply cleaning fixes to a dataset.

    Runs the configured fixes (fill nulls, remove outliers, drop duplicates)
    and saves the cleaned dataset to data/processed/.

    Args:
        filename: Name of the CSV file already uploaded.
        fixes: Optional dict specifying which fixes to apply.
               Example: {"fill_nulls": {"edad": "median"}, "remove_outliers": ["edad"], "remove_duplicates": true}

    Returns:
        dict: Analysis report plus cleaning result with shape changes and applied fixes.

    Raises:
        HTTPException 404: If the file does not exist.
    """
    filepath = DATA_RAW / body.filename
    if not filepath.exists():
        raise HTTPException(404, f"File {body.filename} not found")

    cleaner = DataCleaner(str(filepath))
    report = cleaner.analyze()
    result = cleaner.clean(body.fixes)

    output_path = DATA_PROCESSED / f"clean_{body.filename}"
    cleaner.df.to_csv(output_path, index=False)

    return {
        "filename": body.filename,
        "analysis": report,
        "cleaning_result": result,
        "download_url": f"/api/download/clean_{body.filename}",
    }
