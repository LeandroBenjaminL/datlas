# Security Policy

## Supported Versions

Only the latest version receives security updates.

| Version | Supported          |
|---------|--------------------|
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, **do not open a public issue**.

Instead, report it privately via email to the repository owner.
You should expect an acknowledgment within 48 hours and a remediation plan within 7 days.

## Authentication & Authorization

Datlas usa **X-API-Key** para autenticar requests:

- Si `API_KEY` está vacío (default en desarrollo), los endpoints funcionan sin auth
- Si `API_KEY` tiene un valor, todos los endpoints (excepto `/` y `/health`) requieren:
  ```
  X-API-Key: <tu-api-key>
  ```
- El header se valida en `app/middleware/auth.py` (AuthMiddleware)
- Swagger UI muestra el security scheme automáticamente cuando API_KEY está configurada

## Rate Limiting

- Implementado con **SlowAPI**
- Configurable via `RATE_LIMIT` (default `100/minute` por IP)
- Se aplica a todos los endpoints de API

## File Upload Security

- **Tamaño máximo**: configurable via `MAX_UPLOAD_SIZE_MB` (default 50MB)
- Solo se aceptan archivos CSV
- El límite se aplica en los routers de upload y pipeline

## CORS

- Configurable via `CORS_ORIGINS` (default `*` en desarrollo)
- En producción, setear a los orígenes específicos del frontend
- Ejemplo: `https://leandrobenjaminl.github.io`

## Scope

Datlas processes user-uploaded datasets. Security applies to:

- **Backend API** (FastAPI, port 8000) — file upload, data processing
- **Frontend** (Astro, port 4321) — served via GitHub Pages in production
- **Database** (PostgreSQL 16, port 5432) — user data persistence
- **pgAdmin** (port 5050) — development only

## Token & Secret Security

- **Never commit secrets** to the repository. All secrets go in `.env` (gitignored).
- The `.env.example` file documents required variables without real values.
- Rotate database passwords and API keys regularly.
- In production, use AWS Secrets Manager or similar — never hardcode.

## Data Privacy

- Uploaded datasets are stored in `data/raw/` and `data/processed/` (gitignored).
- No user data is exposed in logs or error messages.
- No telemetry or analytics are sent to external services.
- In production (AWS), data should be encrypted at rest (S3 SSE) and in transit (TLS).

## CI/CD Security

- **Bandit SAST** runs on every PR (`.github/workflows/ci.yml`).
- Secrets are injected via GitHub Actions secrets, never hardcoded.
- Docker images are built from pinned base images (`python:3.12-slim`).
- Frontend deployment uses GitHub Pages with OIDC authentication.

## Dependencies

- Python dependencies in `backend/requirements.txt`
- Node dependencies in `frontend/package.json`
- Docker base images are pinned to specific versions
- Dependabot is configured for pip, npm, Docker, and GitHub Actions
- Run `pip-audit` or `safety check` before major upgrades
