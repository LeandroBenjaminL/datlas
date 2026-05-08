# Identidad Visual de Datlas

> Fecha: 2026-05-08
> Decisión: Leandro

---

## Resumen

Definición del look & feel de Datlas. Se prioriza un estilo **oscuro, tecnológico y profesional** que diferencie a Datlas de las herramientas corporativas genéricas.

---

## Decisiones

| Aspecto | Elección | Alternativas consideradas | Por qué |
|---------|----------|---------------------------|---------|
| **Paleta** | Oscuro violeta | Azul marino, claro minimalista, verde oscuro | Se destaca del azul corporativo genérico, transmite tecnología y creatividad |
| **Tipografía** | Inter (Google Fonts) | System UI, JetBrains Mono | Inter es moderna, profesional, usada por GitHub y Figma. Carga rápida desde Google Fonts |
| **Logo** | Texto: "⚡ Datlas" | Logo ilustrado, icono personalizado | Por ahora texto. Simple, efectivo. Se puede iterar después |

---

## Paleta de colores

| Uso | Color | Hex | CSS Variable |
|-----|-------|-----|-------------|
| Fondo principal | Negro suave | `#0a0a12` | `--bg-primary` |
| Fondo tarjetas | Violeta muy oscuro | `#12122a` | `--bg-card` |
| Bordes | Violeta tenue | `#1e1e3a` | `--border` |
| Texto principal | Blanco suave | `#e2e2f0` | `--text-primary` |
| Texto secundario | Gris azulado | `#94a3b8` | `--text-secondary` |
| Texto footer | Gris oscuro | `#4a4a6a` | `--text-muted` |
| Acento principal | Violeta medio | `#a78bfa` | `--accent` |
| Acento hover | Violeta más intenso | `#c4b5fd` | `--accent-hover` |
| Gradient header | Violeta → Azul → Negro | `linear-gradient(135deg, #1a1040, #0d1b3e, #0a0a12)` | — |

---

## Tipografía

| Propiedad | Valor |
|-----------|-------|
| Fuente principal | `Inter`, system-ui, sans-serif |
| Carga | Google Fonts (CDN) |
| Tamaño base | 18px |
| Header (logo) | 1.6rem, 800 weight |
| Títulos (hero) | 3.5rem, 900 weight |

---

## Componentes visuales

| Componente | Estilo |
|------------|--------|
| Header | Gradiente violeta-azul-negro, borde inferior sutil |
| Footer | Texto gris oscuro centrado, borde superior tenue |
| Tarjetas | Fondo violeta oscuro, borde 1px, hover con elevación sutil |
| Botón primario | Fondo violeta (`#7c3aed`), hover más oscuro |
| Botón outline | Borde gris, hover violeta |
| Badges | Fondo violeta traslúcido, borde violeta suave |

---

## Mockup visual (textual)

```
┌──────────────────────────────────────────────────┐
│  ⚡ Datlas.io    Inicio  Subir  Limpiar  Explorar │
│  ───── (border violeta tenue) ──────────────── │
├──────────────────────────────────────────────────┤
│                                                  │
│                    DATLAS                         │
│   Cargá tu dataset, limpiá los datos, explorá    │
│   patrones y exportá resultados.                 │
│   ┌──────────┐  ┌──────────┐                     │
│   │ Empezar  │  │  GitHub  │                     │
│   └──────────┘  └──────────┘                     │
│                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│   │ 🧹Limpieza│  │🔍Explorar│  │⚡Pipeline│      │
│   │ ...      │  │ ...     │  │ ...     │      │
│   └──────────┘  └──────────┘  └──────────┘      │
│                                                  │
│   Python FastAPI Pandas PostgreSQL Docker AWS    │
├──────────────────────────────────────────────────┤
│  Datlas · GitHub · Arquitectura profesional 2026 │
└──────────────────────────────────────────────────┘
```

---

## Próximos pasos visuales

- ⬜ Favicon personalizado
- ⬜ Logo ilustrado (opcional)
- ⬜ Modo claro (opcional, futuro)
