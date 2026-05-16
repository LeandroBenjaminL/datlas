# Changelog

## [0.3.0] — 2026-05-16

### Added
- Seguridad: bandit SAST (seguridad de código), dependabot (pip/npm/docker/actions)
- Pre-commit hooks: ruff lint+format, bandit, whitespace, yaml check
- Tests de integración: 13 tests con httpx contra API real (upload → clean → explore → pipeline → download)
- Property-based tests: 4 tests con hypothesis (fuzz DataCleaner + DataExplorer)
- Total: 45 tests unitarios + integración + fuzz, 90% cobertura
- CI: 4 jobs paralelos — security (bandit+sarif), lint-backend (ruff), test-backend (coverage), frontend (build)
- Dependabot: actualizaciones automáticas semanales/mensuales para pip, npm, docker, actions
- Perfil C — Pipeline automático: upload → clean → explore en un solo paso
- PipelineService: orquesta DataCleaner + DataExplorer con auto-fixes
- POST /api/pipeline/upload y /api/pipeline/run endpoints
- Frontend /datlas/pipeline: dropzone, track de progreso, resultados combinados
- Frontend rediseñado: step bar, landing con hero animado, tabs en explorar, badges de severidad
- pyproject.toml: pytest + ruff config centralizada

### Fixed
- dateutil warning en cleaner.py con format="mixed"
- ruff E402 (imports top-level), F401 (unused), E702, F841
- content-type assert en test de download
- download 404 (/api/export/ → /api/download/)

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
