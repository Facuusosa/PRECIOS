# BRÚJULA DE PRECIOS — Claude Context

**App:** Comparador de precios mayoristas para comerciantes de Buenos Aires.  
**Stack:** Next.js 16 + Python scrapers + JSON catalog.  
**Estado:** Rediseño completo 26/04/2026. En lanzamiento. Bloqueador real: ventas.

## Fuentes activas
- Yaguar (`targets/yaguar/scraper_pro.py`) — mayorista
- MaxiCarrefour (`targets/maxicarrefour/scraper_pro.py`) — mayorista; cookies en `.env`, mueren en horas por inactividad (no en 30 días), renovación automática — ver `.claude/rules/02-scrapers.md`
- Maxiconsumo (`targets/maxiconsumo/scraper_pro.py`) — mayorista
- Nini (`targets/nini/scraper_pro.py`) — mayorista; cuenta PRESTADA por un tercero, scraper de SOLO LECTURA (whitelist duro de métodos, nunca confirma/anula pedidos) — ver `.claude/rules/02-scrapers.md`
- Coto (`targets/coto/scraper_pro.py`) — CADENA minorista (referencia góndola, no precio de compra); API pública Constructor.io, sin credenciales
- Carrefour retail (`targets/carrefour/scraper_pro.py`) — CADENA minorista; API VTEX Intelligent Search pública, sin credenciales. NO confundir con MaxiCarrefour (mayorista B2B, otro sitio)
- Dia (`targets/dia/scraper_pro.py`) — CADENA minorista; API VTEX legacy Catalog System pública, sin credenciales, sin anti-bot
- Masonline (`targets/masonline/scraper_pro.py`) — CADENA minorista; API VTEX legacy Catalog System pública, sin credenciales, sin anti-bot
- Jumbo (`targets/jumbo/scraper_pro.py`) — CADENA minorista (Cencosud); API VTEX Intelligent Search pública, sin credenciales. ListPrice viene roto (no se usa como precio regular, ver docstring del scraper)

## Entrypoints clave
- Frontend: `BRUJULA-DE-PRECIOS/app/page.tsx`
- Data: `BRUJULA-DE-PRECIOS/lib/data.ts`
- Catálogo: `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
- Unificador: `actualizar_catalogo.py`
- Config: `.env`

## Instrucciones detalladas
- Reglas del proyecto → `.claude/rules/`
- Arquitectura, tiers, operaciones → `.claude/docs/`
- Gestión de contexto y tokens → `.claude/rules/03-contexto.md`

## Skills disponibles (/nombre)
`/inicio-sesion` `/contexto-check` `/status-proyecto` `/bucle-optimizador` `/disenar-pantalla` `/auditoria-seguridad`
`/pipeline-datos` `/verificar-precios` `/actualizar-familias` `/cerrar-sesion` `/railway-deploy`
`/investigar-y-contactar` `/buscar-comercios` `/enviar-outreach` `/verificar-app` `/pre-launch-check`
`/brain-dump` `/revision-semanal` `/buscar-x`

Skills nativas de marketing/ventas (agregadas 29/07/2026, para el bloqueador real: ventas):
- `prospecting` — encontrar y calificar comercios objetivo para outreach
- `cold-email` — escribir mensajes fríos y secuencias de seguimiento que consiguen respuesta
- `copywriting` / `copy-editing` — escribir o mejorar copy de marketing (landing, mensajes, redes)
- `product-marketing` — documento de posicionamiento e ICP (`.agents/product-marketing.md`)
- `launch` — checklist de lanzamiento/anuncio cuando haya feature lista para anunciar
- `analytics` — setup de tracking/medición (usar recién cuando haya tráfico real que medir)

## Agentes disponibles
Invocar: "Actua como el agente definido en `.claude/agents/[nombre].md`"
- `auditor.md` — auditoría completa del proyecto (calidad, seguridad, deuda técnica)
- `auditor-catalogo.md` — auditoría específica del catálogo de precios
- `qa-verificador.md` — QA de la app en producción, escribe reporte a archivo sin contaminar contexto
- `pm-implacable.md` — evalúa ideas: ¿acerca al primer pagador? → CONSTRUIR/ENCOLAR/DESCARTAR
- `diseñador-ux.md` — UX/UI senior mobile comercial, screenshot loop
- `experto-seguridad.md` — auditoría de seguridad pre-release, específica del dominio Brújula
- `limpiador.md` — limpieza de archivos huérfanos y temporales
- `security-ai-generated-code-auditor.md` — auditor de seguridad para código vibe-coded (secretos
  hardcodeados, RLS roto, prompt injection); complementa a `experto-seguridad.md`, no lo reemplaza
- `sales-outbound-strategist.md` — diseña secuencias de prospección multicanal y define ICP
- `sales-outreach.md` — outreach consultivo: prospección fría, seguimiento, manejo de objeciones
- `sales-discovery-coach.md` — coachea preguntas de descubrimiento para calls de venta
- `sales-offer-lead-gen-strategist.md` — diseña oferta y lead magnets para atraer compradores
  (agentes de sales son genéricos B2B SaaS — adaptar al perfil real de Brújula: comercios de
  barrio, ciclo corto, ticket bajo, no asumir el ICP corporativo que traen por default)

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
