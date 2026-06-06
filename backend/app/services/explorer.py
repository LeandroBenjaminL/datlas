"""Data exploration service — profiling, distributions, correlations, statistics."""

import numpy as np
import pandas as pd


class DataExplorer:
    """Explore and profile tabular datasets.

    Loads a CSV and provides methods for comprehensive exploratory data analysis:
    profiling, distributions, correlations, and descriptive statistics.

    Args:
        filepath: Path to the CSV file to load.

    Attributes:
        df: The loaded DataFrame.
        shape: Original (rows, columns) tuple.
    """

    def __init__(self, filepath: str):
        self.df = pd.read_csv(filepath)
        self.shape = self.df.shape

    def profile(self) -> dict:
        """Full dataset profile: shape, types, nulls, uniques, descriptive stats.

        For numeric columns includes mean, std, min, quartiles, max.
        For categorical/text columns includes mode and frequency.

        Returns:
            dict: Shape info and per-column profile data.
        """
        cols = {}
        for col in self.df.columns:
            dtype = self.df[col].dtype
            is_num = pd.api.types.is_numeric_dtype(dtype)
            info = {
                "type": str(dtype),
                "nulls": int(self.df[col].isnull().sum()),
                "null_pct": round(float(self.df[col].isnull().mean() * 100), 2),
                "unique": int(self.df[col].nunique()),
            }
            if is_num:
                d = self.df[col].describe()
                info.update(
                    {
                        "mean": round(float(d.get("mean", 0)), 2),
                        "std": round(float(d.get("std", 0)), 2),
                        "min": round(float(d.get("min", 0)), 2),
                        "q25": round(float(d.get("25%", 0)), 2),
                        "median": round(float(d.get("50%", 0)), 2),
                        "q75": round(float(d.get("75%", 0)), 2),
                        "max": round(float(d.get("max", 0)), 2),
                    }
                )
            else:
                top_series = self.df[col].dropna()
                if not top_series.empty:
                    counts = top_series.value_counts()
                    info["top"] = str(counts.index[0])
                    info["freq"] = int(counts.iloc[0])
                else:
                    info["top"] = None
                    info["freq"] = 0
            cols[col] = info

        return {"shape": {"rows": self.shape[0], "columns": self.shape[1]}, "columns": cols}

    def distributions(self, bins: int = 20) -> dict:
        """Histogram data for every numeric column.

        Args:
            bins: Number of histogram bins (default 20).

        Returns:
            dict: Column name -> {counts: [...], edges: [...]}.
        """
        numeric = self.df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric:
            data = self.df[col].dropna()
            if len(data) < 2:
                continue
            counts, edges = np.histogram(data, bins=bins)
            result[col] = {
                "counts": [int(c) for c in counts],
                "edges": [round(float(e), 3) for e in edges],
            }
        return result

    def correlations(self) -> dict:
        """Pearson correlation matrix and strongest correlated column pairs.

        Returns:
            dict: Matrix (nested dict) and sorted pairs list.
        """
        numeric = self.df.select_dtypes(include=[np.number]).dropna()
        if numeric.shape[1] < 2:
            return {"matrix": {}, "pairs": []}

        corr = numeric.corr(method="pearson")
        matrix = {}
        for col in corr.columns:
            matrix[col] = {c: round(float(corr.loc[c, col]), 3) for c in corr.columns}

        pairs = []
        cols = list(corr.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                pairs.append(
                    {
                        "x": cols[i],
                        "y": cols[j],
                        "correlation": round(float(corr.iloc[i, j]), 3),
                    }
                )
        pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)

        return {"matrix": matrix, "pairs": pairs}

    def statistics(self) -> dict:
        """Descriptive statistics: skewness and kurtosis for numeric columns.

        Returns:
            dict: Column name -> {skewness, kurtosis}.
        """
        numeric = self.df.select_dtypes(include=[np.number]).columns
        result = {}
        for col in numeric:
            data = self.df[col].dropna()
            if len(data) < 3:
                continue
            result[col] = {
                "skewness": round(float(data.skew()), 3),
                "kurtosis": round(float(data.kurt()), 3),
            }
        return result

    def preview(self, n: int = 5) -> list:
        """First rows of the dataset as a list of dicts.

        Args:
            n: Number of rows to return (default 5).

        Returns:
            list: Each row as a dict with column -> value.
        """
        return self.df.head(n).fillna("").to_dict(orient="records")

    def categorical_breakdown(self, top: int = 5) -> dict:
        """Top values for each categorical/text column.

        Args:
            top: Number of top values per column.

        Returns:
            dict: Column name -> [{value, count, pct}, ...].
        """
        result = {}
        for col in self.df.columns:
            dtype = self.df[col].dtype
            if pd.api.types.is_numeric_dtype(dtype):
                continue
            counts = self.df[col].value_counts()
            total = counts.sum()
            result[col] = [
                {"value": str(k), "count": int(v), "pct": round(float(v / total * 100), 1)}
                for k, v in counts.head(top).items()
            ]
        return result

    def null_summary(self) -> dict:
        """Summary of missing values across the dataset.

        Returns:
            dict: Total nulls, overall pct, and per-column breakdown.
        """
        total_cells = self.shape[0] * self.shape[1]
        total_nulls = int(self.df.isnull().sum().sum())
        columns = {}
        for col in self.df.columns:
            n = int(self.df[col].isnull().sum())
            if n > 0:
                pct = round(n / self.shape[0] * 100, 1) if self.shape[0] > 0 else 0.0
                columns[col] = {"count": n, "pct": pct}
        overall_pct = round(total_nulls / total_cells * 100, 2) if total_cells > 0 else 0.0
        return {
            "total_nulls": total_nulls,
            "overall_pct": overall_pct,
            "columns": columns,
        }

    def analyze(self) -> dict:
        """Run all exploration methods and return a comprehensive EDA report.

        Returns:
            dict: Report with profile, distributions, correlations, statistics, preview, and more.
        """
        return {
            "profile": self.profile(),
            "distributions": self.distributions(),
            "correlations": self.correlations(),
            "statistics": self.statistics(),
            "preview": self.preview(),
            "categorical_breakdown": self.categorical_breakdown(),
            "null_summary": self.null_summary(),
        }
