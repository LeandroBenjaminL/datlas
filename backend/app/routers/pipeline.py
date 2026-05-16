"""Pipeline router — automated upload → clean → explore in a single call."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pathlib import Path

from app.services.pipeline import PipelineService

router = APIRouter(prefix="/api", tags=["pipeline"])

DATA_RAW = Path("/app/data/raw")
DATA_PROCESSED = Path("/app/data/processed")

pipeline = PipelineService(str(DATA_RAW), str(DATA_PROCESSED))


@router.post("/pipeline/upload")
async def pipeline_upload(file: UploadFile = File(...)):
    """Upload a CSV and run the full pipeline automatically.

    One-shot: uploads the file, auto-cleans it (nulos, outliers, dupes),
    saves the cleaned version, and runs EDA — all in a single request.

    Args:
        file: The CSV file uploaded as multipart/form-data.

    Returns:
        dict: Combined pipeline report with upload_info, clean_report,
              cleaning_result, and explore_report sections.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")

    content = await file.read()
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    try:
        result = pipeline.run(file.filename, raw_bytes=content)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e


@router.post("/pipeline/run")
async def pipeline_run(filename: str = Body(..., embed=True)):
    """Run the pipeline on an already-uploaded dataset.

    Auto-cleans and explores a file that's already in data/raw/.

    Args:
        filename: Name of an existing CSV file in data/raw/.

    Returns:
        dict: Combined pipeline report.
    """
    raw_path = DATA_RAW / filename
    if not raw_path.exists():
        raise HTTPException(404, f"File {filename} not found. Upload it first via POST /api/upload")

    try:
        result = pipeline.run(filename)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}") from e
        result = pipeline.run(filename)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {str(e)}")
