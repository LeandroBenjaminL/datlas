"""Tests for Pydantic API schemas.

Validates request/response models with valid and invalid inputs.
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    CleanAnalyzeRequest,
    CleanAnalyzeResponse,
    CleanApplyRequest,
    CleanApplyResponse,
    DatasetInfo,
    DatasetsResponse,
    ExploreAnalyzeRequest,
    ExploreAnalyzeResponse,
    PipelineResponse,
    PipelineRunRequest,
    UploadResponse,
)


class TestUploadResponse:
    def test_valid_response(self):
        resp = UploadResponse(
            filename="datos.csv",
            size_kb=12.5,
            rows=100,
            columns=5,
            col_names=["a", "b", "c", "d", "e"],
        )
        assert resp.filename == "datos.csv"
        assert resp.size_kb == 12.5
        assert resp.rows == 100
        assert resp.columns == 5
        assert resp.status == "ok"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            UploadResponse()


class TestCleanAnalyzeRequest:
    def test_valid(self):
        req = CleanAnalyzeRequest(filename="data.csv")
        assert req.filename == "data.csv"

    def test_missing_filename(self):
        with pytest.raises(ValidationError):
            CleanAnalyzeRequest()


class TestCleanApplyRequest:
    def test_valid_with_fixes(self):
        req = CleanApplyRequest(
            filename="data.csv",
            fixes={"fill_nulls": {"edad": "median"}},
        )
        assert req.fixes == {"fill_nulls": {"edad": "median"}}

    def test_default_empty_fixes(self):
        req = CleanApplyRequest(filename="data.csv")
        assert req.fixes == {}


class TestCleanAnalyzeResponse:
    def test_valid(self):
        resp = CleanAnalyzeResponse(
            filename="data.csv",
            report={"nulls": {}, "outliers": {}, "duplicates": {}, "types": {}},
            message="ok",
        )
        assert resp.report == {"nulls": {}, "outliers": {}, "duplicates": {}, "types": {}}

    def test_missing_report(self):
        with pytest.raises(ValidationError):
            CleanAnalyzeResponse(filename="x", message="ok")


class TestCleanApplyResponse:
    def test_valid(self):
        resp = CleanApplyResponse(
            filename="data.csv",
            analysis={"original_shape": (10, 5)},
            cleaning_result={"applied_fixes": []},
            download_url="/api/download/clean_data.csv",
        )
        assert resp.download_url == "/api/download/clean_data.csv"


class TestExploreAnalyzeRequest:
    def test_missing_filename_raises(self):
        with pytest.raises(ValidationError):
            ExploreAnalyzeRequest()


class TestExploreAnalyzeResponse:
    def test_valid(self):
        resp = ExploreAnalyzeResponse(
            filename="data.csv",
            report={},
            message="done",
        )
        assert resp.message == "done"


class TestDatasetInfo:
    def test_valid(self):
        info = DatasetInfo(filename="test.csv", size_kb=1.5)
        assert info.filename == "test.csv"
        assert info.size_kb == 1.5

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            DatasetInfo(filename=123, size_kb="abc")


class TestDatasetsResponse:
    def test_empty(self):
        resp = DatasetsResponse()
        assert resp.raw == []
        assert resp.processed == []

    def test_with_files(self):
        resp = DatasetsResponse(
            raw=[DatasetInfo(filename="a.csv", size_kb=1.0)],
            processed=[DatasetInfo(filename="clean_a.csv", size_kb=0.8)],
        )
        assert len(resp.raw) == 1
        assert len(resp.processed) == 1


class TestPipelineRunRequest:
    def test_valid(self):
        req = PipelineRunRequest(filename="data.csv")
        assert req.filename == "data.csv"

    def test_missing_filename(self):
        with pytest.raises(ValidationError):
            PipelineRunRequest()


class TestPipelineResponse:
    def test_valid(self):
        resp = PipelineResponse(
            upload_info={"filename": "t.csv", "size_kb": 1.0, "rows": 10, "columns": 3},
            clean_report={},
            cleaning_result={},
            explore_report={},
        )
        assert resp.upload_info["rows"] == 10
