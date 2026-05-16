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
| Tests | pytest + ruff | CI con lint + tests en PRs |

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/upload` | Subir archivo CSV |
| POST | `/api/clean/analyze` | Analizar calidad de datos |
| POST | `/api/clean/apply` | Aplicar limpieza |
| POST | `/api/explore/analyze` | Perfil completo + distribuciones + correlaciones |
| GET | `/api/datasets` | Listar datasets raw y procesados |
| GET | `/api/download/{filename}` | Descargar CSV |
| POST | `/api/pipeline/upload` | Pipeline completo: subir + limpiar + explorar |
| POST | `/api/pipeline/run` | Pipeline sobre archivo existente |

## Perfiles

| Perfil | Estado | Descripción |
|--------|--------|-------------|
| A — Clean | ✅ | Subida, análisis de calidad, limpieza automática |
| B — Explore | ✅ | Profiling, distribuciones, correlaciones, estadísticas |
| C — Pipeline | ✅ | Upload → Clean → Explore en un solo paso |

## Flujo de datos

```
POST /api/upload → data/raw/ → POST /api/clean/analyze → reporte
                                    ↓
                            POST /api/clean/apply  → data/processed/
                                                      ↓
                                            POST /api/explore/analyze → reporte EDA

POST /api/pipeline/upload → [upload → clean → explore] → reporte combinado
```

## Tests

```
backend/tests/
├── conftest.py              # Fixtures compartidos
├── test_cleaner.py          # 11 tests — DataCleaner
├── test_explorer.py         # 10 tests — DataExplorer
├── test_pipeline.py         # 7 tests  — PipelineService
└── data/test.csv            # Dataset fixture
```

Ejecutar: `python -m pytest tests/ -v`

## CI/CD

| Evento | Acción |
|--------|--------|
| PR a `main` (backend/) | Ruff lint + pytest |
| Push a `main` (frontend/) | Deploy Astro → GitHub Pages |

## Principios

- **Todo en Docker**: no se instala nada en la máquina host
- **Separación de concerns**: services/ = lógica pura, routers/ = transporte
- **Datos inmutables**: nunca se modifica el dataset original
- **Decisiones documentadas**: cada tecnología tiene su porqué
- **CI en PRs**: cambios grosos pasan por branch → PR → checks → merge

Ver [docs/arquitectura.md](docs/arquitectura.md) para el detalle completo de decisiones técnicas.
