# Datlas — Architecture

> Datlas = Datos + Atlas. Cargá datasets, limpialos, exploralos y transformalos.

## Stack

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| API | Python 3.12 + FastAPI | Endpoints REST + Swagger automático |
| Datos | Pandas 2.2 | Manipulación y limpieza de datasets |
| Base de datos | PostgreSQL 16 | Almacenamiento analítico |
| Frontend | Astro 5 | UI estática con islas interactivas |
| Contenedores | Docker | Entorno reproducible |
| Auth | SlowAPI + X-API-Key | Rate limiting + autenticación |
| Logging | structlog | JSON estructurado con Request ID |
| Storage | S3 / Local | StorageBackend abstracto |
| ORM | SQLAlchemy 2.0 + Alembic | Persistencia + migraciones |

## Capas de la aplicación

```
Request → AuthMiddleware → RateLimiter → Router → Service → DB/S3
            ↓
      RequestIDMiddleware (logging)
```

### Middleware (en orden)
1. **RequestIDMiddleware** — Asigna X-Request-ID a cada request
2. **AuthMiddleware** — Valida X-API-Key (si está configurada)
3. **SlowAPI** — Rate limiting por IP

### Storage
- `StorageBackend` (ABC) con dos implementaciones:
  - `LocalStorage` — archivos en disco (dev)
  - `S3Storage` — buckets S3 (producción)
- Selección automática: si `S3_BUCKET` está configurado, usa S3

## Endpoints

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/` | No | Health check |
| GET | `/health` | No | Health check + PostgreSQL |
| POST | `/api/upload` | Sí* | Subir archivo CSV |
| POST | `/api/clean/analyze` | Sí* | Analizar calidad de datos |
| POST | `/api/clean/apply` | Sí* | Aplicar limpieza |
| POST | `/api/explore/analyze` | Sí* | Perfil exploratorio |
| GET | `/api/datasets` | Sí* | Listar datasets |
| GET | `/api/datasets/{id}/analyses` | Sí* | Análisis de dataset |
| POST | `/api/pipeline/upload` | Sí* | Subir para pipeline |
| POST | `/api/pipeline/run` | Sí* | Ejecutar pipeline |
| GET | `/api/download/{filename}` | Sí* | Descargar archivo |

_\* Auth requerida solo si `API_KEY` está configurada._

## Flujo de datos

```
POST /api/upload → StorageBackend → DB (metadata) → POST /api/clean/analyze → reporte
                                            ↓
                                  POST /api/clean/apply  → StorageBackend
                                            ↓
                                  POST /api/explore/analyze → perfil
                                            ↓
                                  POST /api/pipeline/run → todo en uno
```

## Variables de Entorno clave

| Variable | Default | Uso |
|----------|---------|-----|
| `API_KEY` | `""` | Autenticación API |
| `RATE_LIMIT` | `100/minute` | Rate limiting |
| `MAX_UPLOAD_SIZE_MB` | `50` | Tamaño máximo de subida |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `S3_BUCKET` | `""` | Bucket S3 (vacío = local) |

## Principios

- **Todo en Docker**: no se instala nada en la máquina host
- **Separación de concerns**: services/ = lógica pura, routers/ = transporte
- **Datos inmutables**: nunca se modifica el dataset original
- **Decisiones documentadas**: cada tecnología tiene su porqué
- **Auth por diseño**: seguridad desde el primer request
- **Storage abstracto**: cambiar de local a S3 es cambiar una env var

Ver [docs/arquitectura.md](docs/arquitectura.md) para el detalle completo de decisiones técnicas.
