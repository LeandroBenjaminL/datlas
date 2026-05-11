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

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/upload` | Subir archivo CSV |
| POST | `/api/clean/analyze` | Analizar calidad de datos |
| POST | `/api/clean/apply` | Aplicar limpieza |

## Flujo de datos

```
POST /api/upload → data/raw/ → POST /api/clean/analyze → reporte
                                    ↓
                            POST /api/clean/apply  → data/processed/
```

## Principios

- **Todo en Docker**: no se instala nada en la máquina host
- **Separación de concerns**: services/ = lógica pura, routers/ = transporte
- **Datos inmutables**: nunca se modifica el dataset original
- **Decisiones documentadas**: cada tecnología tiene su porqué

Ver [docs/arquitectura.md](docs/arquitectura.md) para el detalle completo de decisiones técnicas.
