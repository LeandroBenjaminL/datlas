from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import pandas as pd

router = APIRouter(prefix="/api", tags=["upload"])

DATA_DIR = Path("/app/data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
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
