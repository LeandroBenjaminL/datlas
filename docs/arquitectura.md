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

### 4. Containerización: Docker

**Por qué Docker desde el día 0**:
- **Entorno idéntico en todas partes**: tu Windows, mi Linux, AWS, todo igual
- **Sin "en mi máquina funciona"**: el Dockerfile define exactamente qué versión de Python, qué dependencias
- **PostgreSQL sin instalación**: levanta con un comando, se destruye con otro

---

### 5. Frontend: Astro

| Alternativas | Por qué NO |
|-------------|------------|
| React/Next.js | Muy pesado para un portfolio de datos. 40KB+ de JS mínimo |
| Streamlit | Rápido para prototipos pero limitado en diseño y no es web real |
| SvelteKit | Buena opción, pero Astro es más liviano para contenido con islas interactivas |

**Por qué Astro**:
- 0KB de JavaScript por defecto — la página carga instantáneo
- Islas de interactividad: solo cargás JS donde realmente se necesita (upload, clean)
- Build a estáticos → deploy a GitHub Pages en 2 comandos
- 4 páginas: landing, subir (con drag-and-drop), limpiar (con reporte interactivo), explorar (placeholder)

---

### 6. Cloud: AWS (Free Tier) — futuro

```
DESARROLLO LOCAL (Docker)              PRODUCCIÓN (AWS Free Tier)
docker compose up                      GitHub Pages → Frontend Astro
├── datlas-api (FastAPI)    :8000      API Gateway → Lambda (FastAPI via Mangum)
├── datlas-db (PostgreSQL)  :5432      RDS PostgreSQL
└── datlas-pgadmin           :5050     S3 (datasets)
```

---

### 7. Flujo de Datos

```
USUARIO SUBE CSV
       │
       ▼
POST /api/upload
  → Guarda en data/raw/
  → Devuelve metadata (filas, columnas, tipos)
       │
       ▼
POST /api/clean/analyze
  → DataCleaner.detect_nulls()
  → DataCleaner.detect_outliers()   (IQR)
  → DataCleaner.detect_duplicates()
  → DataCleaner.detect_types()
       │
       ▼
POST /api/clean/apply
  → fill_nulls (median/mean/mode)
  → remove_outliers (filtro IQR)
  → remove_duplicates
  → Guarda en data/processed/
  → Devuelve dataset limpio + reporte
       │
       ▼
PERFIL B: Exploración (futuro)
PERFIL C: Pipeline + Export (futuro)
```

---

## Estructura del Proyecto

```
datlas/
│
├── docker-compose.yml           ← 3 servicios: API + DB + pgAdmin
├── .env.example                 ← Variables de entorno
│
├── backend/                     ← FastAPI + Pandas
│   ├── Dockerfile               ← Python 3.12-slim
│   ├── requirements.txt         ← FastAPI, Pandas, SQLAlchemy
│   └── app/
│       ├── main.py              ← Entry point FastAPI + CORS
│       ├── config.py            ← Settings desde .env
│       ├── routers/
│       │   ├── upload.py        ← POST /api/upload
│       │   └── clean.py         ← POST /api/clean/analyze + /apply
│       ├── services/
│       │   └── cleaner.py       ← DataCleaner: nulos, outliers, dupes
│       ├── db/                  ← (futuro) modelos SQLAlchemy
│       └── utils/               ← (futuro) validadores, exportadores
│
├── frontend/                    ← Astro 5 (estático)
│   ├── astro.config.mjs         ← Config con base /datlas para GitHub Pages
│   ├── package.json
│   └── src/
│       ├── layouts/
│       │   └── Layout.astro     ← Layout base con header/footer
│       └── pages/
│           ├── index.astro      ← Landing
│           ├── subir.astro      ← Upload con drag-and-drop + fetch API
│           ├── limpiar.astro    ← Analyze + apply fixes desde la UI
│           └── explorar.astro   ← Placeholder
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
# PostgreSQL
POSTGRES_USER=datlas
POSTGRES_PASSWORD=datlas_secreto_2026
POSTGRES_DB=datlas_db
POSTGRES_PORT=5432

# pgAdmin
PGADMIN_EMAIL=admin@datlas.com
PGADMIN_PASSWORD=admin

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# AWS (futuro)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_REGION=us-east-1
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
4. ⬜ Perfil B — Exploración (distribuciones, correlaciones, estadísticas)
5. ⬜ Perfil C — Pipeline completo + exportación
6. ⬜ Deploy a AWS Lambda + API Gateway
7. ⬜ CI/CD con GitHub Actions

---

## Principios de Diseño

- **Todo en Docker desde el día 0**: no se instala nada en la máquina host
- **Una decisión = una sección en este doc**: si cambiás algo, actualizás el porqué
- **Separación de concerns**: services/ tiene la lógica pura, routers/ tiene el transporte
- **Nunca decidir sin mostrar alternativas**: el alumno elige, el profe muestra opciones
