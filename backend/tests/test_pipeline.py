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
        # Verificar valores concretos: el pipeline aplica fixes automáticos
        assert cr["original_shape"] == (10, 6)
        assert cr["new_shape"][0] <= 10  # puede reducir filas por outliers
        assert cr["new_shape"][1] == 6
        assert len(cr["applied_fixes"]) >= 1
        # Al menos debería rellenar nulos de edad y salario
        fixes_text = " ".join(cr["applied_fixes"])
        assert "edad" in fixes_text or "salario" in fixes_text

    def test_explore_report(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        er = result["explore_report"]
        assert "profile" in er
        assert "distributions" in er
        assert "correlations" in er
        # Verificar que el profile tiene los datos del CSV limpio
        assert er["profile"]["shape"]["rows"] <= 10
        assert er["profile"]["shape"]["columns"] == 6
        # El CSV limpio no debería tener nulos
        assert "null_summary" in er
        assert er["null_summary"]["total_nulls"] == 0

    def test_saves_cleaned_file(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        pipeline.run("test.csv", raw_bytes=raw_bytes)
        cleaned = Path(pipeline.processed_dir) / "clean_test.csv"
        assert cleaned.exists()
        # Verificar contenido: debe ser un CSV válido con datos
        import pandas as pd

        df = pd.read_csv(cleaned)
        assert len(df) > 0
        assert len(df.columns) == 6
        # Debe tener cero nulos (el pipeline los rellenó)
        assert df.isnull().sum().sum() == 0

    def test_run_existing_file(self, pipeline_with_csv):
        result = pipeline_with_csv.run("test.csv")
        assert result["upload_info"]["filename"] == "test.csv"
        assert "cleaning_result" in result

    def test_auto_fixes(self, pipeline, test_csv):
        raw_bytes = test_csv.read_bytes()
        result = pipeline.run("test.csv", raw_bytes=raw_bytes)
        cr = result["cleaning_result"]
        assert len(cr["applied_fixes"]) > 0
        # Verificar fixes específicos que deberían aplicarse
        fixes = cr["applied_fixes"]
        has_null_fix = any("filled nulls" in f for f in fixes)
        assert has_null_fix, f"Expected null-fill fix, got: {fixes}"


class TestPipelineServiceErrors:
    """Tests de error para PipelineService — proteger contra regresiones."""

    def test_run_nonexistent_file(self, pipeline):
        """Archivo que no existe sin raw_bytes — debe lanzar FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="noexiste.csv"):
            pipeline.run("noexiste.csv")

    def test_run_empty_csv(self, pipeline):
        """Pipeline con CSV vacío (solo header) no debería crashear."""
        empty_bytes = b"nombre,edad,ciudad\n"
        result = pipeline.run("empty.csv", raw_bytes=empty_bytes)
        assert result["upload_info"]["rows"] == 0
        assert result["upload_info"]["columns"] == 3
        assert result["cleaning_result"]["new_shape"] == (0, 3)
