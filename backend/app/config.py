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
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    API_KEY: str = ""  # Empty = no auth (dev mode). Set in production.

    # ── Security ──
    CORS_ORIGINS: str = "*"  # Comma-separated origins, "*" for dev
    RATE_LIMIT: str = "100/minute"  # Global rate limit
    MAX_UPLOAD_SIZE_MB: int = 100  # Max CSV upload size in megabytes

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS_ORIGINS into a list of allowed origins."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── PostgreSQL ──
    DATABASE_URL: str | None = None  # Render inyecta esto automáticamente
    POSTGRES_HOST: str = "localhost"  # "db" en docker-compose, host real en Render
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
        """Construye la URL de conexión a PostgreSQL.

        Prioridad:
        1. DATABASE_URL (Render la inyecta automáticamente)
        2. Construida desde POSTGRES_HOST + credenciales (docker-compose usa "db")
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        """URL para SQLAlchemy sincrónico (Alembic usa esta).

        Misma prioridad que database_url.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
