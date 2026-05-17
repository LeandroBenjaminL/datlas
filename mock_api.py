"""
Mock API para Datlas - Simula los endpoints reales
Útil para probar el frontend sin necesidad de Docker/PostgreSQL/pandas
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os

# Crear directorios necesarios
DATA_DIR = Path("./data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Datlas Mock API")

# CORS para permitir requests desde cualquier origen (frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- ENDPOINTS MOCK ----

@app.get("/")
async def root():
    return {"name": "Datlas Mock API", "status": "online", "docs": "/docs"}

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")
    
    content = await file.read()
    filepath = RAW_DIR / file.filename
    filepath.write_bytes(content)
    
    # Leer con pandas para obtener metadata real
    df = pd.read_csv(filepath)
    
    return {
        "filename": file.filename,
        "size_kb": round(len(content) / 1024, 2),
        "rows": len(df),
        "columns": len(df.columns),
        "col_names": list(df.columns),
        "status": "ok",
    }

@app.post("/api/clean/analyze")
async def analyze(filename: dict):
    filepath = RAW_DIR / filename["filename"]
    if not filepath.exists():
        raise HTTPException(404, f"File {filename['filename']} not found")
    
    # Análisis mock pero basado en datos reales
    df = pd.read_csv(filepath)
    
    # Detectar nulos
    nulls = {}
    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            nulls[col] = {
                "null_count": int(null_count),
                "null_percent": round(null_count / len(df) * 100, 2),
                "dtype": str(df[col].dtype),
                "suggested_fix": "fill with median" if pd.api.types.is_numeric_dtype(df[col]) else "fill with mode"
            }
    
    # Detectar outliers (IQR)
    outliers = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
        if outlier_count > 0:
            outliers[col] = {
                "outlier_count": int(outlier_count),
                "outlier_percent": round(outlier_count / len(df) * 100, 2),
                "lower_bound": round(lower, 2),
                "upper_bound": round(upper, 2)
            }
    
    # Detectar duplicados
    total_dupes = df.duplicated(keep=False).sum()
    duplicates = {
        "total_duplicate_rows": int(total_dupes),
        "duplicate_percent": round(total_dupes / len(df) * 100, 2),
        "columns_with_duplicates": {}
    }
    
    if total_dupes > 0:
        partial_mask = df.duplicated(subset=None, keep=False)
        dupe_df = df[partial_mask]
        for col in df.columns:
            col_dupes = dupe_df.duplicated(subset=[col], keep=False).sum()
            if col_dupes > 0:
                duplicates["columns_with_duplicates"][col] = int(col_dupes)
    
    # Detectar tipos
    types = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        possible_mismatch = None
        suggested_type = None
        
        # Simple check for type mismatches
        if dtype == "object":
            # Check if could be datetime
            try:
                pd.to_datetime(df[col].dropna().head(10))
                possible_mismatch = True
                suggested_type = "datetime"
            except:
                pass
            
            # Check if could be numeric
            try:
                pd.to_numeric(df[col].dropna().head(10))
                possible_mismatch = True
                suggested_type = "numeric"
            except:
                pass
        
        types[col] = {
            "detected_type": dtype,
            "sample_values": sample,
            "possible_mismatch": possible_mismatch,
            "suggested_type": suggested_type
        }
    
    return {
        "filename": filename["filename"],
        "report": {
            "original_shape": {"rows": len(df), "columns": len(df.columns)},
            "nulls": nulls,
            "outliers": outliers,
            "duplicates": duplicates,
            "types": types
        },
        "message": "Analysis complete. Call POST /api/clean/apply to apply fixes."
    }

@app.post("/api/clean/apply")
async def apply_cleaning(data: dict):
    filename = data["filename"]
    fixes = data.get("fixes", {})
    
    filepath = RAW_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found")
    
    df = pd.read_csv(filepath)
    original_shape = df.shape
    applied = []
    
    # Aplicar fixes
    if "fill_nulls" in fixes:
        for col, strategy in fixes["fill_nulls"].items():
            if col in df.columns:
                if strategy == "median" and pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                    applied.append(f"filled nulls in {col} with median")
                elif strategy == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
                    applied.append(f"filled nulls in {col} with mean")
                elif strategy == "mode":
                    mode_val = df[col].mode()
                    fill_val = mode_val.iloc[0] if not mode_val.empty else "N/A"
                    df[col] = df[col].fillna(fill_val)
                    applied.append(f"filled nulls in {col} with mode")
                else:
                    # Drop nulls
                    df = df.dropna(subset=[col])
                    applied.append(f"dropped nulls in {col}")
    
    if "remove_outliers" in fixes:
        for col in fixes["remove_outliers"]:
            if col in df.select_dtypes(include=[np.number]).columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                before = len(df)
                df = df[(df[col] >= lower) & (df[col] <= upper)]
                removed = before - len(df)
                applied.append(f"removed {removed} outliers from {col}")
    
    if fixes.get("remove_duplicates"):
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        applied.append(f"removed {removed} duplicate rows")
    
    # Guardar resultado
    output_path = PROCESSED_DIR / f"clean_{filename}"
    df.to_csv(output_path, index=False)
    
    return {
        "filename": filename,
        "analysis": {"message": "Analysis done"},
        "cleaning_result": {
            "original_shape": original_shape,
            "new_shape": df.shape,
            "rows_removed": original_shape[0] - len(df),
            "applied_fixes": applied
        },
        "download_url": f"/api/export/clean_{filename}"
    }

@app.get("/api/export/{filename}")
async def export_file(filename: str):
    filepath = PROCESSED_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='text/csv'
    )

if __name__ == "__main__":
    uvicorn.run("mock_api:app", host="0.0.0.0", port=8000, reload=True)