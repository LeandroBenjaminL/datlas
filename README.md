# ⚡ Datlas

> Cargá un dataset, limpiá los datos, explorá patrones y exportá resultados. Todo en un solo lugar. Sin instalar nada.

Datlas es una **arquitectura profesional** para limpieza y análisis de datos. Subís un CSV, Datlas detecta problemas (nulos, outliers, duplicados), te muestra un reporte, y aplica las correcciones que elegís. Todo via API REST, con frontend en Astro y PostgreSQL para persistencia.

---

## Stack

| Tecnología | Versión | Por qué |
|------------|---------|---------|
| **Python** | 3.12 | ~15% más rápido que 3.10, ecosistema de datos imbatible |
| **FastAPI** | 0.115+ | Async nativo, Swagger automático, validación con Pydantic |
| **Pandas** | 2.2+ | El estándar de la industria para manipulación de datos |
| **PostgreSQL** | 16 | Window functions, JSONB, CTEs — ideal para datos analíticos |
| **Docker** | latest | Mismo entorno en dev y prod. "En mi máquina funciona" no existe |
| **Astro** | 6 | 0KB JS por defecto, islas de interactividad, build estático |
| **pgAdmin** | latest | Interfaz visual para explorar la DB sin tocar terminal |
| **Auth** | SlowAPI + X-API-Key | Rate limiting configurables y autenticación por API Key |
| **Logging** | structlog | JSON estructurado con Request ID para tracing distribuido |
| **Storage** | S3 / Local | StorageBackend abstracto, transparente para los routers |
| **SQLAlchemy** | 2.0+ | ORM con Alembic para migraciones de base de datos |
| **Verity Engine** | — | Editor visual de circuitos lógicos adaptado para data pipelines |
| **AWS Lambda** | — | Serverless: pagás solo cuando se usa (futuro) |

Cada tecnología se eligió con un porqué documentado en [`docs/arquitectura.md`](docs/arquitectura.md).

---

## Los 3 Perfiles de Datlas

```
┌─────────────────────────────────────────────────────────┐
│                         USUARIO                          │
│                   arrastra un CSV                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  🧹 Perfil A: Limpieza                                  │
│  ──────────────────────                                  │
│  • Valores nulos (detecta + sugiere cómo corregir)      │
│  • Outliers (método IQR)                                │
│  • Duplicados (totales y parciales)                     │
│  • Tipos incorrectos (fechas, números, booleanos)       │
│  • Normalización (Min-Max, Standard, Robust)            │
│  • Encoding (One-Hot, Label, Ordinal)                   │
├─────────────────────────────────────────────────────────┤
│  🔍 Perfil B: Exploración                               │
│  ────────────────────────                                │
│  • Perfil automático (tipos, nulos, unique, min, max)   │
│  • Distribuciones (histogramas + boxplots)              │
│  • Correlaciones (matriz interactiva)                   │
│  • Estadísticas (tests, normalidad, ANOVA)              │
│  • Gráficos (scatter, heatmap, pairplot)                │
├─────────────────────────────────────────────────────────┤
│  ⚡ Perfil C: Pipeline (próximamente)                   │
│  ──────────────────────────                              │
│  • Flujo completo: sucio → limpio → explorado → DB     │
│  • Exportación a CSV, Excel, Parquet, JSON              │
│  • API REST para conectar con el frontend               │
└─────────────────────────────────────────────────────────┘
```

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│  DESARROLLO LOCAL (Docker)                                        │
│                                                                   │
│  docker compose up                                                │
│  ├── datlas-api    (FastAPI + Pandas)     puerto 8000             │
│  ├── datlas-db     (PostgreSQL 16)        puerto 5432             │
│  └── datlas-pgadmin (interfaz visual)     puerto 5050             │
│                                                                   │
│  🔐 Auth: X-API-Key (vacío = dev mode)                           │
│  📝 Logs: JSON estructurado con Request ID                        │
│  💾 Storage: Local (dev) / S3 (prod, configurable)                │
│                                                                   │
│  Todo corre en containers. No instalás nada en tu máquina.         │
└──────────────────────────────────────────────────────────────────┘
                          │
                          │ deploy
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  PRODUCCIÓN                                                       │
│                                                                   │
│  Render ─────────► Backend FastAPI (Docker) + PostgreSQL          │
│                     • AuthMiddleware (X-API-Key)                   │
│                     • Rate limiting (SlowAPI)                      │
│                     • Logging JSON (structlog)                     │
│                     • S3 Storage (opcional)                        │
│  GitHub Pages ───► Frontend Astro (estático)                      │
│                                                                   │
│  URLs:                                                             │
│  🔌 API       https://datlas-api.onrender.com                     │
│  📚 Docs      https://datlas-api.onrender.com/docs                │
│  🌐 Frontend  https://leandrobenjaminl.github.io/datlas            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Cómo levantar

```bash
# 1. Clonar
git clone https://github.com/LeandroBenjaminL/datlas.git
cd datlas

# 2. Configurar variables de entorno
cp .env.example .env
# (los defaults ya funcionan para desarrollo local)

# 3. Levantar todo
docker compose up --build
```

### Servicios

| Servicio | URL | Login |
|----------|-----|-------|
| API FastAPI | `http://localhost:8000` | — |
| Documentación Swagger | `http://localhost:8000/docs` | — |
| Frontend Astro | `http://localhost:4321/datlas` | — |
| Flow (Verity Engine) | `http://localhost:4321/datlas/flow` | — |
| pgAdmin | `http://localhost:5050` | `admin@datlas.com` / `admin` |
| PostgreSQL | `localhost:5432` | `datlas` / `datlas_secreto_2026` |

---

## API Reference

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/` | No | Health check + versión de la API |
| GET | `/health` | No | Health check detallado con verificación PostgreSQL |
| POST | `/api/upload` | Sí* | Subir archivo CSV |
| POST | `/api/clean/analyze` | Sí* | Analizar calidad de datos (nulos, outliers, duplicados) |
| POST | `/api/clean/apply` | Sí* | Aplicar correcciones de limpieza |
| POST | `/api/explore/analyze` | Sí* | Perfil exploratorio completo del dataset |
| GET | `/api/datasets` | Sí* | Listar datasets subidos |
| GET | `/api/datasets/{id}/analyses` | Sí* | Obtener análisis de un dataset |
| POST | `/api/pipeline/upload` | Sí* | Subir CSV para pipeline |
| POST | `/api/pipeline/run` | Sí* | Ejecutar pipeline completo |
| GET | `/api/download/{filename}` | Sí* | Descargar archivo procesado |

_\* Auth requerida solo si `API_KEY` está configurada (ver sección Seguridad)._

### Autenticación

Cuando `API_KEY` está configurada, todos los endpoints (excepto health) requieren:

```
X-API-Key: tu-api-key
```

Si `API_KEY` está vacío (default en dev), los endpoints funcionan sin auth.

### POST `/api/upload`
Sube un archivo CSV y devuelve metadata.

**Request**: `multipart/form-data` con campo `file`
**Response**:
```json
{
  "filename": "test.csv",
  "size_kb": 0.03,
  "rows": 3,
  "columns": 3,
  "col_names": ["col1", "col2", "col3"],
  "status": "ok"
}
```

### POST `/api/clean/analyze`
Analiza un dataset ya subido y detecta problemas.

**Request**:
```json
{ "filename": "sucio.csv" }
```
**Response**: Reporte con nulos, outliers (IQR), duplicados y tipos de datos.

### POST `/api/clean/apply`
Aplica correcciones al dataset y devuelve el resultado limpio.

**Request**:
```json
{
  "filename": "sucio.csv",
  "fixes": {
    "fill_nulls": { "edad": "median", "ciudad": "mode" },
    "remove_outliers": ["edad", "salario"],
    "remove_duplicates": true
  }
}
```
**Response**: Dataset limpio guardado en `data/processed/` + resumen de cambios.

### POST `/api/explore/analyze`
Genera un perfil exploratorio completo.

**Request**:
```json
{ "filename": "dataset.csv" }
```
**Response**: Perfil con tipos, estadísticas, distribuciones, correlaciones, valores únicos.

### GET `/api/datasets`
Lista todos los datasets subidos y sus análisis.

### POST `/api/pipeline/upload` + `/api/pipeline/run`
Flujo completo: subir → limpiar → explorar → exportar en pipeline.

Ver documentación interactiva en `/docs` para ejemplos completos.

---

## Documentación

| Archivo | Propósito |
|---------|-----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitectura del proyecto |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Comandos de desarrollo |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones |
| [docs/arquitectura.md](docs/arquitectura.md) | Decisiones técnicas detalladas |
| [docs/decisiones/](docs/decisiones/) | Decisiones de diseño |

## Desarrollo del frontend

El frontend Astro corre fuera de Docker:

```bash
cd frontend
npm install
npm run dev        # → http://localhost:4321/datlas
```

La API debe estar corriendo (en Docker) en `http://localhost:8000`. El CORS ya está configurado para aceptar requests desde cualquier origen en desarrollo.

---

## Variables de Entorno

Ver `.env.example` para la lista completa. Variables clave:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_KEY` | `""` (vacío) | API Key para auth. Vacío = dev mode |
| `CORS_ORIGINS` | `*` | Orígenes permitidos (separados por coma) |
| `RATE_LIMIT` | `100/minute` | Límite de requests por IP |
| `MAX_UPLOAD_SIZE_MB` | `50` | Tamaño máximo de archivo a subir |
| `LOG_LEVEL` | `INFO` | Nivel de logging (DEBUG, INFO, WARNING, ERROR) |
| `DATABASE_URL` | — | Conexión PostgreSQL (Render la inyecta) |
| `S3_BUCKET` | `""` (vacío) | Bucket S3. Vacío = storage local |

## Testing

```bash
# Todas las pruebas
cd backend && python -m pytest tests/ -v

# Con cobertura
cd backend && python -m pytest tests/ -v --cov=app/ --cov-report=term-missing

# Test manual con curl
curl -X POST http://localhost:8000/api/upload -F "file=@data/raw/test.csv"

# Test autenticado
curl -X POST http://localhost:8000/api/clean/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu-api-key" \
  -d '{"filename": "test.csv"}'
```

---

## Estructura del proyecto

```
datlas/
├── docker-compose.yml        ← 3 servicios: API + DB + pgAdmin
├── .env.example              ← template de variables de entorno
├── render.yaml               ← Config de deploy para Render
├── backend/
│   ├── Dockerfile            ← Python 3.12-slim
│   ├── requirements.txt      ← FastAPI, Pandas, SQLAlchemy...
│   ├── alembic/              ← Migraciones de base de datos
│   └── app/
│       ├── main.py           ← Entry point + middleware + health
│       ├── config.py         ← Settings (.env → Pydantic)
│       ├── logging.py        ← structlog + RequestIDMiddleware
│       ├── schemas.py        ← Pydantic schemas para API
│       ├── middleware/
│       │   ├── auth.py       ← AuthMiddleware (X-API-Key)
│       │   └── logging.py    ← RequestIDMiddleware
│       ├── routers/
│       │   ├── upload.py     ← POST /api/upload
│       │   ├── clean.py      ← POST /api/clean/analyze + /apply
│       │   ├── explore.py    ← POST /api/explore/analyze
│       │   ├── export.py     ← GET /api/download, /api/datasets
│       │   └── pipeline.py   ← Pipeline automático
│       ├── services/
│       │   ├── cleaner.py    ← DataCleaner: nulos, outliers, dupes
│       │   ├── explorer.py   ← DataExplorer: profiling
│       │   ├── pipeline.py   ← PipelineService: orquestador
│       │   └── storage.py    ← StorageBackend (Local/S3)
│       └── db/
│           ├── database.py   ← Engine, session, get_db
│           ├── models.py     ← Dataset + AnalysisResult ORM
│           └── crud.py       ← CRUD operations
├── frontend/
│   ├── astro.config.mjs      ← Config Astro + GitHub Pages
│   ├── package.json
│   └── src/
│       ├── layouts/          ← Layout base con header/footer
│       └── pages/            ← Landing, subir, limpiar, explorar
├── data/                     ← Datasets locales (gitignored)
│   ├── raw/
│   └── processed/
└── docs/
    └── arquitectura.md       ← Decisiones documentadas con porqués
```

---

## Roadmap

- ✅ **Fase 0**: Docker + PostgreSQL + FastAPI esqueleto
- ✅ **Fase 0.5**: Frontend Astro + GitHub Pages
- ✅ **Fase 1**: Perfil A — limpieza de datos (nulos, outliers, duplicados)
- ✅ **Fase 2**: Perfil B — exploración y profiling
- ✅ **Fase 3**: Perfil C — pipeline completo + exportación
- ✅ **Fase 4**: Deploy a producción (Render + GitHub Pages)
- ✅ **Fase 5**: CI/CD con GitHub Actions (tests automáticos)
- ✅ **Fase 6**: PostgreSQL persistence (SQLAlchemy + Alembic)
- ✅ **Fase 7**: Schemas Pydantic con validación en todos los endpoints
- ✅ **Fase 8**: Auth & Security (X-API-Key, rate limiting, CORS)
- ✅ **Fase 9**: Structured logging (structlog, Request ID)
- ✅ **Fase 10**: S3 Storage (Local/S3 abstracto)
- ⬜ **Fase 11**: Property-based testing con Hypothesis (ampliar cobertura)
- ⬜ **Fase 12**: Frontend conectado a API deployada

---

## Principios

- **Todo en Docker desde el día 0**: no se instala nada en la máquina host
- **Cada decisión documentada**: si cambiás algo, actualizás el porqué
- **Testeable por archivo**: cada módulo se puede probar con `if __name__ == "__main__"`
- **Un commit = una unidad de trabajo**: se entiende qué cambió y por qué
- **Diseño antes que código**: primero se piensa, después se escribe

---

## Licencia

MIT — hacé lo que quieras.
