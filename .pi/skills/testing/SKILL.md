# Testing Skill — Datlas

## Filosofía

> Los tests no están para comprobar que el código funciona (el "camino feliz"),
> sino para ser una **malla de seguridad** que detecta regresiones y reduce
> incertidumbre ante cambios futuros.

Principios operativos:

1. **Testeá los errores primero.** El camino feliz es fácil; los edge cases
   (CSV vacío, nulls, encodings rotos, datos inconsistentes) son los que rompen
   en producción.

2. **Aserts concretos > aserts de estructura.** `assert "key" in dict` no
   protege nada. `assert result["rows"] == 10` sí.

3. **Integración real > unitarios con mocks.** Testear contra servicios reales
   (httpx contra la app, tmp_path con archivos reales) da más confianza que
   mockear todo. En datlas ya lo hacemos: los tests usan `httpx.ASGITransport`
   sin mocks.

4. **Coverage no es el objetivo.** 100% de líneas cubiertas con asserts débiles
   es peor que 70% con asserts significativos. Un test de `test_upload_rejects_non_csv`
   protege más que 10 tests de camino feliz.

## Tipos de tests en datlas

### Unitarios (test_cleaner.py, test_explorer.py)
Testean una clase aislada con datos controlados vía `tmp_path`.
- **Cuándo**: lógica de negocio pura (detección de outliers, nulos, estadísticas)
- **Fixture**: `tmp_path` para CSVs temporales, `test_csv_path` para el fixture base
- **Regla**: nunca mockeen pandas; usen datos reales sintéticos

### Integración (test_integration.py)
Testean la API HTTP completa con `httpx.ASGITransport`.
- **Cuándo**: endpoints, flujo completo upload→clean→explore, manejo de errores HTTP
- **Fixture**: `client` (AsyncClient contra la app real)
- **Regla**: cubrir al menos un caso de error por endpoint (404, 400, etc.)

### Pipeline (test_pipeline.py)
Testean la orquestación completa sin levantar el server.
- **Cuándo**: flujo upload→clean→explore integrado
- **Fixture**: `pipeline` (PipelineService con tmp_path)
- **Regla**: verificar que el archivo limpio existe Y tiene contenido correcto

### Property-based (test_hypothesis.py)
Testean con datos aleatorios generados por hypothesis.
- **Cuándo**: propiedades invariantes ("analyze() nunca crashea", "clean() preserva tipos")
- **Regla**: mantener max_examples ≤ 20 para no ralentizar CI

## Edge case checklist

Antes de dar por terminado un feature, verificá que existan tests para:

| Categoría | Casos |
|---|---|
| **Datos vacíos** | CSV sin filas, columna sin datos, todo nulos |
| **Tamaños extremos** | 1 sola fila, 1 sola columna, 100k filas |
| **Tipos mezclados** | Números en columna string, strings en columna numérica |
| **Encoding** | Latin-1, UTF-8 BOM, Windows-1252 |
| **Formato** | CSV malformado (columnas inconsistentes), binario, JSON por error |
| **Valores límite** | IQR = 0 (todos iguales), sin outliers, sin duplicados |
| **API errors** | 404 (no existe), 400 (input inválido), 500 (error interno) |
| **Concurrencia** | Dos uploads simultáneos, pipeline corriendo dos veces |

## Comandos

```bash
# Todos los tests
cd backend && python -m pytest tests/ -v --tb=short

# Con coverage
cd backend && python -m pytest tests/ -v --tb=short --cov=app/ --cov-report=term-missing

# Solo un archivo
cd backend && python -m pytest tests/test_cleaner.py -v

# Solo tests de error
cd backend && python -m pytest tests/ -v -k "error or edge or empty or binary or latin"

# Hypothesis (property-based)
cd backend && python -m pytest tests/test_hypothesis.py -v
```

## Anti-patrones a evitar

```python
# ❌ MAL: assert estructural sin validar valor
assert "nulls" in report

# ✅ BIEN: verificá el valor concreto
assert report["nulls"]["edad"]["null_count"] == 2

# ❌ MAL: solo camino feliz
def test_upload(client):
    r = await client.post("/api/upload", ...)
    assert r.status_code == 200

# ✅ BIEN: cubrí también el error
def test_upload_rejects_non_csv(client):
    r = await client.post("/api/upload", files={"file": ("bad.txt", b"...", "text/plain")})
    assert r.status_code == 400
```

## Cuando agregar un test nuevo

Regla de decisión rápida:

```
¿El cambio toca lógica de negocio?     → test unitario
¿El cambio toca un endpoint?           → test de integración (feliz + error)
¿El cambio toca el pipeline completo?  → test de pipeline
¿El cambio podría romperse con datos raros? → test property-based
```
