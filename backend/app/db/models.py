"""
SQLAlchemy ORM models for Datlas.

Tables:
- Dataset: uploaded file metadata (no CSV content stored — ephemeral in production)
- AnalysisResult: clean/explore/pipeline analysis reports stored as JSONB
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Dataset(Base):
    """Metadata for an uploaded dataset.

    The raw CSV content is NOT persisted in the database — it lives on
    ephemeral disk in development and should be downloaded by the user.
    In production (Render), uploaded files are lost on each deploy.
    """

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    size_kb: Mapped[float] = mapped_column(nullable=False)
    rows: Mapped[int] = mapped_column(Integer, nullable=False)
    columns: Mapped[int] = mapped_column(Integer, nullable=False)
    col_names: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ──
    analyses: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="dataset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} filename='{self.filename}'>"


class AnalysisResult(Base):
    """Result of a clean, explore, or pipeline analysis run.

    Stores the full JSON report so users can revisit past analyses
    without re-running compute.
    """

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="clean | explore | pipeline")
    report: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Relationships ──
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="analyses")

    def __repr__(self) -> str:
        return f"<AnalysisResult id={self.id} type='{self.analysis_type}' dataset_id={self.dataset_id}>"
