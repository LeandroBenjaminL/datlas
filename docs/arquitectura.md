# Datlas — Arquitectura

> **Identidad**: Datlas = Datos + Atlas. El titán que carga datasets, los limpia, los explora, y los entrega transformados.
> 
> Frase: *"Tu dataset está roto, no sabés qué tiene, y necesitás resultados. Yo me encargo."*

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
- **Es lo que están pidiendo las empresas hoy** (junto con experiencia en cloud)

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
- Extensible (PostGIS para datos geoespaciales si algún día hace falta)
- pgAdmin incluido en Docker para desarrollo visual

---

### 4. Containerización: Docker

**Por qué Docker desde el día 0**:
- **Entorno idéntico en todas partes**: tu Windows, mi Linux, AWS, todo igual
- **Sin "en mi máquina funciona"**: el Dockerfile define exactamente qué versión de Python, qué dependencias
- **PostgreSQL sin instalación**: levanta con un comando, se destruye con otro
- **Prepara para AWS**: mismo Dockerfile se usa en ECS/Lambda container

---

### 5. Frontend: Astro (futuro)

| Alternativas | Por qué NO |
|-------------|------------|
| React/Next.js | Muy pesado para un portfolio de datos. 40KB+ de JS mínimo |
| Streamlit | Rápido para prototipos pero limitado en diseño y no es web real |
| SvelteKit | Buena opción, pero Astro es más liviano para contenido con islas interactivas |

**Por qué Astro**:
- 0KB de JavaScript por defecto — la página carga instantáneo
- Islas de interactividad: solo cargás JS donde realmente se necesita
- Markdown nativo para reportes
- Build a estáticos → deploy a GitHub Pages en 2 comandos
- Comunidad creciendo fuerte (40K+ estrellas en GitHub)

---

### 6. Cloud: AWS (Free Tier)

**Arquitectura objetivo**:

```
┌──────────────────────────────────────────────────────────┐
│  DESARROLLO LOCAL (Docker)                                │
│                                                           │
│  docker-compose up                                        │
│  ├── datlas-api (FastAPI + Pandas)                        │
│  ├── datlas-db (PostgreSQL 16)                            │
│  └── datlas-pgadmin (interfaz visual)                    │
│                                                           │
│  Todo en localhost, cero costo, iteración instantánea      │
└──────────────────────────────────────────────────────────┘
                          │
                          │ deploy
                          ▼
┌──────────────────────────────────────────────────────────┐
│  PRODUCCIÓN (AWS Free Tier)                               │
│                                                           │
│  GitHub Pages ────► Frontend Astro (estático)             │
│       │                                                   │
│       │ llamadas API                                      │
│       ▼                                                   │
│  API Gateway ────► Lambda (FastAPI via Mangum)            │
│       │                                                   │
│       │ persistencia                                      │
│       ▼                                                   │
│  RDS PostgreSQL (free tier 12 meses)                      │
│       │                                                   │
│       │ datasets                                          │
│       ▼                                                   │
│  S3 (almacenamiento de archivos)                          │
└──────────────────────────────────────────────────────────┘
```

---

### 7. Flujo de Datos (Pipeline Datlas)

Datlas implementa **los 3 perfiles combinados**:

```
            ┌─────────────────────┐
            │   USUARIO SUBE CSV  │
            └─────────┬───────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │  PERFIL A: LIMPIEZA  │
            │  • Detectar nulos    │
            │  • Outliers (IQR)    │
            │  • Duplicados        │
            │  • Normalizar tipos  │
            │  • Encoding           │
            └─────────┬───────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ PERFIL B: EXPLORAR  │
            │  • Profiling         │
            │  • Distribuciones    │
            │  • Correlaciones     │
            │  • Estadísticas      │
            │  • Gráficos          │
            └─────────┬───────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ PERFIL C: ENTREGAR  │
            │  • Dataset limpio    │
            │  • Reporte HTML/PDF  │
            │  • Datos en DB       │
            │  • API para frontend │
            └─────────────────────┘
```

---

## Estructura del Proyecto Datlas

```
data-analyst-ecosystem/
│
├── docker-compose.yml           ← Levanta todo: API + DB + pgAdmin
├── .env.example                 ← Variables de entorno para Datlas
│
├── backend/                     ← FastAPI: el cerebro de Datlas
│   ├── Dockerfile               ← Imagen Python 3.12 + dependencias
│   ├── requirements.txt         ← FastAPI, Pandas, SQLAlchemy, etc
│   └── app/
│       ├── main.py              ← Entry point: app FastAPI
│       ├── config.py            ← Settings desde .env
│       ├── routers/
│       │   ├── upload.py        ← POST /upload (subir dataset)
│       │   ├── clean.py         ← POST /clean (limpiar datos)
│       │   ├── explore.py       ← GET  /explore (perfil del dataset)
│       │   └── export.py        ← GET  /export (descargar resultados)
│       ├── services/
│       │   ├── cleaner.py       ← Perfil A: lógica de limpieza
│       │   ├── explorer.py      ← Perfil B: profiling y estadísticas
│       │   └── pipeline.py      ← Perfil C: orquestación del flujo
│       ├── db/
│       │   ├── models.py        ← SQLAlchemy: tablas PostgreSQL
│       │   ├── connection.py    ← Conexión a la DB
│       │   └── migrations/      ← Alembic (cuando haga falta)
│       └── utils/
│           ├── validators.py    ← Validación de archivos subidos
│           └── exporters.py     ← CSV, JSON, Parquet, Excel
│
├── data/                        ← Datasets (gitignored)
│   ├── raw/                     ← Datasets crudos subidos
│   └── processed/               ← Datasets limpios y transformados
│
└── docs/
    └── arquitectura.md          ← Este archivo
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

## Cómo Levantar el Proyecto

```bash
# 1. Clonar (si no está ya)
git clone https://github.com/LeandroBenjaminL/datlas.git
cd data-analyst-ecosystem

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env si querés cambiar passwords

# 3. Levantar todo con Docker
docker compose up --build

# 4. Acceder
# API:        http://localhost:8000
# API Docs:   http://localhost:8000/docs
# pgAdmin:    http://localhost:5050
# PostgreSQL: localhost:5432
```

---

## Próximos Pasos (Roadmap)

1. ✅ Docker + PostgreSQL + FastAPI esqueleto
2. ⬜ Implementar Perfil A (limpieza)
3. ⬜ Implementar Perfil B (exploración)
4. ⬜ Frontend Astro (GitHub Pages)
5. ⬜ Deploy a AWS Lambda + API Gateway
6. ⬜ CI/CD con GitHub Actions

---

## Principios de Diseño

- **Todo en Docker desde el día 0**: no se instala nada en la máquina host
- **Una decisión = una sección en este doc**: si cambiás algo, actualizás el porqué
- **Testeable por archivo**: cada módulo tiene `if __name__ == "__main__"` para pruebas rápidas
- **Nunca decidir sin mostrar alternativas**: el alumno elige, el profe muestra opciones
