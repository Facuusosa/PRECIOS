# BRÚJULA DE PRECIOS — Claude Context

**App:** Comparador de precios mayoristas para comerciantes de Buenos Aires.  
**Stack:** Next.js 16 + Python scrapers + JSON catalog.  
**Estado:** Rediseño completo 26/04/2026. En lanzamiento. Bloqueador real: ventas.

## Mayoristas activos
- Yaguar (`targets/yaguar/scraper_pro.py`)
- MaxiCarrefour (`targets/maxicarrefour/scraper_pro.py`) — cookies en `.env`, renovar cada ~30 días
- Maxiconsumo (`targets/maxiconsumo/scraper_pro.py`)

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
`/contexto-check` `/status-proyecto` `/bucle-optimizador` `/disenar-pantalla` `/auditoria-seguridad`
`/pipeline-datos` `/verificar-precios` `/actualizar-familias` `/cerrar-sesion` `/railway-deploy`
`/investigar-y-contactar` `/buscar-comercios` `/enviar-outreach` `/verificar-app` `/pre-launch-check`

## Agentes disponibles
Invocar: "Actua como el agente definido en `.claude/agents/[nombre].md`"
- `auditor.md` — auditoría completa del proyecto (calidad, seguridad, deuda técnica)
- `auditor-catalogo.md` — auditoría específica del catálogo de precios
- `qa-verificador.md` — QA de la app en producción, escribe reporte a archivo sin contaminar contexto

## Próxima fase (cuando haya tracción)
Ver `.claude/docs/proxima-fase.md` — auth, Railway cron, pagos, vistas de login y tiers.
Railway plan Hobby ($5/mes) ya contratado — usar para scrapers automáticos en la nube.
