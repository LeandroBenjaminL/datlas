# Investigación Complementaria — Datlas

> **Sesión**: subagent-chat-019e482a (complementaria)
> **Propósito**: Investigación en profundidad de áreas no cubiertas por la auditoría principal, para informar decisiones de refactor.
> **Fecha**: 2026-05-21

---

## Índice

1. [Seguridad — Vectores Adicionales](#1-seguridad--vectores-adicionales)
2. [Database / Schema](#2-database--schema)
3. [Testing — Cobertura y Estrategia](#3-testing--cobertura-y-estrategia)
4. [CI/CD — Mejoras y Automatización](#4-cicd--mejoras-y-automatización)
5. [Frontend — Deuda Técnica y Consistencia](#5-frontend--deuda-técnica-y-consistencia)
6. [Dependencias — Auditoría y Locking](#6-dependencias--auditoría-y-locking)
7. [Infraestructura / Monitoreo](#7-infraestructura--monitoreo)
8. [API Surface y Documentación](#8-api-surface-y-documentación)
9. [Plan de Acción Recomendado](#9-plan-de-acción-recomendado)

---

## 1. Seguridad — Vectores Adicionales

La auditoría principal encontró path traversal crítico y falta de autenticación. Complemento con vectores que vale la pena revisar.

### 1.1 Secretos en el repositorio

| Archivo              | Secreto                                       | Riesgo                                                        |
| -------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| `.env`               | `POSTGRES_PASSWORD=datlas_secreto_2026`       | ALTO — está commiteado                                        |
| `.env.example`       | Misma password de ejemplo                     | BAJO — es ejemplo, pero sugiere que en producción se use esta |
| `docker-compose.yml` | `POSTGRES_PASSWORD`, `PGADMIN_PASSWORD=admin` | ALTO — defaults inline                                        |

**Recomendación**: `.env` debe estar en `.gitignore` (ya está). Pero **el archivo ya fue commiteado** — hay que rotar el secreto y purgar del historial de git. Usar `git filter-branch` o `bfg-repo-cleaner`.

### 1.2 `.env` ya commiteado — alcance del daño

```bash
git log --all --diff-filter=A -- .env
```

Si `.env` apareció en algún commit, la password de PostgreSQL y pgAdmin están en el historial. Cualquiera que clone el repo puede verla.

**Recomendación**: después de rotar credenciales, purgar con BFG.

### 1.3 Bandit config — exclusiones peligrosas

```ini
[bandit]
skips: B101,B404,B603,B607
```

- **B101** (`assert`): lo skipea — asserts pueden dejar info en producción
- **B404** (`import subprocess`): lo skipea — subprocess module import es bandera de seguridad
- **B603** (`subprocess_without_shell_equals_true`): lo skipea
- **B607** (`start_process_with_partial_path`): lo skipea

Si bien el código actual no usa subprocess, estas exclusiones eliminan la detección si alguien lo agrega después.

**Recomendación**: eliminar los skips; si no hay subprocess, Bandit no va a falsopositivar.

### 1.4 Sin rate limiting

`POST /api/upload` acepta archivos sin límite de rate. Un atacante podría:

- Subir archivos gigantes hasta llenar el disco
- Subir miles de archivos chicos (ataque de recursos)
- Enviar payloads malformados en loop

**Recomendación**: agregar `slowapi` o middleware de rate limiting. FastAPI tiene buena integración con `slowapi`.

### 1.5 Validación de upload — solo extensión

```python
if not file.filename.endswith(".csv"):
    raise HTTPException(400, "Solo archivos .csv")
```

Esto solo valida extensión. Un `.exe` renombrado a `.csv` pasa. Además:

- No hay límite de tamaño explícito (el frontend dice 100MB pero backend no lo enforcea)
- No hay validación de content-type en backend
- No hay sanitización del filename (path traversal ya cubierto por otra auditoría)

**Recomendación**:

```python
import magic  # python-magic
mime = magic.from_buffer(await file.read(1024), mime=True)
await file.seek(0)
if mime not in ("text/csv", "text/plain", "application/octet-stream"):
    raise HTTPException(400, "Tipo de archivo no permitido")
```

### 1.6 CORS — allow_origins=["*"]

CORS con `allow_credentials=True` + `allow_origins=["*"]` es una **combinación inválida** según la especificación. Los browsers lo ignoran. En desarrollo no importa, pero si se despliega es un agujero.

**Recomendación**: configurar origins específicos vía variable de entorno.

### 1.7 Sin headers de seguridad

No hay CSP, X-Content-Type-Options, X-Frame-Options, ni SecurityHeadersMiddleware.

**Recomendación**: agregar `SecureHeadersMiddleware` o configurar nginx para servirlos.

---

## 2. Database / Schema

### 2.1 Estado actual

PostgreSQL 16 está en docker-compose, SQLAlchemy 2.0 y Alembic 1.14 están instalados, pero:

- `backend/app/db/__init__.py` está **vacío** (solo `# DB package`)
- No hay modelos SQLAlchemy
- No hay migraciones de Alembic
- No hay conexión a la base en runtime (config.py tiene `database_url` pero no se importa en `main.py`)
- El directorio `data/.gitkeep` sugiere que algún dato se guarda en CSV, no en DB

### 2.2 ¿Para qué se necesita la DB?

Analizando el código:

- **Upload**: guarda archivos en `data/raw/` (filesystem, no DB)
- **Clean**: opera sobre DataFrames en memoria
- **Explore**: opera sobre DataFrames en memoria
- **Export**: lee del filesystem
- **Pipeline**: opera en memoria + filesystem

**Ningún endpoint actual usa PostgreSQL**. La DB está configurada pero no integrada.

### 2.3 ¿Debería integrarse?

| Factor              | Decisión                                                                 |
| ------------------- | ------------------------------------------------------------------------ |
| Dataset persistence | Filesystem es suficiente para datasets chicos                            |
| Metadata / tracking | DB sería útil para tracking: quién subió qué, cuándo, config de limpieza |
| Features futuros    | Auth (users), versionado de datasets, jobs async — DB necesaria          |
| Complejidad ahora   | Agregar DB ahora es sobreingeniería si no se necesita                    |

**Recomendación**: definir si la DB es para la Fase 2 (post-seguridad) o se elimina temporalmente del docker-compose para reducir superficie de ataque. Si se mantiene, crear al menos un modelo `Dataset` y una migración Alembic de ejemplo.

### 2.4 Si se integra, esquema sugerido

```python
# backend/app/models/dataset.py
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    size_bytes = Column(Integer)
    rows = Column(Integer)
    columns = Column(Integer)
    col_names = Column(JSON)
    uploaded_at = Column(DateTime, server_default="now()")
    status = Column(String(50), default="raw")  # raw, cleaned, explored
```

### 2.5 Sesgo de supervivencia en la DB

La base postgres está en docker-compose pero no se usa. Esto significa:

- Configuración extra sin beneficio
- `psycopg2-binary` en requirements sin uso
- Puerto 5432 expuesto públicamente
- pgAdmin escucha en 5050

**Recomendación**: decidir si se necesita ahora. Si no, sacar db + pgadmin del docker-compose y de requirements. Agregarlos cuando haya un caso de uso real.

---

## 3. Testing — Cobertura y Estrategia

### 3.1 Estado actual

| Suite           | Archivos                              | Lo que cubre                                                                                |
| --------------- | ------------------------------------- | ------------------------------------------------------------------------------------------- |
| Unit (cleaner)  | `test_cleaner.py` (10 tests)          | DataCleaner: load, nulls, outliers, duplicates, types, clean strategies                     |
| Unit (explorer) | `test_explorer.py` (9 tests)          | DataExplorer: profile, distributions, correlations, statistics, preview, categorical, nulls |
| Unit (pipeline) | `test_pipeline.py` (7 tests)          | PipelineService: run, auto-fixes, clean, explore                                            |
| Integration     | `test_integration.py` (11 tests)      | Endpoints: health, upload, clean, explore, datasets, download, error cases                  |
| Hypothesis      | `test_hypothesis.py` (2 test classes) | Property-based: cleaner + explorer con datos aleatorios                                     |

### 3.2 Brechas de testing

| Área                   | Ausente                                                               | Riesgo     |
| ---------------------- | --------------------------------------------------------------------- | ---------- |
| **Seguridad**          | Path traversal, file size, content-type, CORS, auth bypass            | 🔴 Crítico |
| **Carga**              | Archivos grandes (>100MB), muchos archivos                            | 🟠 Medio   |
| **Concurrencia**       | Uploads simultáneos, race conditions                                  | 🟠 Medio   |
| **Frontend**           | Astro pages render correcto, componentes interactivos                 | 🟡 Bajo    |
| **Edge cases**         | Archivos vacíos, encoding no UTF-8, CSV corrupto, columnas sin nombre | 🟠 Medio   |
| **Integración con DB** | No aplica (DB no integrada)                                           | 🟢 N/A     |
| **Fuzzing**            | Hypothesis cubre algo, pero con pocas iteraciones                     | 🟡 Bajo    |
| **Performance**        | Timeout en endpoints pesados (explore con datasets grandes)           | 🟠 Medio   |
| **Regression**         | Sin snapshot testing ni golden files                                  | 🟡 Bajo    |

### 3.3 Coverage report

Hay un `.coverage` en backend/ (generado por pytest-cov). Pero **no hay umbral mínimo configurado** en CI. Si coverage baja, no falla.

**Recomendación en CI**:

```yaml
- run: python -m pytest tests/ -v --tb=short --cov=app/ --cov-report=term-missing --cov-fail-under=80 -x
```

### 3.4 Hypothesis — mejora de parámetros

```python
@settings(max_examples=20)  # MUY bajo para property-based testing
```

Hypothesis necesita ~100-200 ejemplos para encontrar edge cases. 20 es casi inútil.

**Recomendación**: subir a `max_examples=200` o dejarlo default (100). Agregar `stateful testing` para el pipeline.

### 3.5 Tests de seguridad — plantilla

```python
@pytest.mark.asyncio
async def test_path_traversal_upload(client):
    """Intentar path traversal en upload."""
    csv_content = b"a,b\n1,2"
    r = await client.post(
        "/api/upload",
        files={"file": ("../../../etc/passwd.csv", csv_content, "text/csv")},
    )
    # El archivo no debería escribirse fuera de data/raw/
    assert r.status_code == 400 or r.status_code == 422

@pytest.mark.asyncio
async def test_path_traversal_download(client):
    """Intentar path traversal en download."""
    r = await client.get("/api/download/../../../etc/passwd")
    assert r.status_code == 404
```

---

## 4. CI/CD — Mejoras y Automatización

### 4.1 CI actual

```yaml
jobs: security → lint-backend → test-backend → frontend (paralelo)
```

**Fortalezas**:

- Ruff lint + format check
- Bandit SAST con artifact upload
- pytest con coverage
- Astro build check
- Dependabot activo (pip, npm, docker, actions)

**Debilidades**:

- No corre tests de integración con DB real (usan ASGI transport, no levantan infra)
- Bandit corre pero sus resultados se suben como artifact — nadie los revisa en el PR
- No hay Docker build test (el Dockerfile puede romperse sin que CI lo detecte)
- No hay push a registro de imágenes
- No hay security scanning de dependencias (pip-audit, npm audit, Trivy)
- No hay deploy automático del backend
- Coverage no tiene umbral mínimo

### 4.2 Mejoras recomendadas

```yaml
# Agregar a CI:
- name: Security scan de dependencias
  run: |
    pip install pip-audit
    pip-audit -r backend/requirements.txt --desc

- name: Docker build test
  run: docker compose build api

- name: Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: "docker.io/library/datlas-api:latest"
```

### 4.3 Deploy

Solo deploya frontend a GitHub Pages. El backend no tiene deploy.

**Recomendación**: evaluar si el backend necesita deploy (Fly.io, Railway, o similar) o si queda como herramienta local/Docker. Si se deploya, agregar CD con Docker build + push.

### 4.4 Dependabot

Configurado correctamente para pip, npm, docker, actions. Las schedules semanales/mensuales están bien.

**Único issue**: no hay lockfile en backend (`requirements.txt` no pincha versiones transativas). Dependabot solo actualizará las directas.

---

## 5. Frontend — Deuda Técnica y Consistencia

### 5.1 API URL inconsistente — 🔴 BUG

```javascript
// index.astro (home):
const API = "http://localhost:8000";

// subir.astro:
const API = "";

// limpiar.astro:
const API = "";
```

**Problema**:

- `index.astro` hardcodea `http://localhost:8000` — en producción con nginx reverse proxy, la API está en `/api/` (relativo), no en localhost:8000
- Las otras páginas usan `''` (relativo), que funciona con nginx pero **falla en desarrollo** si el frontend está en otro puerto

**Solución**: usar una variable de entorno de build o siempre relativo (que el reverse proxy maneje):

```javascript
// astro.config.mjs
export default defineConfig({
  define: {
    "import.meta.env.API_BASE": JSON.stringify(process.env.API_BASE || ""),
  },
});

// En las páginas:
const API = import.meta.env.API_BASE || "";
```

### 5.2 Sin TypeScript

Los scripts inline en Astro son JavaScript plano. Para un proyecto de este tamaño no es crítico, pero:

- Sin type-checking en las respuestas de la API
- Sin autocompletado de shape de datos
- Posibles undefined errors en runtime

**Recomendación**: al menos tipar las respuestas de la API con interfaces.

### 5.3 Sin manejo de estado global

Cada página maneja su estado con variables globales y manipulación directa del DOM. Esto escala mal. Para mantenerse en vanilla:

- Extraer fetch helpers en un módulo compartido
- Usar data-atributos en vez de IDs volátiles

### 5.4 Sin SRI (Subresource Integrity)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

No hay SRI. Si el CDN es comprometido, el frontend ejecuta código malicioso.

**Recomendación**: usar `npm install chart.js` y embeber en el build de Astro, o agregar atributo `integrity`.

### 5.5 nginx.conf — observaciones

```
location /api/ {
    proxy_pass http://api:8000;
    # Sin timeouts configurados
    # Sin proxy_read_timeout para endpoints lentos (explore)
    # Sin limitación de tamaño de upload
}
```

**Recomendación**: agregar límites y timeouts:

```nginx
location /api/ {
    proxy_pass http://api:8000;
    proxy_read_timeout 120s;
    client_max_body_size 100M;
}
```

---

## 6. Dependencias — Auditoría y Locking

### 6.1 Backend (requirements.txt)

Dependencias directas verificadas contra versiones actuales (mayo 2026):

| Paquete         | Versión | Estado                        |
| --------------- | ------- | ----------------------------- |
| fastapi         | 0.115.6 | ✅ Actual                     |
| uvicorn         | 0.34.0  | ✅ Actual                     |
| pydantic        | 2.10.4  | ✅ Actual                     |
| pandas          | 3.0.3   | ✅ Actual                     |
| sqlalchemy      | 2.0.36  | ⚠️ No se usa                  |
| psycopg2-binary | 2.9.10  | ⚠️ No se usa                  |
| alembic         | 1.14.1  | ⚠️ No se usa                  |
| matplotlib      | 3.10.9  | ⚠️ No se usa en código actual |
| seaborn         | 0.13.2  | ⚠️ No se usa en código actual |
| hypothesis      | >=6.125 | ✅ Uso adecuado               |
| bandit          | 1.9.4   | ✅ Uso adecuado               |

**Dependencias no utilizadas** (peso muerto):

- `sqlalchemy`, `psycopg2-binary`, `alembic` — si la DB no se integra pronto
- `matplotlib`, `seaborn` — si los charts se generan en frontend

**Problema**: no hay `pip freeze > requirements-lock.txt`. Cualquier build puede instalar versiones transativas diferentes.

### 6.2 Frontend (package.json)

```json
{
  "dependencies": {
    "astro": "^6.3.3"
  }
}
```

Una sola dependencia. Limpio. Lock file (`package-lock.json` y `pnpm-lock.yaml`) presente.

### 6.3 Docker

- `python:3.13-slim` — actual, buena
- `node:22-alpine` — actual, buena
- `postgres:16-alpine` — actual
- `dpage/pgadmin4:latest` — ⚠️ `latest` puede romperse inesperadamente

**Recomendación**: pinchar versión de pgAdmin (ej: `dpage/pgadmin4:2026-05-21-1` o similar)

### 6.4 Vulnerabilidades conocidas

Sin correr audit tool no se puede garantizar, pero:

- `psycopg2-binary 2.9.10` — sin CVEs conocidas a fecha
- `fastapi 0.115.6` — estable
- `pandas 3.0.3` — estable

**Recomendación**: agregar `pip-audit` al CI para detectar vulnerabilidades en cada PR.

---

## 7. Infraestructura / Monitoreo

### 7.1 Salud actual

Solo `GET /` health check que devuelve `{"status": "online"}`. No verifica:

- Conexión a DB (cuando exista)
- Espacio en disco
- Que directorios `data/raw` y `data/processed` sean escribibles

### 7.2 Logging

```python
print(f"🚀 Datlas API starting on http://{settings.API_HOST}:{settings.API_PORT}")
```

**Print statements en lugar de logging**. En producción esto no es capturable por sistemas de logging.

**Recomendación**:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Datlas API starting on %s:%s", settings.API_HOST, settings.API_PORT)
```

### 7.3 Sin métricas

No hay Prometheus, OpenTelemetry, ni endpoints de métricas. No se puede monitorear:

- Latencia por endpoint
- Tasa de error
- Throughput
- Uso de memoria/CPU

**Recomendación**: agregar `prometheus-fastapi-instrumentator` para métricas básicas sin esfuerzo.

### 7.4 Docker healthchecks

El API container **no tiene healthcheck**. Solo DB tiene. Si la API crashea, Docker no lo detecta.

**Recomendación en docker-compose**:

```yaml
api:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/"]
    interval: 30s
    timeout: 5s
    retries: 3
```

### 7.5 Sin estrategia de backups

PostgreSQL tiene un volumen `pgdata` pero no hay:

- Backup automático
- Punto de restauración
- WAL archiving

Si la DB se integra en serio, esto es necesario.

### 7.6 Sin .dockerignore

**Caso**: el Dockerfile copia todo el contexto (`COPY . .`), incluyendo `.env`, `.git`, `node_modules`, `tests`, `.coverage`.

- `python:3.13-slim` no tiene curl — no se puede healthcheck sin instalarlo
- No hay `.dockerignore` en `backend/` ni en `frontend/`

**Recomendación**:

```dockerignore
# backend/.dockerignore
.git
__pycache__/
*.pyc
.env
tests/
.coverage
api.log
api.err
api.out
```

---

## 8. API Surface y Documentación

### 8.1 Endpoints documentados en ARCHITECTURE.md vs reales

ARCHITECTURE.md documenta **4 endpoints** (health, upload, analyze, apply). La API real tiene **11 endpoints** en 5 routers.

| Documentado             | Real                         | Diferencia       |
| ----------------------- | ---------------------------- | ---------------- |
| GET /                   | ✅                           | Health check     |
| POST /api/upload        | ✅                           | -                |
| POST /api/clean/analyze | ✅                           | -                |
| POST /api/clean/apply   | ✅                           | -                |
| ❌                      | POST /api/explore/analyze    | Faltante en docs |
| ❌                      | GET /api/datasets            | Faltante en docs |
| ❌                      | GET /api/download/{filename} | Faltante en docs |
| ❌                      | POST /api/pipeline/upload    | Faltante en docs |
| ❌                      | POST /api/pipeline/run       | Faltante en docs |

**Recomendación**: sincronizar ARCHITECTURE.md con la API real.

### 8.2 OpenAPI / Swagger

FastAPI genera `/docs` automáticamente, lo cual está bien. Pero:

- No hay `summary` ni `response_description` en los endpoints (falta metadata)
- Los modelos de respuesta no están tipados con Pydantic
- No hay ejemplos de request/response

**Recomendación**: agregar Pydantic response models para que Swagger sea más útil.

### 8.3 Status codes

- 400 para `.csv` validation — bien
- 404 para file not found — bien
- 500 en pipeline con `Exception` genérico — mejorable

```python
except Exception as e:
    raise HTTPException(500, f"Pipeline error: {str(e)}") from e
```

Exponer el mensaje de excepción interna puede leakear información. Usar `HTTPException(500, "Pipeline processing failed")` y loguear el detalle.

---

## 9. Plan de Acción Recomendado

Prioridad basada en la decisión de la otra sesión (Seguridad → Infra → Frontend → Features).

### Fase 1B — Complementos de Seguridad (junto con Fase 1)

| #   | Tarea                                                           | Prioridad | Archivos                                          |
| --- | --------------------------------------------------------------- | --------- | ------------------------------------------------- |
| 1   | Rotar credenciales + purgar `.env` de git history               | 🔴 Alta   | `.env`, git history                               |
| 2   | Revisar `bandit` skips → eliminar exclusiones innecesarias      | 🔴 Alta   | `.bandit`                                         |
| 3   | Agregar `.dockerignore` a backend y frontend                    | 🔴 Alta   | `backend/.dockerignore`, `frontend/.dockerignore` |
| 4   | Agregar validación de content-type en upload + límite de tamaño | 🔴 Alta   | `upload.py`                                       |
| 5   | Agregar healthcheck a api container                             | 🔴 Alta   | `docker-compose.yml`                              |
| 6   | Agregar logging (reemplazar `print()`)                          | 🟠 Media  | `main.py`, routers                                |
| 7   | Configurar CORS por variable de entorno                         | 🟠 Media  | `main.py`, `config.py`                            |
| 8   | Agregar security headers middleware                             | 🟠 Media  | `main.py`                                         |

### Fase 2B — Testing Complementario

| #   | Tarea                                                | Prioridad | Archivos                         |
| --- | ---------------------------------------------------- | --------- | -------------------------------- |
| 1   | Agregar tests de path traversal                      | 🔴 Alta   | `tests/test_security.py` (nuevo) |
| 2   | Agregar tests de validación de upload (tamaño, tipo) | 🟠 Media  | `tests/test_security.py`         |
| 3   | Subir `max_examples` de Hypothesis a 200             | 🟡 Baja   | `test_hypothesis.py`             |
| 4   | Agregar `--cov-fail-under=80` en CI                  | 🟠 Media  | `.github/workflows/ci.yml`       |
| 5   | Agregar `pip-audit` a CI                             | 🟠 Media  | `.github/workflows/ci.yml`       |

### Fase 3B — Database e Infra

| #   | Tarea                                                    | Prioridad | Archivos                                  |
| --- | -------------------------------------------------------- | --------- | ----------------------------------------- |
| 1   | Decidir: mantener DB ahora o sacar del docker-compose    | 🟠 Media  | `docker-compose.yml`                      |
| 2   | Si se mantiene: crear modelo Dataset + migración Alembic | 🟠 Media  | `backend/app/models/`, `backend/alembic/` |
| 3   | Agregar rate limiting a endpoints de upload              | 🟠 Media  | `main.py`, `requirements.txt`             |
| 4   | Agregar prometheus metrics                               | 🟡 Baja   | `main.py`                                 |

### Fase 4B — Frontend

| #   | Tarea                                        | Prioridad | Archivos                           |
| --- | -------------------------------------------- | --------- | ---------------------------------- |
| 1   | **BUG**: unificar API URL (relativo siempre) | 🔴 Alta   | `index.astro`, `subir.astro`, etc. |
| 2   | Agregar límite de tamaño en nginx            | 🟠 Media  | `nginx.conf`                       |
| 3   | Migrar chart.js de CDN a npm (SRI)           | 🟡 Baja   | `package.json`, layouts            |
| 4   | Tipar responses de API en frontend           | 🟡 Baja   | Páginas `.astro`                   |

### Fase 5 — Docs y API Surface

| #   | Tarea                                            | Prioridad | Archivos          |
| --- | ------------------------------------------------ | --------- | ----------------- |
| 1   | Sincronizar ARCHITECTURE.md con endpoints reales | 🟠 Media  | `ARCHITECTURE.md` |
| 2   | Agregar Pydantic response models                 | 🟡 Baja   | Routers           |
| 3   | No exponer mensajes de error internos en 500     | 🟠 Media  | `pipeline.py`     |

---

## Notas de Investigación

### Herramientas usadas

- Lectura directa de código fuente (backend, frontend, infra, tests, CI/CD, docs)
- Análisis de dependencias (requirements.txt, package.json, Docker images)
- Revisión de seguridad manual (OWASP Top 10 como referencia)
- Análisis de testing (cobertura, brechas, estrategia)

### Principios aplicados

- **Defense in depth**: no confiar en una sola capa de seguridad
- **Principle of least privilege**: non-root user, CORS mínimo, secretos rotados
- **Fail fast**: tests detectan problemas temprano
- **Documentation as code**: docs sincronizadas con el código real

### Enlaces

- [Auditoría principal (sesión datlas)](sesión subagent-chat-019e4807)
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Pip-audit](https://github.com/pypa/pip-audit)
