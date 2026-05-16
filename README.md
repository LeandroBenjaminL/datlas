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
| **Astro** | 5 | 0KB JS por defecto, islas de interactividad, build estático |
| **pgAdmin** | latest | Interfaz visual para explorar la DB sin tocar terminal |
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
┌──────────────────────────────────────────────────────────┐
│  DESARROLLO LOCAL (Docker)                                │
│                                                           │
│  docker compose up                                        │
│  ├── datlas-api    (FastAPI + Pandas)     puerto 8000     │
│  ├── datlas-db     (PostgreSQL 16)        puerto 5432     │
│  └── datlas-pgadmin (interfaz visual)     puerto 5050     │
│                                                           │
│  Todo corre en containers. No instalás nada en tu máquina. │
└──────────────────────────────────────────────────────────┘
                          │
                          │ deploy (futuro)
                          ▼
┌──────────────────────────────────────────────────────────┐
│  PRODUCCIÓN (AWS Free Tier)                               │
│                                                           │
│  GitHub Pages ───► Frontend Astro (estático)             │
│  API Gateway  ───► Lambda (FastAPI via Mangum)           │
│  RDS ────────────► PostgreSQL                             │
│  S3 ─────────────► Datasets y archivos                    │
└──────────────────────────────────────────────────────────┘
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

## Testing

```bash
# Test manual con curl
curl -X POST http://localhost:8000/api/upload -F "file=@data/raw/test.csv"

# Test de análisis
curl -X POST http://localhost:8000/api/clean/analyze \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.csv"}'
```

---

## Estructura del proyecto

```
datlas/
├── docker-compose.yml        ← 3 servicios: API + DB + pgAdmin
├── .env.example              ← template de variables de entorno
├── backend/
│   ├── Dockerfile            ← Python 3.12-slim
│   ├── requirements.txt      ← FastAPI, Pandas, SQLAlchemy...
│   └── app/
│       ├── main.py           ← Entry point FastAPI
│       ├── config.py         ← Settings (.env → Pydantic)
│       ├── routers/
│       │   ├── upload.py     ← POST /api/upload
│       │   └── clean.py      ← POST /api/clean/analyze + /apply
│       ├── services/
│       │   └── cleaner.py    ← DataCleaner: nulos, outliers, dupes
│       ├── db/               ← SQLAlchemy models (futuro)
│       └── utils/            ← Validators, exporters (futuro)
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
- ⬜ **Fase 2**: Perfil B — exploración y profiling
- ⬜ **Fase 3**: Perfil C — pipeline completo + exportación
- ✅ **Fase 3.5**: Flow — editor visual de pipelines con Verity Engine (`/datlas/flow`)
- ⬜ **Fase 4**: Deploy a AWS Lambda + API Gateway
- ⬜ **Fase 5**: CI/CD con GitHub Actions (tests automáticos)

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
