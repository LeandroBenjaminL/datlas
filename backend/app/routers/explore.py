"""Explore router — data profiling and exploration endpoints.

Provides POST /api/explore/analyze to run a full EDA report
on an uploaded dataset: profile, distributions, correlations, and statistics.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas import ExploreAnalyzeRequest, ExploreAnalyzeResponse
from app.services.explorer import DataExplorer

router = APIRouter(prefix="/api", tags=["explore"])

try:
    DATA_RAW = Path("/app/data/raw")
    DATA_RAW.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    DATA_RAW = Path("data/raw")
    DATA_RAW.mkdir(parents=True, exist_ok=True)


@router.post("/explore/analyze", response_model=ExploreAnalyzeResponse)
async def explore_analyze(body: ExploreAnalyzeRequest):
    """Run a full exploratory analysis on an uploaded dataset.

    Returns a comprehensive report with:
    - Profile: shape, types, nulls, uniques, descriptive stats
    - Distributions: histogram bins and counts per numeric column
    - Correlations: Pearson matrix and strongest pairs
    - Statistics: skewness and kurtosis per numeric column

    Args:
        filename: Name of the CSV file already uploaded via POST /api/upload.

    Returns:
        dict: EDA report with profile, distributions, correlations, and statistics sections.

    Raises:
        HTTPException 404: If the file does not exist.
        HTTPException 400: If the file is not a .csv.
    """
    filepath = DATA_RAW / body.filename
    if not filepath.exists():
        raise HTTPException(404, f"File {body.filename} not found. Upload it first via POST /api/upload")
    if filepath.suffix != ".csv":
        raise HTTPException(400, "Only .csv files supported")

    explorer = DataExplorer(str(filepath))
    report = explorer.analyze()

    return {
        "filename": body.filename,
        "report": report,
        "message": "Exploration complete.",
    }
