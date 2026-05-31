# Datlas — Makefile
# =============================================================================
# Comandos para desarrollo, testing y deploy de Datlas.
# =============================================================================

.PHONY: help up down setup test lint format clean build-docker

# --- Ayuda ---
help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Docker ---
up: ## Levantar todos los servicios (API + DB + pgAdmin)
	docker compose up -d

down: ## Bajar todos los servicios
	docker compose down

build: ## Build de las imágenes Docker
	docker compose build

restart: down up ## Reiniciar todos los servicios

logs: ## Ver logs de todos los servicios
	docker compose logs -f

# --- Setup ---
setup-backend: ## Instalar dependencias del backend (local, sin Docker)
	cd backend && pip install -r requirements.txt
	cd backend && pip install -e ".[dev]" 2>/dev/null || true

setup-frontend: ## Instalar dependencias del frontend
	cd frontend && npm install

setup: setup-backend setup-frontend ## Setup completo (backend + frontend)
	@echo "✅ Datlas listo para desarrollar"

# --- Testing ---
test: ## Correr tests del backend
	cd backend && python -m pytest tests/ -v --tb=short

test-cov: ## Tests con cobertura
	cd backend && python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

test-frontend: ## Build del frontend (verifica que compile)
	cd frontend && npm run build

# --- Linting ---
lint: lint-backend lint-frontend ## Lint completo

lint-backend: ## Lint del backend
	cd backend && ruff check app/ tests/
	cd backend && ruff format --check app/ tests/

lint-frontend: ## Lint del frontend
	cd frontend && npx astro check 2>/dev/null || echo "astro check no disponible"

format: ## Formatear código
	cd backend && ruff format app/ tests/

# --- Seguridad ---
security: ## Análisis de seguridad con Bandit
	cd backend && bandit -c .bandit -r app/

# --- Limpieza ---
clean: ## Limpiar archivos generados
	rm -rf backend/__pycache__ backend/app/__pycache__ backend/.pytest_cache
	rm -rf backend/.ruff_cache backend/.mypy_cache
	rm -rf frontend/dist frontend/.astro
	rm -rf data/processed/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# --- Servicios locales (sin Docker) ---
dev-backend: ## Iniciar backend en modo desarrollo
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend: ## Iniciar frontend en modo desarrollo
	cd frontend && npm run dev

# --- Docker build y push ---
docker-build: ## Build de imagen para producción
	docker build -t datlas-api backend/

docker-push: docker-build ## Push a registry (configurar REGISTRY primero)
	docker tag datlas-api $(REGISTRY)/datlas-api:latest
	docker push $(REGISTRY)/datlas-api:latest
