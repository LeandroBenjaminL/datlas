"""Pydantic schemas for Datlas API request/response models.

Provides typed models for validation and auto-generated OpenAPI documentation.
"""

from pydantic import BaseModel, Field

# ── Upload ──────────────────────────────────────────────────


class UploadResponse(BaseModel):
    """Response after uploading a CSV file."""

    filename: str = Field(..., description="Original filename of the uploaded CSV")
    size_kb: float = Field(..., description="File size in kilobytes")
    rows: int = Field(..., description="Number of rows in the dataset")
    columns: int = Field(..., description="Number of columns in the dataset")
    col_names: list[str] = Field(..., description="Column names")
    status: str = Field(default="ok", description="Upload status")


# ── Clean ───────────────────────────────────────────────────


class CleanAnalyzeRequest(BaseModel):
    """Request to analyze a previously uploaded dataset."""

    filename: str = Field(..., description="Name of the uploaded CSV file")


class CleanApplyRequest(BaseModel):
    """Request to apply cleaning fixes to a dataset."""

    filename: str = Field(..., description="Name of the uploaded CSV file")
    fixes: dict = Field(
        default_factory=dict,
        description="Dict of fixes to apply, e.g. fill_nulls, remove_outliers, remove_duplicates",
    )


class CleanAnalyzeResponse(BaseModel):
    """Response with quality analysis results."""

    filename: str
    report: dict = Field(..., description="Analysis report with nulls, outliers, duplicates, types")
    message: str


class CleanApplyResponse(BaseModel):
    """Response after applying cleaning fixes."""

    filename: str
    analysis: dict = Field(..., description="Original analysis report")
    cleaning_result: dict = Field(..., description="Summary of applied fixes and shape changes")
    download_url: str = Field(..., description="Path to download the cleaned file")


# ── Explore ─────────────────────────────────────────────────


class ExploreAnalyzeRequest(BaseModel):
    """Request to run exploratory analysis on a dataset."""

    filename: str = Field(..., description="Name of the uploaded CSV file")


class ExploreAnalyzeResponse(BaseModel):
    """Response with full EDA report."""

    filename: str
    report: dict = Field(..., description="EDA report: profile, distributions, correlations, statistics")
    message: str


# ── Export ───────────────────────────────────────────────────


class DatasetInfo(BaseModel):
    """Metadata for a single dataset file."""

    filename: str
    size_kb: float


class DatasetsResponse(BaseModel):
    """List of all available datasets."""

    raw: list[DatasetInfo] = Field(default_factory=list)
    processed: list[DatasetInfo] = Field(default_factory=list)


# ── Pipeline ─────────────────────────────────────────────────


class PipelineRunRequest(BaseModel):
    """Request to run the pipeline on an already uploaded file."""

    filename: str = Field(..., description="Name of the uploaded CSV file")


class PipelineResponse(BaseModel):
    """Response from the pipeline (upload → clean → explore)."""

    upload_info: dict = Field(..., description="Upload metadata: filename, size_kb, rows, columns")
    clean_report: dict = Field(..., description="Quality analysis: nulls, outliers, duplicates, types")
    cleaning_result: dict = Field(..., description="Summary of applied fixes")
    explore_report: dict = Field(..., description="EDA report: profile, distributions, correlations")


# ── Error ────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error description")
