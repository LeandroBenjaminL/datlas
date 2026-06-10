# Contributing

## Entorno de desarrollo

1. Clonar el repo
2. `cp .env.example .env`
3. `docker compose up --build` (levanta API + PostgreSQL + pgAdmin)
4. `cd frontend && npm install` (para el frontend)

## Convenciones

- **Python**: PEP 8. Los docstrings siguen formato Google-style.
- **Commits**: Conventional Commits en inglés (`feat:`, `fix:`, `docs:`, `chore:`).
- **Branching**: `main` es siempre deployable. Todo cambio va por branch → PR → CI → merge.

## API

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/` | No | Health check |
| GET | `/health` | No | Health check + PostgreSQL |
| POST | `/api/upload` | Sí* | Subir CSV |
| POST | `/api/clean/analyze` | Sí* | Analizar calidad de datos |
| POST | `/api/clean/apply` | Sí* | Aplicar correcciones |
| POST | `/api/explore/analyze` | Sí* | Perfil exploratorio |
| GET | `/api/datasets` | Sí* | Listar datasets |
| POST | `/api/pipeline/upload` | Sí* | Subir para pipeline |
| POST | `/api/pipeline/run` | Sí* | Ejecutar pipeline |
| GET | `/api/download/{filename}` | Sí* | Descargar |

_\* Auth requerida solo si `API_KEY` está configurada._

## CI/CD

4 jobs en GitHub Actions:

| Job | Tool | Descripción |
|-----|------|-------------|
| `review-budget` | — | Verifica que el PR no exceda 400 líneas |
| `security` | Bandit | Análisis estático de seguridad |
| `lint-backend` | Ruff | Lint + formateo de código Python |
| `test-backend` | Pytest | 141 tests con cobertura |
| `frontend` | Astro | Build del frontend |

Para PRs grandes (>400 líneas), agregar label `override-review-budget`.

## Reportar bugs

Abrir issue en GitHub con:
- Descripción del problema
- Dataset de ejemplo (si aplica)
- Payload de request usado
