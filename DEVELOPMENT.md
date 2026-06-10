# Development

## Comandos frecuentes

```bash
docker compose up --build          # Levantar API + DB + pgAdmin
docker compose logs api -f         # Ver logs de la API
docker compose down                # Parar todo
```

```bash
cd frontend
npm run dev                        # Servidor de desarrollo Astro → :4321
npm run build                      # Build estático para GitHub Pages
```

## Testing

```bash
cd backend

# Todas las pruebas (141 tests)
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ -v --cov=app/ --cov-report=term-missing

# Por archivo
python -m pytest tests/test_security.py -v
python -m pytest tests/test_logging.py -v
python -m pytest tests/test_storage.py -v

# Ruff lint + format
python -m ruff check app/ tests/
python -m ruff format --check app/ tests/
```

## Variables de Entorno

```bash
cp .env.example .env
```

Variables clave para desarrollo:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_KEY` | `""` (vacío) | Sin auth en dev |
| `RATE_LIMIT` | `100/minute` | Rate limiting |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `S3_BUCKET` | `""` | Vacío = storage local |

## API Debug

```bash
# Health check
curl http://localhost:8000/

# Health check detallado
curl http://localhost:8000/health

# Swagger UI
# http://localhost:8000/docs

# Subir archivo
curl -X POST http://localhost:8000/api/upload -F "file=@data/raw/test.csv"
```

## Estructura

```
backend/
├── alembic/              ← Migraciones DB
└── app/
    ├── main.py           ← Entry point + middleware
    ├── config.py         ← Settings
    ├── logging.py        ← structlog config
    ├── schemas.py        ← Pydantic schemas
    ├── middleware/
    │   ├── auth.py       ← AuthMiddleware
    │   └── logging.py    ← RequestIDMiddleware
    ├── routers/          ← Endpoints REST
    ├── services/         ← Lógica de negocio
    └── db/               ← SQLAlchemy models + CRUD
```

## Documentación

| Archivo | Propósito |
|---------|-----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitectura y decisiones técnicas |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |
| [docs/decisiones/](docs/decisiones/) | Decisiones de diseño |
