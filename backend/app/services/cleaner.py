"""Data cleaning service — quality detection and automated fixes.

Provides the DataCleaner class that wraps a Pandas DataFrame and offers:
- Null detection with imputation strategies
- Outlier detection via the IQR method
- Duplicate row detection
- Type mismatch detection
- Configurable cleaning pipeline
"""

import pandas as pd
import numpy as np


class DataCleaner:
    """Analyze and clean tabular datasets using Pandas.

    Loads a CSV file into a DataFrame and provides methods to detect
    data quality issues and apply configurable fixes.

    Args:
        filepath: Path to the CSV file to load.

    Attributes:
        df: The loaded DataFrame (may be modified by clean()).
        original_shape: Tuple (rows, columns) before any cleaning.
        report: Dict with the latest analysis results.
    """

    def __init__(self, filepath: str):
        """Load the dataset and store its original shape."""
        self.df = pd.read_csv(filepath)
        self.original_shape = self.df.shape
        self.report = {}

    def detect_nulls(self) -> dict:
        """Detect columns with missing values.

        Returns a dict per column with null count, percentage, detected type,
        and a suggested imputation strategy.

        Returns:
            dict: Column name -> {null_count, null_percent, dtype, suggested_fix}.
        """
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
        """Recommend a null imputation strategy based on column dtype.

        Numeric columns建議用median (robusto a outliers),
        datetime y categóricas用mode (valor más frecuente).

        Args:
            col: Column name.

        Returns:
            str: Suggested fix description.
        """
        dtype = self.df[col].dtype
        if pd.api.types.is_numeric_dtype(dtype):
            return "fill with median"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "fill with mode (most frequent)"
        else:
            return "fill with mode (most frequent)"

    def detect_outliers(self) -> dict:
        """Detect outliers in numeric columns using the IQR method.

        Values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] are flagged as outliers.

        Returns:
            dict: Column name -> {outlier_count, outlier_percent, lower_bound, upper_bound}.
        """
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
        """Detect fully duplicate rows in the dataset.

        Counts total duplicate rows and identifies which columns
        contain duplicated values within those rows.

        Returns:
            dict: Total duplicate rows, percentage, and per-column duplicate counts.
        """
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
        """Detect column types and flag possible type mismatches.

        Checks if string columns could be parsed as datetime or numeric types.

        Returns:
            dict: Column name -> {detected_type, sample_values, possible_mismatch, suggested_type}.
        """
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
        """Check if a column's string values could be parsed as datetime or numeric.

        Samples the first 20 non-null values and attempts type coercion.
        Returns the suggested type if a mismatch is likely, None otherwise.

        Args:
            col: Column name.

        Returns:
            str or None: "datetime", "numeric", or None if no mismatch.
        """
        sample = self.df[col].dropna().astype(str).head(20)
        if sample.empty:
            return None
        try:
            pd.to_datetime(sample, format="mixed")
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
        """Run all detection methods and return a comprehensive quality report.

        Executes null, outlier, duplicate, and type detection in sequence.

        Returns:
            dict: Report with original shape and findings for each category.
        """
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
        """Apply cleaning fixes to a copy of the dataset.

        Supports three fix types:
        - fill_nulls: Dict of {col: strategy}, strategy is "median", "mean", or "mode"
        - remove_outliers: List of column names to filter IQR outliers from
        - remove_duplicates: Boolean, if True drops fully duplicate rows

        Operates on a copy of the original DataFrame. The cleaned version
        replaces self.df for further processing.

        Args:
            fixes: Optional config dict specifying which fixes to apply.

        Returns:
            dict: Summary of original shape, new shape, rows removed, and applied fixes.
        """
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
