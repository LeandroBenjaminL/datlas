"""Clean router — data analysis and cleaning endpoints.

Provides POST /api/clean/analyze to detect data quality issues
and POST /api/clean/apply to apply configurable fixes on an uploaded dataset.

All analysis reports are persisted in PostgreSQL for later retrieval.
Files are resolved via tiered storage: local first, then S3.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.crud import (
    get_dataset_by_filename,
    save_analysis,
    update_dataset_status,
)
from app.db.database import get_db
from app.schemas import (
    CleanAnalyzeRequest,
    CleanAnalyzeResponse,
    CleanApplyRequest,
    CleanApplyResponse,
)
from app.services.cleaner import DataCleaner
from app.services.file_resolver import DATA_PROCESSED, ensure_file_local, store_file

router = APIRouter(prefix="/api", tags=["clean"])


@router.post("/clean/analyze", response_model=CleanAnalyzeResponse)
async def analyze(body: CleanAnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze a dataset and detect data quality issues.

    Scans the file for null values, outliers (IQR method), duplicate rows,
    and type mismatches. Returns a structured report with per-column findings.
    The report is persisted in PostgreSQL.

    Args:
        filename: Name of the CSV file already uploaded via POST /api/upload.

    Returns:
        dict: Report with original shape, nulls, outliers, duplicates, and type analysis.

    Raises:
        HTTPException 404: If the file does not exist locally or in S3.
        HTTPException 400: If the file is not a .csv.
    """
    if not body.filename.endswith(".csv"):
        raise HTTPException(400, "Only .csv files supported")

    try:
        filepath = ensure_file_local(body.filename, folder="raw", db=db)
    except FileNotFoundError:
        raise HTTPException(
            404,
            f"File {body.filename} not found. Upload it first via POST /api/upload",
        )

    cleaner = DataCleaner(str(filepath))
    report = cleaner.analyze()

    # Persist analysis in PostgreSQL
    dataset = get_dataset_by_filename(db, body.filename)
    if dataset:
        save_analysis(db, dataset_id=dataset.id, analysis_type="clean", report=report)

    return {
        "filename": body.filename,
        "report": report,
        "message": "Analysis complete. Call POST /api/clean/apply to apply fixes.",
    }


@router.post("/clean/apply", response_model=CleanApplyResponse)
async def apply_cleaning(body: CleanApplyRequest, db: Session = Depends(get_db)):
    """Apply cleaning fixes to a dataset.

    Runs the configured fixes (fill nulls, remove outliers, drop duplicates)
    and saves the cleaned dataset to data/processed/. Results are persisted
    in PostgreSQL.

    Args:
        filename: Name of the CSV file already uploaded.
        fixes: Optional dict specifying which fixes to apply.
               Example: {"fill_nulls": {"edad": "median"}, "remove_outliers": ["edad"], "remove_duplicates": true}

    Returns:
        dict: Analysis report plus cleaning result with shape changes and applied fixes.

    Raises:
        HTTPException 404: If the file does not exist locally or in DB.
    """
    if not body.filename.endswith(".csv"):
        raise HTTPException(400, "Only .csv files supported")

    try:
        filepath = ensure_file_local(body.filename, folder="raw", db=db)
    except FileNotFoundError:
        raise HTTPException(
            404,
            f"File {body.filename} not found. Upload it first via POST /api/upload",
        )

    cleaner = DataCleaner(str(filepath))
    report = cleaner.analyze()
    result = cleaner.clean(body.fixes)

    # Guardar cleaned en local
    output_filename = f"clean_{body.filename}"
    output_path = DATA_PROCESSED / output_filename
    cleaner.df.to_csv(output_path, index=False)

    with open(output_path, "rb") as f:
        store_file(output_filename, f.read(), folder="processed")

    # Persist analysis + cleaning result in PostgreSQL
    dataset = get_dataset_by_filename(db, body.filename)
    if dataset:
        combined_report = {"analysis": report, "cleaning_result": result}
        save_analysis(db, dataset_id=dataset.id, analysis_type="clean_apply", report=combined_report)
        update_dataset_status(db, dataset.id, status="cleaned")

    return {
        "filename": body.filename,
        "analysis": report,
        "cleaning_result": result,
        "download_url": f"/api/download/{output_filename}",
    }
