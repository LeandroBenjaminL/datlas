"""Pipeline service — automated upload → clean → explore in one shot."""

from pathlib import Path

import pandas as pd

from app.services.cleaner import DataCleaner
from app.services.explorer import DataExplorer


class PipelineService:
    """Orchestrate the full Datlas pipeline: auto-clean + explore.

    Takes a raw CSV path, runs data quality analysis, applies suggested
    fixes automatically, saves the cleaned version, and runs EDA on the result.
    """

    def __init__(self, raw_dir: str, processed_dir: str):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def run(self, filename: str, raw_bytes: bytes | None = None) -> dict:
        """Execute the full pipeline on a file.

        Args:
            filename: CSV filename (must end in .csv).
            raw_bytes: Optional file content for newly uploaded files.
                       If None, the file must already exist in raw_dir.

        Returns:
            dict: Combined pipeline report with upload_info, clean_report,
                  cleaning_result, and explore_report sections.
        """
        if raw_bytes is not None:
            filepath = self.raw_dir / filename
            filepath.write_bytes(raw_bytes)
        else:
            filepath = self.raw_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"{filename} not found in {self.raw_dir}")

        df_check = pd.read_csv(filepath)
        upload_info = {
            "filename": filename,
            "size_kb": round(filepath.stat().st_size / 1024, 2),
            "rows": len(df_check),
            "columns": len(df_check.columns),
        }

        cleaner = DataCleaner(str(filepath))
        clean_report = cleaner.analyze()

        auto_fixes = self._build_auto_fixes(clean_report)
        cleaning_result = cleaner.clean(auto_fixes)

        output_path = self.processed_dir / f"clean_{filename}"
        cleaner.df.to_csv(output_path, index=False)

        explorer = DataExplorer(str(output_path))
        explore_report = explorer.analyze()

        return {
            "upload_info": upload_info,
            "clean_report": clean_report,
            "cleaning_result": cleaning_result,
            "explore_report": explore_report,
        }

    def _build_auto_fixes(self, report: dict) -> dict:
        """Build a fixes dict from the analysis report — auto-apply everything.

        Uses the suggested strategy for each null column and flags all
        outlier columns and duplicates for removal.
        """
        fixes = {"fill_nulls": {}, "remove_outliers": [], "remove_duplicates": False}

        for col, info in report.get("nulls", {}).items():
            fix = info.get("suggested_fix", "fill with mode")
            if "median" in fix:
                fixes["fill_nulls"][col] = "median"
            elif "mean" in fix:
                fixes["fill_nulls"][col] = "mean"
            else:
                fixes["fill_nulls"][col] = "mode"

        for col in report.get("outliers", {}):
            fixes["remove_outliers"].append(col)

        dupes = report.get("duplicates", {})
        if dupes.get("total_duplicate_rows", 0) > 0:
            fixes["remove_duplicates"] = True

        return fixes
