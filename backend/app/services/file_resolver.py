"""File resolver — tiered storage (local disk + PostgreSQL).

Centraliza la definición de DATA_RAW / DATA_PROCESSED y provee helpers
para que los routers puedan leer y escribir archivos sin preocuparse
por si están en disco local o en la base de datos.

Estrategia de resolución (tiered storage):
  1. Buscar en disco local primero (rápido, sin red).
  2. Si no está en local, restaurar desde PostgreSQL (BYTEA) a disco local.
  3. Si no está en ningún lado, lanzar FileNotFoundError.

Al escribir:
  1. Guardar en disco local siempre.
  2. El contenido se persiste en PostgreSQL vía create_dataset() desde el router.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# ── Rutas base ──────────────────────────────────────────────
# Intentamos /app/data (Docker) primero, sino data/ (local dev).
try:
    BASE_DIR = Path("/app/data")
    BASE_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    BASE_DIR = Path("data")
    BASE_DIR.mkdir(parents=True, exist_ok=True)

DATA_RAW = BASE_DIR / "raw"
DATA_PROCESSED = BASE_DIR / "processed"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


def store_file(filename: str, content: bytes, folder: str = "raw") -> Path:
    """Guardar archivo en disco local.

    La persistencia en PostgreSQL se maneja aparte (create_dataset en el router).

    Args:
        filename: Nombre del archivo.
        content: Contenido en bytes.
        folder: Subdirectorio ('raw' o 'processed').

    Returns:
        Path local del archivo guardado.
    """
    base = _base_dir(folder)
    local_path = base / filename
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)
    return local_path


def ensure_file_local(
    filename: str,
    folder: str = "raw",
    db: "Session | None" = None,
) -> Path:
    """Asegurar que un archivo esté disponible en disco local.

    Si ya está en local, devuelve el path directamente.
    Si no está en local pero existe en PostgreSQL (content BYTEA),
    lo restaura desde la DB a disco local.
    Si no está en ningún lado, lanza FileNotFoundError.

    Args:
        filename: Nombre del archivo.
        folder: Subdirectorio ('raw' o 'processed').
        db: Sesión de SQLAlchemy opcional para restaurar desde PostgreSQL.

    Returns:
        Path absoluto al archivo local.

    Raises:
        FileNotFoundError: Si el archivo no existe ni en local ni en DB.
    """
    base = _base_dir(folder)
    local_path = base / filename

    if local_path.exists():
        return local_path

    # No está en local → intentar restaurar desde PostgreSQL
    if db is not None:
        from app.db.crud import get_dataset_by_filename

        dataset = get_dataset_by_filename(db, filename)
        if dataset is not None and dataset.content is not None:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(dataset.content)
            return local_path

    raise FileNotFoundError(
        f"File {filename} not found. Upload it first via POST /api/upload",
    )


def _base_dir(folder: str) -> Path:
    """Resolver el directorio base según el folder."""
    return DATA_PROCESSED if folder == "processed" else DATA_RAW
