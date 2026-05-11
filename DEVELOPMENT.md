# Development

## Comandos frecuentes

```bash
docker compose up --build          # Levantar API + DB + pgAdmin
docker compose logs api -f         # Ver logs de la API
docker compose down                # Parar todo
```

```bash
cd frontend
npm run dev                        # Servidor de desarrollo Astro → :4321
npm run build                      # Build estático para GitHub Pages
```

## Documentación

| Archivo | Propósito |
|---------|-----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitectura y decisiones técnicas |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |
| [docs/decisiones/](docs/decisiones/) | Decisiones de diseño (identidad visual, etc.) |

## API Debug

```bash
# Health check
curl http://localhost:8000/

# Swagger UI
# http://localhost:8000/docs
```

## Roadmap

- ✅ Perfil A — Limpieza
- ⬜ Perfil B — Exploración (distribuciones, correlaciones)
- ⬜ Perfil C — Pipeline + exportación
- ⬜ Deploy AWS
- ⬜ CI/CD
