# Datlas — Arquitectura

> **Identidad**: Datlas = Datos + Atlas. El titán que carga datasets, los limpia, los explora, y los entrega transformados.

---

## Decisiones de Arquitectura

Cada tecnología se eligió con un porqué. Si alguna vez alguien pregunta "¿por qué X y no Y?", este documento responde.

---

### 1. Lenguaje: Python 3.12

| Alternativas consideradas | Por qué NO | Por qué Python |
|---------------------------|------------|----------------|
| R | Excelente para estadística, pero ecosistema limitado para web/APIs | Tiene TODO el stack: análisis + API + deployment |
| Julia | Muy rápido, pero comunidad chica y pocas librerías web | Pandas es el estándar de la industria para manipulación de datos |
| Node.js | Bueno para APIs, pero análisis de datos es secundario | El ecosistema de data science es imbatible (Pandas, NumPy, Scikit-learn) |

**Decisión**: Python 3.12. Es la versión más reciente estable, ~15% más rápida que 3.10 en operaciones comunes.

---

### 2. Framework API: FastAPI

| Alternativas | Por qué NO |
|-------------|------------|
| Flask | Funciona, pero es manual para todo. Sin async nativo |
| Django REST | Muy pesado para esto. Viene con ORM, admin, auth — 80% no se usa |
| Litestar | Bueno pero menos adoptado. Comunidad 10x más chica |

**Por qué FastAPI**:
- Async nativo → maneja múltiples requests simultáneos sin bloquear
- Documentación Swagger automática → entrás a `/docs` y ves todos los endpoints
- Validación con Pydantic → los datos entrantes se validan solos
- Rendimiento comparable a Node.js/Go

---

### 3. Base de Datos: PostgreSQL 16

| Alternativas | Por qué NO |
|-------------|------------|
| MySQL/MariaDB | Menos features analíticas (sin window functions avanzadas, CTE recursivas limitadas) |
| SQLite | No escala, single-writer, sin concurrencia real |
| MongoDB | NoSQL no es ideal para datos tabulares analíticos |

**Por qué PostgreSQL**:
- El estándar de facto para análisis de datos
- Soporte nativo para JSON/JSONB (podés guardar datos semi-estructurados)
- Window functions, CTEs, agregaciones avanzadas
- pgAdmin incluido en Docker para desarrollo visual

---

### 4. ORM: SQLAlchemy 2.0 + Alembic

| Alternativas | Por qué NO |
|-------------|------------|
| SQLAlchemy 1.x | La 2.0 es muy superior: async, type hints nativos, mejor composición |
| Tortoise ORM | Bueno pero comunidad chica y menos adopción |
| Peewee | Simple pero limitado para consultas complejas |

**Por qué SQLAlchemy 2.0**:
- ORM más maduro de Python: 15+ años de evolución
- Async nativo con `AsyncSession` (compatible con FastAPI)
- `selectinload` para eager loading eficiente
- Alembic para migraciones: control de versiones del schema

---

### 5. Containerización: Docker

**Por qué Docker desde el día 0**:
- **Entorno idéntico en todas partes**: tu Windows, mi Linux, AWS, todo igual
- **Sin "en mi máquina funciona"**: el Dockerfile define exactamente qué versión de Python, qué dependencias
- **PostgreSQL sin instalación**: levanta con un comando, se destruye con otro

---

### 6. Frontend: Astro

| Alternativas | Por qué NO |
|-------------|------------|
| React/Next.js | Muy pesado para un portfolio de datos. 40KB+ de JS mínimo |
| Streamlit | Rápido para prototipos pero limitado en diseño y no es web real |
| SvelteKit | Buena opción, pero Astro es más liviano para contenido con islas interactivas |

**Por qué Astro**:
- 0KB de JavaScript por defecto — la página carga instantáneo
- Islas de interactividad: solo cargás JS donde realmente se necesita (upload, clean)
- Build a estáticos → deploy a GitHub Pages en 2 comandos

---

### 7. Autenticación: X-API-Key + SlowAPI

| Alternativas | Por qué NO |
|-------------|------------|
| JWT | Overkill para una API de datos. Requiere login, refresh tokens, gestión de sesiones |
| OAuth2 | Muy pesado para un proyecto individual |
| Basic Auth | Sin expiración ni rotación de credenciales |

**Por qué X-API-Key**:
- Simple: un header, un valor, listo
- Dev-friendly: vacío = sin auth en desarrollo
- Swagger lo soporta nativamente (security scheme)
- SlowAPI integrado: rate limiting en el mismo middleware

**Cómo funciona**:
- `API_KEY` en env vars. Si está vacío, los endpoints no piden auth
- Si tiene valor, AuthMiddleware valida `X-API-Key` en cada request
- SlowAPI limita requests por IP según `RATE_LIMIT`

---

### 8. Logging: structlog

| Alternativas | Por qué NO |
|-------------|------------|
| Logging estándar | No produce JSON, difícil de parsear en producción |
| Loguru | Bueno pero menos integrado con FastAPI |
| Sentry | Para errores, no para logging general |

**Por qué structlog**:
- Produce JSON estructurado → logea a Elastic/Kibana o CloudWatch fácilmente
- Request ID tracking: cada request tiene un ID único que cruza logs y responses
- Niveles configurables via `LOG_LEVEL`
- Middleware FastAPI dedicado

---

### 9. Storage: Abstracto (Local / S3)

**Por qué un ABC (Abstract Base Class)**:
- Desacopla los routers del sistema de archivos
- Misma API para LocalStorage y S3Storage
- Cambiar de local a S3 es cambiar una variable de entorno (`S3_BUCKET`)
- Fácil de testear con mocks

**Implementaciones**:
- `LocalStorage`: archivos en `data/raw/` y `data/processed/` (desarrollo)
- `S3Storage`: buckets S3 con credenciales AWS (producción)

---

### 10. CI/CD: GitHub Actions

4 jobs paralelos que deben pasar para mergear:

| Job | Herramienta | Qué verifica |
|-----|------------|--------------|
| review-budget | gh CLI | PR no excede 400 líneas (excepto con label) |
| security | Bandit | Vulnerabilidades de seguridad en código Python |
| lint-backend | Ruff | Estilo PEP 8 + formato consistente |
| test-backend | Pytest + pytest-cov | 141 tests, cobertura de código |
| frontend | Astro build | Build estático sin errores |

---

### 11. Cloud: Render + GitHub Pages (producción)

```
DESARROLLO LOCAL (Docker)              PRODUCCIÓN (Render + GitHub Pages)
docker compose up
├── datlas-api (FastAPI)    :8000      Render Web Service (Docker)
├── datlas-db (PostgreSQL)  :5432      Render PostgreSQL (gratis 90 días)
└── datlas-pgAdmin           :5050     —
                                        GitHub Pages → Frontend Astro
```

---

### 12. Flujo de Datos (completo)

```
                         ┌──────────────────────┐
                         │  USUARIO SUBE CSV     │
                         └──────┬───────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  AuthMiddleware        │  ← Valida X-API-Key (si configurada)
                    │  RateLimiter           │  ← SlowAPI por IP
                    │  RequestIDMiddleware   │  ← Asigna X-Request-ID
                    └───────────────────────┘
                                │
                                ▼
           ┌────────────────────────────────────┐
           │  POST /api/upload                   │
           │  → StorageBackend.save()            │  ← Local o S3 según S3_BUCKET
           │  → CRUD.create_dataset()            │  ← Persiste metadata en PostgreSQL
           │  → Devuelve metadata (filas, cols)  │
           └────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
           ┌────────────┐ ┌──────────┐ ┌──────────┐
           │clean       │ │explore   │ │ pipeline │
           │/analyze    │ │/analyze  │ │ /run     │
           │/apply      │ │          │ │          │
           └────────────┘ └──────────┘ └──────────┘
                    │           │           │
                    ▼           ▼           ▼
           ┌────────────────────────────────────┐
           │  CRUD.create_analysis()            │
           │  → Guarda reporte en PostgreSQL    │
           │  → JSONB con resultados completos  │
           └────────────────────────────────────┘
```

---

## Estructura del Proyecto

```
datlas/
│
├── docker-compose.yml           ← 3 servicios: API + DB + pgAdmin
├── .env.example                 ← Variables de entorno
├── render.yaml                  ← Deploy automático a Render
│
├── backend/                     ← FastAPI + Pandas
│   ├── Dockerfile               ← Python 3.12-slim
│   ├── requirements.txt         ← FastAPI, Pandas, SQLAlchemy
│   ├── alembic/                 ← Migraciones de base de datos
│   │   ├── versions/            ← Archivos de migración
│   │   ├── env.py               ← Configuración de Alembic
│   │   └── script.py.mako       ← Template para migraciones
│   └── app/
│       ├── __init__.py
│       ├── main.py              ← Entry point + middleware + health
│       ├── config.py            ← Settings desde .env (Pydantic)
│       ├── logging.py           ← structlog + RequestIDMiddleware
│       ├── schemas.py           ← Pydantic schemas de request/response
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── auth.py          ← AuthMiddleware (X-API-Key)
│       │   └── logging.py       ← RequestIDMiddleware
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── upload.py        ← POST /api/upload
│       │   ├── clean.py         ← POST /api/clean/analyze + /apply
│       │   ├── explore.py       ← POST /api/explore/analyze
│       │   ├── export.py        ← GET /api/datasets, /api/download
│       │   └── pipeline.py      ← POST /api/pipeline/upload + /run
│       ├── services/
│       │   ├── __init__.py
│       │   ├── cleaner.py       ← DataCleaner: nulos, outliers, dupes
│       │   ├── explorer.py      ← DataExplorer: profiling, stats, corr
│       │   ├── pipeline.py      ← PipelineService: orquestador
│       │   └── storage.py       ← StorageBackend (Local/S3 ABC)
│       └── db/
│           ├── __init__.py
│           ├── database.py      ← Engine, session factory, get_db
│           ├── models.py        ← Dataset + AnalysisResult ORM
│           └── crud.py          ← CRUD operations
│
├── frontend/                    ← Astro 5 (estático)
│   ├── astro.config.mjs         ← Config con base /datlas para GHPages
│   ├── package.json
│   └── src/
│       ├── layouts/
│       │   └── Layout.astro     ← Layout base con header/footer
│       └── pages/
│           ├── index.astro      ← Landing
│           ├── subir.astro      ← Upload con drag-and-drop
│           ├── limpiar.astro    ← Analyze + apply fixes desde la UI
│           ├── explorar.astro   ← Exploración de datos
│           └── pipeline.astro   ← Pipeline automático
│
├── data/
│   ├── raw/                     ← Datasets crudos (no tocar)
│   └── processed/               ← Datasets limpios (output)
│
└── docs/
    ├── arquitectura.md          ← Este archivo
    └── decisiones/
        └── identidad-visual.md  ← Paleta de colores y estilo
```

---

## Variables de Entorno

```env
# ── PostgreSQL ──
POSTGRES_USER=datlas
POSTGRES_PASSWORD=datlas_secreto_2026
POSTGRES_DB=datlas_db
POSTGRES_PORT=5432
# DATABASE_URL=              # Render la inyecta automáticamente

# ── pgAdmin ──
PGADMIN_EMAIL=admin@datlas.com
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050

# ── API ──
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
API_KEY=                     # Vacío = sin auth (dev). Setear en prod.
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR

# ── Security ──
CORS_ORIGINS=*               # Comma-separated, * para dev
RATE_LIMIT=100/minute        # Global rate limit
MAX_UPLOAD_SIZE_MB=50        # Tamaño máximo de archivo

# ── S3 Storage (opcional) ──
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_REGION=us-east-1
# S3_BUCKET=datlas-datasets  # Si está vacío, usa almacenamiento local
```

---

## Cómo Levantar

```bash
# Backend (API + DB + pgAdmin)
docker compose up --build

# Frontend (para desarrollo)
cd frontend && npm install && npm run dev
```

| Servicio | URL | Login |
|----------|-----|-------|
| API FastAPI | http://localhost:8000 | — |
| Swagger Docs | http://localhost:8000/docs | — |
| Frontend (dev) | http://localhost:4321/datlas | — |
| pgAdmin | http://localhost:5050 | admin@datlas.com / admin |
| PostgreSQL | localhost:5432 | datlas / datlas_secreto_2026 |

---

## Roadmap

1. ✅ Docker + PostgreSQL + FastAPI esqueleto
2. ✅ Frontend Astro
3. ✅ Perfil A — Limpieza (nulos, outliers, duplicados, tipos)
4. ✅ Perfil B — Exploración (distribuciones, correlaciones, estadísticas)
5. ✅ Perfil C — Pipeline completo + exportación
6. ✅ Deploy a Render + GitHub Pages
7. ✅ CI/CD con GitHub Actions (4 jobs)
8. ✅ PostgreSQL persistence (SQLAlchemy + Alembic)
9. ✅ Pydantic schemas para todos los endpoints
10. ✅ Auth & Security (X-API-Key, rate limiting, CORS, file size limits)
11. ✅ Structured logging (structlog, Request ID)
12. ✅ S3 Storage (Local/S3 abstracto)
13. ⬜ Property-based testing ampliado (Hypothesis)
14. ⬜ Frontend conectado a API deployada

---

## Principios de Diseño

- **Todo en Docker desde el día 0**: no se instala nada en la máquina host
- **Una decisión = una sección en este doc**: si cambiás algo, actualizás el porqué
- **Separación de concerns**: services/ tiene la lógica pura, routers/ tiene el transporte
- **Nunca decidir sin mostrar alternativas**: el alumno elige, el profe muestra opciones
- **Auth por diseño**: seguridad desde el primer request, configurable por env var
- **Storage abstracto**: cambiar de almacenamiento local a S3 es cambiar una variable de entorno
