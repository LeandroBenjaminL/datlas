from fastapi import APIRouter, HTTPException, Body
from pathlib import Path
from app.services.cleaner import DataCleaner

router = APIRouter(prefix="/api", tags=["clean"])

DATA_RAW = Path("/app/data/raw")
DATA_PROCESSED = Path("/app/data/processed")
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


@router.post("/clean/analyze")
async def analyze(filename: str = Body(..., embed=True)):
    filepath = DATA_RAW / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found. Upload it first via POST /api/upload")
    if not filepath.suffix == ".csv":
        raise HTTPException(400, "Only .csv files supported")

    cleaner = DataCleaner(str(filepath))
    report = cleaner.analyze()

    return {
        "filename": filename,
        "report": report,
        "message": "Analysis complete. Call POST /api/clean/apply to apply fixes.",
    }


@router.post("/clean/apply")
async def apply_cleaning(
    filename: str = Body(...),
    fixes: dict = Body(default={}),
):
    filepath = DATA_RAW / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found")

    cleaner = DataCleaner(str(filepath))
    report = cleaner.analyze()
    result = cleaner.clean(fixes)

    output_path = DATA_PROCESSED / f"clean_{filename}"
    cleaner.df.to_csv(output_path, index=False)

    return {
        "filename": filename,
        "analysis": report,
        "cleaning_result": result,
        "download_url": f"/api/export/clean_{filename}",
    }
