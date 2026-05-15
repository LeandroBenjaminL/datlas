"""Explore router — data profiling and exploration endpoints.

Provides POST /api/explore/analyze to run a full EDA report
on an uploaded dataset: profile, distributions, correlations, and statistics.
"""

from fastapi import APIRouter, HTTPException, Body
from pathlib import Path
from app.services.explorer import DataExplorer

router = APIRouter(prefix="/api", tags=["explore"])

DATA_RAW = Path("/app/data/raw")


@router.post("/explore/analyze")
async def explore_analyze(filename: str = Body(..., embed=True)):
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
    filepath = DATA_RAW / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found. Upload it first via POST /api/upload")
    if filepath.suffix != ".csv":
        raise HTTPException(400, "Only .csv files supported")

    explorer = DataExplorer(str(filepath))
    report = explorer.analyze()

    return {
        "filename": filename,
        "report": report,
        "message": "Exploration complete.",
    }
