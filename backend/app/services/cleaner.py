import pandas as pd
import numpy as np
from pathlib import Path


class DataCleaner:
    def __init__(self, filepath: str):
        self.df = pd.read_csv(filepath)
        self.original_shape = self.df.shape
        self.report = {}

    def detect_nulls(self) -> dict:
        null_counts = self.df.isnull().sum()
        null_percent = (null_counts / len(self.df) * 100).round(2)
        null_cols = null_counts[null_counts > 0]

        result = {}
        for col in null_cols.index:
            result[col] = {
                "null_count": int(null_counts[col]),
                "null_percent": float(null_percent[col]),
                "dtype": str(self.df[col].dtype),
                "suggested_fix": self._suggest_null_fix(col),
            }
        return result

    def _suggest_null_fix(self, col: str) -> str:
        dtype = self.df[col].dtype
        if pd.api.types.is_numeric_dtype(dtype):
            return "fill with median"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "fill with mode (most frequent)"
        else:
            return "fill with mode (most frequent)"

    def detect_outliers(self) -> dict:
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric_cols:
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = self.df[(self.df[col] < lower) | (self.df[col] > upper)]
            if not outliers.empty:
                result[col] = {
                    "outlier_count": len(outliers),
                    "outlier_percent": round(len(outliers) / len(self.df) * 100, 2),
                    "lower_bound": round(lower, 2),
                    "upper_bound": round(upper, 2),
                }
        return result

    def detect_duplicates(self) -> dict:
        total_dupes = self.df.duplicated(keep=False).sum()
        partial_mask = self.df.duplicated(subset=None, keep=False)
        partial_cols = {}
        if total_dupes > 0:
            dupe_df = self.df[partial_mask]
            for col in self.df.columns:
                col_dupes = dupe_df.duplicated(subset=[col], keep=False).sum()
                if col_dupes > 0:
                    partial_cols[col] = int(col_dupes)
        return {
            "total_duplicate_rows": int(total_dupes),
            "duplicate_percent": round(total_dupes / len(self.df) * 100, 2),
            "columns_with_duplicates": partial_cols,
        }

    def detect_types(self) -> dict:
        result = {}
        for col in self.df.columns:
            dtype = self.df[col].dtype
            sample = self.df[col].dropna().head(3).tolist()
            correction = self._check_type_mismatch(col)
            result[col] = {
                "detected_type": str(dtype),
                "sample_values": sample[:3],
                "possible_mismatch": correction is not None,
                "suggested_type": correction,
            }
        return result

    def _check_type_mismatch(self, col: str) -> str | None:
        sample = self.df[col].dropna().astype(str).head(20)
        if sample.empty:
            return None
        try:
            pd.to_datetime(sample)
            if self.df[col].dtype != "datetime64[ns]":
                return "datetime"
        except (ValueError, TypeError):
            pass
        try:
            numeric_sample = sample.str.replace(",", ".", regex=False)
            numeric_sample = numeric_sample.str.extract(r"^(-?\d+[.]?\d*)$", expand=False)
            numeric_sample = numeric_sample.dropna()
            if len(numeric_sample) >= len(sample) * 0.8:
                if self.df[col].dtype not in ["int64", "float64"]:
                    return "numeric"
        except Exception:
            pass
        return None

    def analyze(self) -> dict:
        self.report = {
            "original_shape": {
                "rows": self.original_shape[0],
                "columns": self.original_shape[1],
            },
            "nulls": self.detect_nulls(),
            "outliers": self.detect_outliers(),
            "duplicates": self.detect_duplicates(),
            "types": self.detect_types(),
        }
        return self.report

    def clean(self, fixes: dict | None = None) -> dict:
        df = self.df.copy()
        applied = []

        fixes = fixes or {}

        if fixes.get("fill_nulls"):
            for col, strategy in fixes["fill_nulls"].items():
                if col not in df.columns:
                    continue
                if strategy == "median" and pd.api.types.is_numeric_dtype(df[col].dtype):
                    df[col] = df[col].fillna(df[col].median())
                    applied.append(f"filled nulls in {col} with median")
                elif strategy == "mean" and pd.api.types.is_numeric_dtype(df[col].dtype):
                    df[col] = df[col].fillna(df[col].mean())
                    applied.append(f"filled nulls in {col} with mean")
                elif strategy == "mode":
                    df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "N/A")
                    applied.append(f"filled nulls in {col} with mode")
                else:
                    df[col] = df[col].dropna()
                    applied.append(f"dropped nulls in {col}")

        if fixes.get("remove_outliers"):
            for col in fixes["remove_outliers"]:
                if col not in df.select_dtypes(include=[np.number]).columns:
                    continue
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

        self.df = df
        return {
            "original_shape": self.original_shape,
            "new_shape": df.shape,
            "rows_removed": self.original_shape[0] - len(df),
            "applied_fixes": applied,
        }
