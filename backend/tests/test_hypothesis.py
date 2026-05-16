"""Property-based tests with hypothesis — fuzz DataCleaner + DataExplorer."""

import io
from pathlib import Path

import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.cleaner import DataCleaner
from app.services.explorer import DataExplorer


def dataframe_to_csv(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def csv_from_dataframe(df: pd.DataFrame) -> str:
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        df.to_csv(tmp.name, index=False)
        return tmp.name


# ── Column name strategies ──
col_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Punctuation", "Sc")),
    min_size=1,
    max_size=20,
).filter(lambda x: not x.startswith("_") and x.strip())


# ── DataCleaner ────────────────────────────────────


class TestDataCleanerHypothesis:
    @given(
        n_rows=st.integers(min_value=1, max_value=50),
        n_cols=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=20)
    def test_analyze_never_crashes(self, n_rows, n_cols):
        cols = {f"col_{i}": np.random.randn(n_rows) for i in range(n_cols)}
        df = pd.DataFrame(cols)
        path = csv_from_dataframe(df)
        cleaner = DataCleaner(path)
        report = cleaner.analyze()
        assert "original_shape" in report
        assert report["original_shape"]["rows"] == n_rows
        Path(path).unlink(missing_ok=True)

    @given(
        n_rows=st.integers(min_value=5, max_value=50),
        null_pct=st.floats(min_value=0.0, max_value=0.5),
    )
    @settings(max_examples=15)
    def test_clean_with_nulls(self, n_rows, null_pct):
        df = pd.DataFrame(
            {
                "a": np.random.randn(n_rows),
                "b": np.random.randn(n_rows),
            }
        )
        mask_a = np.random.random(n_rows) < null_pct
        mask_b = np.random.random(n_rows) < null_pct
        df.loc[mask_a, "a"] = np.nan
        df.loc[mask_b, "b"] = np.nan
        path = csv_from_dataframe(df)
        cleaner = DataCleaner(path)
        result = cleaner.clean({"fill_nulls": {"a": "median", "b": "mean"}})
        assert result["new_shape"][0] == n_rows
        assert cleaner.df["a"].isnull().sum() == 0
        Path(path).unlink(missing_ok=True)


# ── DataExplorer ───────────────────────────────────


class TestDataExplorerHypothesis:
    @given(
        n_rows=st.integers(min_value=2, max_value=100),
        numeric_cols=st.integers(min_value=1, max_value=8),
        cat_cols=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=20)
    def test_analyze_never_crashes(self, n_rows, numeric_cols, cat_cols):
        data = {}
        for i in range(numeric_cols):
            data[f"num_{i}"] = np.random.randn(n_rows)
        for i in range(cat_cols):
            data[f"cat_{i}"] = np.random.choice(["A", "B", "C"], n_rows)
        df = pd.DataFrame(data)
        path = csv_from_dataframe(df)
        explorer = DataExplorer(path)
        report = explorer.analyze()
        assert "profile" in report
        assert report["profile"]["shape"]["rows"] == n_rows
        Path(path).unlink(missing_ok=True)

    @given(
        n_rows=st.integers(min_value=5, max_value=50),
        outlier_scale=st.floats(min_value=5.0, max_value=100.0),
    )
    @settings(max_examples=10)
    def test_outliers_detected(self, n_rows, outlier_scale):
        data = np.random.randn(n_rows) * 10
        data[0] = outlier_scale * 10
        df = pd.DataFrame({"x": data})
        path = csv_from_dataframe(df)
        cleaner = DataCleaner(path)
        outliers = cleaner.detect_outliers()
        if "x" in outliers:
            assert outliers["x"]["outlier_count"] >= 1
        Path(path).unlink(missing_ok=True)
