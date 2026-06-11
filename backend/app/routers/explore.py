"""Explore router — data profiling and exploration endpoints.

Provides POST /api/explore/analyze to run a full EDA report
on an uploaded dataset: profile, distributions, correlations, and statistics.

All analysis reports are persisted in PostgreSQL for later retrieval.
The file is resolved via tiered storage: local first, then S3.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.crud import get_dataset_by_filename, save_analysis
from app.db.database import get_db
from app.schemas import ExploreAnalyzeRequest, ExploreAnalyzeResponse
from app.services.explorer import DataExplorer
from app.services.file_resolver import ensure_file_local

router = APIRouter(prefix="/api", tags=["explore"])


@router.post("/explore/analyze", response_model=ExploreAnalyzeResponse)
async def explore_analyze(body: ExploreAnalyzeRequest, db: Session = Depends(get_db)):
    """Run a full exploratory analysis on an uploaded dataset.

    Returns a comprehensive report with:
    - Profile: shape, types, nulls, uniques, descriptive stats
    - Distributions: histogram bins and counts per numeric column
    - Correlations: Pearson matrix and strongest pairs
    - Statistics: skewness and kurtosis per numeric column

    The report is persisted in PostgreSQL.

    Args:
        filename: Name of the CSV file already uploaded via POST /api/upload.

    Returns:
        dict: EDA report with profile, distributions, correlations, and statistics sections.

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

    explorer = DataExplorer(str(filepath))
    report = explorer.analyze()

    # Persist analysis in PostgreSQL
    dataset = get_dataset_by_filename(db, body.filename)
    if dataset:
        save_analysis(db, dataset_id=dataset.id, analysis_type="explore", report=report)

    return {
        "filename": body.filename,
        "report": report,
        "message": "Exploration complete.",
    }
