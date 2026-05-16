from pathlib import Path
import pytest

from app.services.pipeline import PipelineService


@pytest.fixture
def pipeline(tmp_path) -> PipelineService:
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir()
    processed.mkdir()
    return PipelineService(str(raw), str(processed))


@pytest.fixture
def pipeline_with_csv(pipeline, test_csv) -> PipelineService:
    import shutil
    raw = Path(pipeline.raw_dir)
    shutil.copy2(str(test_csv), str(raw / "test.csv"))
    return pipeline


class TestPipelineService:
    def test_run_with_bytes(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        assert "upload_info" in result
        assert "clean_report" in result
        assert "cleaning_result" in result
        assert "explore_report" in result

    def test_upload_info(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        ui = result["upload_info"]
        assert ui["filename"] == "test.csv"
        assert ui["rows"] == 10
        assert ui["columns"] == 6

    def test_cleaning_result(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        cr = result["cleaning_result"]
        assert "original_shape" in cr
        assert "new_shape" in cr
        assert "applied_fixes" in cr

    def test_explore_report(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        er = result["explore_report"]
        assert "profile" in er
        assert "distributions" in er
        assert "correlations" in er

    def test_saves_cleaned_file(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        pipeline.run("test.csv", raw_bytes=raw_bytes)
        cleaned = Path(pipeline.processed_dir) / "clean_test.csv"
        assert cleaned.exists()

    def test_run_existing_file(self, pipeline_with_csv):
        result = pipeline_with_csv.run("test.csv")
        assert result["upload_info"]["filename"] == "test.csv"
        assert "cleaning_result" in result

    def test_auto_fixes(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        cr = result["cleaning_result"]
        assert len(cr["applied_fixes"]) > 0
