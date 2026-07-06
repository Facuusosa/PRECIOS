# BRÚJULA DE PRECIOS — Claude Context

**App:** Comparador de precios mayoristas para comerciantes de Buenos Aires.  
**Stack:** Next.js 16 + Python scrapers + JSON catalog.  
**Estado:** Rediseño completo 26/04/2026. En lanzamiento. Bloqueador real: ventas.

## Fuentes activas
- Yaguar (`targets/yaguar/scraper_pro.py`) — mayorista
- MaxiCarrefour (`targets/maxicarrefour/scraper_pro.py`) — mayorista; cookies en `.env`, renovar cada ~30 días
- Maxiconsumo (`targets/maxiconsumo/scraper_pro.py`) — mayorista
- Coto (`targets/coto/scraper_pro.py`) — CADENA minorista (referencia góndola, no precio de compra); API pública Constructor.io, sin credenciales
- Carrefour retail (`targets/carrefour/scraper_pro.py`) — CADENA minorista; API VTEX Intelligent Search pública, sin credenciales. NO confundir con MaxiCarrefour (mayorista B2B, otro sitio)

## Entrypoints clave
- Frontend: `BRUJULA-DE-PRECIOS/app/page.tsx`
- Data: `BRUJULA-DE-PRECIOS/lib/data.ts`
- Catálogo: `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
- Unificador: `actualizar_catalogo.py`
- Config: `config.py` + `.env`

## Instrucciones detalladas
- Reglas del proyecto → `.claude/rules/`
- Arquitectura, tiers, operaciones → `.claude/docs/`
- Gestión de contexto y tokens → `.claude/rules/03-contexto.md`

## Skills disponibles (/nombre)
`/inicio-sesion` `/contexto-check` `/status-proyecto` `/bucle-optimizador` `/disenar-pantalla` `/auditoria-seguridad`
`/pipeline-datos` `/verificar-precios` `/actualizar-familias` `/cerrar-sesion` `/railway-deploy`
`/investigar-y-contactar` `/buscar-comercios` `/enviar-outreach` `/verificar-app` `/pre-launch-check`
`/brain-dump` `/revision-semanal` `/buscar-x`

## Agentes disponibles
Invocar: "Actua como el agente definido en `.claude/agents/[nombre].md`"
- `auditor.md` — auditoría completa del proyecto (calidad, seguridad, deuda técnica)
- `auditor-catalogo.md` — auditoría específica del catálogo de precios
- `qa-verificador.md` — QA de la app en producción, escribe reporte a archivo sin contaminar contexto
- `pm-implacable.md` — evalúa ideas: ¿acerca al primer pagador? → CONSTRUIR/ENCOLAR/DESCARTAR
- `diseñador-ux.md` — UX/UI senior mobile comercial, screenshot loop
- `experto-seguridad.md` — auditoría de seguridad pre-release
- `limpiador.md` — limpieza de archivos huérfanos y temporales

## Próxima fase (cuando haya tracción)
Ver `.claude/docs/proxima-fase.md` — auth, Railway cron, pagos, vistas de login y tiers.
Railway plan Hobby ($5/mes) ya contratado — usar para scrapers automáticos en la nube.

---

## Comportamiento, proactividad y orquestación
Todo el comportamiento general (ritual de sesión, triggers proactivos, selección de modelo,
orquestación por tipo de tarea, protocolo adversarial) NO se repite acá. Vive en su hogar canónico:
- `~/.claude/CLAUDE.md` (global) — identidad, comportamiento proactivo, selección de modelo, ritual
- `.claude/rules/06-jarvis-razonamiento.md` — orquestación por tipo de tarea + protocolo adversarial
- `.claude/rules/04-protocolo.md` — protocolo de trabajo, worktrees, cierre de sesión

Este archivo es SOLO el contexto específico de Brújula (stack, mayoristas, entrypoints, herramientas).

## Reglas por dominio — LEER antes de tocar (carga bajo demanda)
No se cargan siempre para no inflar el contexto. Antes de trabajar en cada dominio, leer:
- **Frontend / UI** → `.claude/docs/frontend/react.md` + `.claude/docs/frontend/styles.md`
