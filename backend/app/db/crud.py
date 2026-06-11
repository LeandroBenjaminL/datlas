"""
CRUD operations for Dataset and AnalysisResult models.

Thin persistence layer — no business logic, just SQLAlchemy queries.
"""

from sqlalchemy.orm import Session

from app.db.models import AnalysisResult, Dataset

# ── Dataset ──────────────────────────────────────────────────


def create_dataset(
    db: Session,
    *,
    filename: str,
    original_filename: str,
    size_kb: float,
    rows: int,
    columns: int,
    col_names: list[str],
    content: bytes | None = None,
) -> Dataset:
    """Insert a new dataset metadata record with optional CSV content.

    If a dataset with the same filename already exists, it is replaced
    (upsert semantics — old record and its analyses are deleted via cascade).

    The content parameter stores the raw CSV bytes in a LargeBinary column
    so files survive across deploys on Render.
    """
    existing = db.query(Dataset).filter(Dataset.filename == filename).first()
    if existing:
        db.delete(existing)
        db.flush()

    dataset = Dataset(
        filename=filename,
        original_filename=original_filename,
        size_kb=size_kb,
        rows=rows,
        columns=columns,
        col_names=col_names,
        content=content,
        status="uploaded",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_by_filename(db: Session, filename: str) -> Dataset | None:
    """Look up a dataset by its stored filename."""
    return db.query(Dataset).filter(Dataset.filename == filename).first()


def get_dataset_by_id(db: Session, dataset_id: int) -> Dataset | None:
    """Look up a dataset by its primary key."""
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def list_datasets(db: Session) -> list[Dataset]:
    """Return all datasets ordered by creation time (newest first)."""
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


def update_dataset_status(db: Session, dataset_id: int, status: str) -> Dataset | None:
    """Update the status field of a dataset (e.g. 'uploaded' → 'cleaned')."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset:
        dataset.status = status
        db.commit()
        db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset_id: int) -> bool:
    """Delete a dataset and its cascade-linked analyses. Returns True if found."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    return False


# ── Analysis ────────────────────────────────────────────────


def save_analysis(
    db: Session,
    *,
    dataset_id: int,
    analysis_type: str,
    report: dict,
) -> AnalysisResult:
    """Persist an analysis report (clean, explore, or pipeline)."""
    result = AnalysisResult(
        dataset_id=dataset_id,
        analysis_type=analysis_type,
        report=report,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_analyses(db: Session, dataset_id: int) -> list[AnalysisResult]:
    """Return all analyses for a dataset, newest first."""
    return (
        db.query(AnalysisResult)
        .filter(AnalysisResult.dataset_id == dataset_id)
        .order_by(AnalysisResult.created_at.desc())
        .all()
    )


def get_latest_analysis(db: Session, dataset_id: int, analysis_type: str) -> AnalysisResult | None:
    """Return the most recent analysis of a given type for a dataset."""
    return (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.dataset_id == dataset_id,
            AnalysisResult.analysis_type == analysis_type,
        )
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
