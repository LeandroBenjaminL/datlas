---
name: datlas-workflow
description: "Flujo de trabajo de Datlas — de CSV sucio a dataset limpio vía API."
license: MIT
metadata:
  author: Leandro Benjamin L.
  version: "1.0"
---

# Datlas — Workflow

## Árbol de decisión

```
¿Qué necesitás?
│
├── Subir un dataset
│   └── → POST /api/upload
│
├── Limpiar datos (nulos, outliers, duplicados, tipos)
│   └── → POST /api/clean
│
├── Explorar / profilear
│   └── → GET /api/explore
│
├── Exportar resultados
│   └── → GET /api/export
│
├── Tarea transversal
│   ├── commits           → skill commits-real
│   ├── documentación     → skill commits-real
│   ├── tests             → preguntarme
│   └── engram, memoria   → guardar después de cada cambio
│
└── No sabés
    └── → Preguntame, analizamos juntos
```

## Flujo senior

```
1. LEER
   ├── Escuchar la solicitud
   ├── Consultar Engram (contexto previo?)
   └── Si es vago → preguntar hasta entender

2. ANALIZAR
   ├── Pensar 2+ enfoques posibles
   └── Identificar pros/contras

3. PREGUNTAR
   ├── Mostrar alternativas
   └── Explicar tradeoffs

4. DECIDIR JUNTOS
   ├── Elegir el mejor enfoque
   └── Cargar skills necesarias

5. RESOLVER
   ├── Implementar paso a paso
   ├── Testear cada paso antes de avanzar
   └── Tests > docs > commit

6. ENGRAM
   ├── Guardar decisiones de arquitectura
   ├── Guardar bugs y fixes
   └── Guardar resumen de sesión
```

## Reglas de oro

- **Enseñar siempre**: cada interacción = algo nuevo aprendido
- **Docker todo**: no instalar nada en la máquina host
- **API-first**: la interfaz de Datlas es REST, después viene el frontend
- **Preguntar antes de decidir**: nunca imponer una solución
