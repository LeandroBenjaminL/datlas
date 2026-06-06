"""
Datlas Configuration.

Lee variables de entorno usando Pydantic Settings.
Prioridad: .env > environment variables > defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Todas las configuraciones de Datlas."""

    # ── API ──
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # ── PostgreSQL ──
    POSTGRES_USER: str = "datlas"
    POSTGRES_PASSWORD: str = "datlas_secreto_2026"
    POSTGRES_DB: str = "datlas_db"
    POSTGRES_PORT: int = 5432

    # ── AWS (futuro) ──
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str | None = None

    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a PostgreSQL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def database_url_sync(self) -> str:
        """URL para SQLAlchemy sincrónico (Alembic usa esta)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@localhost:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
