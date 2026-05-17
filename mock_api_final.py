"""
Simple Mock API para Datlas - Sin dependencias externas
Usa solo módulos built-in de Python (csv, json, etc.)
Perfecto para Windows sin necesidad de compilar nada
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import csv
import json
import os
from pathlib import Path
import statistics
import math
from typing import List, Dict, Any, Optional

# Crear directorios necesarios
DATA_DIR = Path("./data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Datlas Simple Mock API")

# CORS para permitir requests desde cualquier origen (frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for uploaded files (in memory for demo)
uploaded_files = {}

def read_csv_file(filepath: Path) -> List[Dict[str, Any]]:
    """Read CSV file and return list of dictionaries"""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv_file(filepath: Path, data: List[Dict[str, Any]], fieldnames: List[str]):
    """Write list of dictionaries to CSV file"""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def is_numeric(value: str) -> bool:
    """Check if a string value is numeric"""
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_float(value: str) -> bool:
    """Check if a string value is a float"""
    try:
        float(value)
        return '.' in value
    except ValueError:
        return False

def is_int(value: str) -> bool:
    """Check if a string value is an integer"""
    try:
        int(value)
        return '.' not in value
    except ValueError:
        return False

def safe_float(value: str) -> Optional[float]:
    """Safely convert string to float, return None if not possible"""
    try:
        return float(value)
    except ValueError:
        return None

def safe_int(value: str) -> Optional[int]:
    """Safely convert string to int, return None if not possible"""
    try:
        return int(value)
    except ValueError:
        return None

def calculate_iqr_bounds(values: List[float]) -> tuple:
    """Calculate IQR bounds for outlier detection"""
    if len(values) < 4:
        return None, None
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    q1 = sorted_values[n // 4]
    q3 = sorted_values[3 * n // 4]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return lower_bound, upper_bound

def analyze_column_types_and_missing(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze column types, missing values, and suggest fixes"""
    if not rows:
        return {}
    
    columns = list(rows[0].keys())
    analysis = {}
    
    for col in columns:
        values = [row[col] for row in rows if row[col] and row[col].strip()]
        missing_count = len([row for row in rows if not row[col] or not row[col].strip()])
        missing_percent = round((missing_count / len(rows)) * 100, 2) if rows else 0
        
        # Determine column type
        numeric_values = [safe_float(v) for v in values if safe_float(v) is not None]
        int_values = [safe_int(v) for v in values if safe_int(v) is not None]
        
        # Check if all numeric values are actually integers
        all_integers = all(isinstance(v, int) and float(v).is_integer() for v in numeric_values) if numeric_values else False
        
        if len(numeric_values) == len(values) and len(values) > 0:
            # All values are numeric
            if all_integers:
                detected_type = "integer"
                suggested_fix = "fill with median"
            else:
                detected_type = "float"
                suggested_fix = "fill with median"
        elif len([v for v in values if v.replace('-', '').replace('.', '').isdigit()]) == len(values) and len(values) > 0:
            # All values look like numbers (with possible minus/decimal points)
            detected_type = "numeric"
            suggested_fix = "fill with median"
        else:
            # Treat as string/categorical
            detected_type = "string"
            suggested_fix = "fill with mode"
        
        analysis[col] = {
            "missing_count": missing_count,
            "missing_percent": missing_percent,
            "detected_type": detected_type,
            "suggested_fix": suggested_fix,
            "sample_values": values[:3] if values else []
        }
    
    return analysis

def detect_outliers_iqr(rows: List[Dict[str, Any]], column: str) -> Dict[str, Any]:
    """Detect outliers using IQR method for a specific column"""
    values = []
    for row in rows:
        val = row[column]
        if val and val.strip():
            num_val = safe_float(val)
            if num_val is not None:
                values.append(num_val)
    
    if len(values) < 4:
        return {"outlier_count": 0, "outlier_percent": 0, "lower_bound": None, "upper_bound": None}
    
    lower_bound, upper_bound = calculate_iqr_bounds(values)
    if lower_bound is None or upper_bound is None:
        return {"outlier_count": 0, "outlier_percent": 0, "lower_bound": None, "upper_bound": None}
    
    outliers = [v for v in values if v < lower_bound or v > upper_bound]
    outlier_count = len(outliers)
    outlier_percent = round((outlier_count / len(values)) * 100, 2) if values else 0
    
    return {
        "outlier_count": outlier_count,
        "outlier_percent": outlier_percent,
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2)
    }

def detect_duplicates(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect duplicate rows"""
    # Convert rows to tuples for hashable comparison
    row_tuples = [tuple(sorted(row.items())) for row in rows]
    seen = set()
    duplicates = []
    
    for i, row_tuple in enumerate(row_tuples):
        if row_tuple in seen:
            duplicates.append(i)
        else:
            seen.add(row_tuple)
    
    total_dupes = len(duplicates)
    duplicate_percent = round((total_dupes / len(rows)) * 100, 2) if rows else 0
    
    # Find which columns have duplicates in duplicate rows
    columns_with_duplicates = {}
    if duplicates and rows:
        duplicate_rows = [rows[i] for i in duplicates]
        columns = list(rows[0].keys())
        
        for col in columns:
            col_values = [row[col] for row in duplicate_rows if row[col] and row[col].strip()]
            if len(col_values) != len(set(col_values)):  # Has duplicates
                # Count duplicates per value
                from collections import Counter
                value_counts = Counter(col_values)
                dup_count = sum(count - 1 for count in value_counts.values() if count > 1)
                if dup_count > 0:
                    columns_with_duplicates[col] = dup_count
    
    return {
        "total_duplicate_rows": total_dupes,
        "duplicate_percent": duplicate_percent,
        "columns_with_duplicates": columns_with_duplicates
    }

# ---- ENDPOINTS ----

@app.get("/")
async def root():
    return {"name": "Datlas Simple Mock API", "status": "online", "version": "0.1.0"}

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "Solo archivos .csv")
    
    content = await file.read()
    filepath = RAW_DIR / file.filename
    filepath.write_bytes(content)
    
    # Read CSV to get metadata
    try:
        rows = read_csv_file(filepath)
        if not rows:
            raise HTTPException(400, "El archivo CSV está vacío")
        
        col_names = list(rows[0].keys()) if rows else []
        
        return {
            "filename": file.filename,
            "size_kb": round(len(content) / 1024, 2),
            "rows": len(rows),
            "columns": len(col_names),
            "col_names": col_names,
            "status": "ok",
        }
    except Exception as e:
        raise HTTPException(400, f"Error al leer CSV: {str(e)}")

@app.post("/api/clean/analyze")
async def analyze(data: dict):
    filename = data.get("filename")
    if not filename:
        raise HTTPException(400, "Filename is required")
    
    filepath = RAW_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found. Upload it first via POST /api/upload")
    
    try:
        rows = read_csv_file(filepath)
        if not rows:
            raise HTTPException(400, "El archivo CSV está vacío")
        
        # Analysis
        nulls_analysis = analyze_column_types_and_missing(rows)
        
        # Format nulls analysis for response
        nulls_formatted = {}
        for col, analysis in nulls_analysis.items():
            if analysis["missing_count"] > 0:
                nulls_formatted[col] = {
                    "null_count": analysis["missing_count"],
                    "null_percent": analysis["missing_percent"],
                    "dtype": analysis["detected_type"],
                    "suggested_fix": analysis["suggested_fix"]
                }
        
        # Detect outliers for numeric columns
        outliers_formatted = {}
        for col in nulls_analysis.keys():
            col_analysis = nulls_analysis[col]
            if col_analysis["detected_type"] in ["integer", "float", "numeric"]:
                outlier_result = detect_outliers_iqr(rows, col)
                if outlier_result["outlier_count"] > 0:
                    outliers_formatted[col] = outlier_result
        
        # Detect duplicates
        duplicates_result = detect_duplicates(rows)
        
        # Types analysis (simplified)
        types_formatted = {}
        for col, analysis in nulls_analysis.items():
            sample_vals = analysis["sample_values"][:3]
            types_formatted[col] = {
                "detected_type": analysis["detected_type"],
                "sample_values": sample_vals,
                "possible_mismatch": False,  # Simplified
                "suggested_type": None
            }
        
        report = {
            "original_shape": {
                "rows": len(rows),
                "columns": len(rows[0].keys()) if rows else 0
            },
            "nulls": nulls_formatted,
            "outliers": outliers_formatted,
            "duplicates": duplicates_result,
            "types": types_formatted
        }
        
        return {
            "filename": filename,
            "report": report,
            "message": "Analysis complete. Call POST /api/clean/apply to apply fixes."
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error during analysis: {str(e)}")

@app.post("/api/clean/apply")
async def apply_cleaning(data: dict):
    filename = data.get("filename")
    fixes = data.get("fixes", {})
    
    if not filename:
        raise HTTPException(400, "Filename is required")
    
    filepath = RAW_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, f"File {filename} not found")
    
    try:
        rows = read_csv_file(filepath)
        if not rows:
            raise HTTPException(400, "El archivo CSV está vacío")
        
        original_shape = (len(rows), len(rows[0].keys()) if rows else 0)
        applied_fixes = []
        
        # Work on a copy
        processed_rows = [dict(row) for row in rows]
        
        # Apply null fixes
        if "fill_nulls" in fixes:
            for col, strategy in fixes["fill_nulls"].items():
                if col not in rows[0] if rows else True:
                    continue
                
                # Get column values for calculating fix values
                col_values = [row[col] for row in rows if row[col] and row[col].strip()]
                
                if strategy == "median":
                    # Calculate median
                    numeric_vals = [safe_float(v) for v in col_values if safe_float(v) is not None]
                    if numeric_vals:
                        median_val = statistics.median(numeric_vals)
                        for row in processed_rows:
                            if not row[col] or not row[col].strip():
                                row[col] = str(median_val)
                        applied_fixes.append(f"filled nulls in {col} with median ({median_val})")
                
                elif strategy == "mean":
                    # Calculate mean
                    numeric_vals = [safe_float(v) for v in col_values if safe_float(v) is not None]
                    if numeric_vals:
                        mean_val = statistics.mean(numeric_vals)
                        for row in processed_rows:
                            if not row[col] or not row[col].strip():
                                row[col] = str(mean_val)
                        applied_fixes.append(f"filled nulls in {col} with mean ({mean_val:.2f})")
                
                elif strategy == "mode":
                    # Calculate mode
                    from collections import Counter
                    if col_values:
                        mode_val = Counter(col_values).most_common(1)[0][0]
                        for row in processed_rows:
                            if not row[col] or not row[col].strip():
                                row[col] = mode_val
                        applied_fixes.append(f"filled nulls in {col} with mode ('{mode_val}')")
                
                else:  # drop
                    # Remove rows with nulls in this column
                    before_len = len(processed_rows)
                    processed_rows = [row for row in processed_rows if row[col] and row[col].strip()]
                    removed_count = before_len - len(processed_rows)
                    if removed_count > 0:
                        applied_fixes.append(f"dropped {removed_count} rows with nulls in {col}")
        
        # Apply outlier removal
        if "remove_outliers" in fixes:
            for col in fixes["remove_outliers"]:
                if col not in rows[0] if rows else True:
                    continue
                
                # Get numeric values for IQR calculation
                numeric_vals = []
                valid_rows = []
                for i, row in enumerate(processed_rows):
                    val = row[col]
                    if val and val.strip():
                        num_val = safe_float(val)
                        if num_val is not None:
                            numeric_vals.append(num_val)
                            valid_rows.append((i, num_val))
                
                if len(numeric_vals) >= 4:
                    lower_bound, upper_bound = calculate_iqr_bounds(numeric_vals)
                    if lower_bound is not None and upper_bound is not None:
                        # Keep only rows within bounds
                        kept_rows = []
                        removed_count = 0
                        for i, (orig_idx, num_val) in enumerate(valid_rows):
                            if lower_bound <= num_val <= upper_bound:
                                kept_rows.append(processed_rows[orig_idx])
                            else:
                                removed_count += 1
                        
                        # Also keep rows that had null/empty values in this column
                        for row in processed_rows:
                            if not row[col] or not row[col].strip():
                                kept_rows.append(row)
                        
                        processed_rows = kept_rows
                        if removed_count > 0:
                            applied_fixes.append(f"removed {removed_count} outliers from {col}")
        
        # Apply duplicate removal
        if fixes.get("remove_duplicates"):
            # Convert to tuples for deduplication, keep first occurrence
            seen = set()
            unique_rows = []
            removed_count = 0
            
            for row in processed_rows:
                row_tuple = tuple(sorted(row.items()))
                if row_tuple not in seen:
                    seen.add(row_tuple)
                    unique_rows.append(row)
                else:
                    removed_count += 1
            
            if removed_count > 0:
                processed_rows = unique_rows
                applied_fixes.append(f"removed {removed_count} duplicate rows")
        
        # Save processed file
        output_filename = f"clean_{filename}"
        output_path = PROCESSED_DIR / output_filename
        
        if processed_rows:
            fieldnames = list(processed_rows[0].keys())
            write_csv_file(output_path, processed_rows, fieldnames)
        else:
            # Create empty file with headers if no rows remain
            if rows:
                fieldnames = list(rows[0].keys())
                write_csv_file(output_path, [], fieldnames)
        
        new_shape = (len(processed_rows), len(processed_rows[0].keys()) if processed_rows else 0)
        rows_removed = original_shape[0] - new_shape[0]
        
        return {
            "filename": filename,
            "analysis": {"message": "Analysis done"},
            "cleaning_result": {
                "original_shape": original_shape,
                "new_shape": new_shape,
                "rows_removed": rows_removed,
                "applied_fixes": applied_fixes
            },
            "download_url": f"/api/export/{output_filename}"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error during cleaning: {str(e)}")

@app.get("/api/export/{filename}")
async def export_file(filename: str):
    filepath = PROCESSED_DIR / filename
    if not filepath.exists():
        # Also check in raw directory for backwards compatibility
        filepath_alt = RAW_DIR / filename
        if not filepath_alt.exists():
            raise HTTPException(404, f"File {filename} not found")
        filepath = filepath_alt
    
    # Return file as download
    from fastapi.responses import FileResponse
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='text/csv'
    )

if __name__ == "__main__":
    print("Starting Datlas Simple Mock API...")
    print("Docs available at http://localhost:8000/docs")
    print("Tip: This version works without pandas/numpy compilation!")
    uvicorn.run("mock_api_final:app", host="0.0.0.0", port=8000, reload=True)