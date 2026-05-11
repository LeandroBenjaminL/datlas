# Changelog

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
