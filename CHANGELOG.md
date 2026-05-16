# Changelog

## [0.3.0] — 2026-05-16

### Added
- Perfil C — Pipeline automático: upload → clean → explore en un solo paso
- `POST /api/pipeline/upload` — subir CSV y recibir reporte completo
- `POST /api/pipeline/run` — ejecutar pipeline sobre archivo existente
- PipelineService: orquesta DataCleaner + DataExplorer con auto-fixes
- Frontend `/datlas/pipeline`: dropzone, track de progreso animado, resultados
- Step "Pipeline" en barra de progreso y navegación
- Tests: 28 tests para cleaner, explorer y pipeline services
- CI: GitHub Action con ruff lint + pytest en PRs contra main

### Changed
- Frontend rediseñado completo: step bar, landing con hero animado, tabs en explorar, badges de severidad, dropzone con glow
- Landing `ventas.csv` y `pokemonDB_dataset.csv` visibles con links a limpiar/explorar
- `cleaner.py`: `format="mixed"` en `pd.to_datetime` para eliminar warnings de dateutil
- `backend/requirements.txt`: agregados pytest, ruff

### Fixed
- Download 404: `/api/export/` → `/api/download/`
- `download_url` hardcodeado en limpiar.astro

## [0.2.0] — 2026-05-11

### Added
- frontend conectado a la API: upload drag-and-drop + limpieza interactiva
- Google-style docstrings en todos los módulos Python
- ARCHITECTURE.md, CONTRIBUTING.md, DEVELOPMENT.md, CHANGELOG.md
- docs/arquitectura.md actualizada con el estado real del código
- README con secciones Testing, Frontend Dev y API Reference

### Changed
- Perfil A (limpieza) marcado como completo en el roadmap

## [0.1.0] — 2026-05-08

### Added
- Docker Compose con FastAPI + PostgreSQL 16 + pgAdmin
- Backend FastAPI esqueleto (main.py, config.py)
- Frontend Astro con layout oscuro + paleta violeta
- POST /api/upload — endpoint de subida de CSV
- POST /api/clean/analyze — detección de nulos, outliers, duplicados
- POST /api/clean/apply — aplicación de correcciones configurables
- DataCleaner service con IQR, imputación y limpieza
- Documentación de arquitectura en docs/arquitectura.md
