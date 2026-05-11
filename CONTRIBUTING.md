# Contributing

## Entorno de desarrollo

1. Clonar el repo
2. `cp .env.example .env`
3. `docker compose up --build` (levanta API + PostgreSQL + pgAdmin)
4. `cd frontend && npm install` (para el frontend)

## Convenciones

- **Python**: PEP 8. Los docstrings siguen formato Google-style.
- **Commits**: Conventional Commits en inglés (`feat:`, `fix:`, `docs:`, `chore:`).
- **Branching**: directo a `main` para cambios chicos, branch + PR solo para features grandes.

## API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/upload` | POST | Subir CSV |
| `/api/clean/analyze` | POST | Analizar calidad de datos |
| `/api/clean/apply` | POST | Aplicar correcciones |

## Reportar bugs

Abrir issue en GitHub con:
- Descripción del problema
- Dataset de ejemplo (si aplica)
- Payload de request usado
