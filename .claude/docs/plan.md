# Docs: Plan de ejecución

## Completado al 17/04/2026
- [x] Auditoría completa del proyecto
- [x] Bugs críticos de scrapers corregidos (MaxiCarrefour cookies renovadas 16/04)
- [x] .claude/ reorganizado (rules/ + docs/)
- [x] Maxiconsumo scraper reescrito (586 → 9,677 productos por categorías)
- [x] Yaguar multi-archivo (8 archivos combinados, 6,067 SKUs únicos)
- [x] Fuzzy EAN nativo en actualizar_catalogo.py (Paso 1b, Jaccard 0.60)
- [x] Frontend: 4 vistas cargando sin errores TypeScript
- [x] Vista Inicio: Top 20 bombas, 3 mayoristas primero, orden por ahorro %
- [x] Vista Comparar: ABC=A + 3 precios primero en cada sector
- [x] Catálogo: 16,825 productos, 3,018 con 2+ precios comparables

## Completado al 26/04/2026 (rediseño)
- [x] Rediseño completo frontend — 9 vistas, sistema de diseño completo
- [x] Deploy en Vercel (v0-brujula-de-precios.vercel.app)
- [x] Railway pipeline configurado (cron 6am UTC diario)
- [x] Catálogo 16,462 productos, actualizado 28/04

## Pendiente — Mayo 2026
- [ ] Primeros mensajes outreach enviados (WhatsApps listos en data/outreach/ desde 20/04)
- [ ] Feature gating FREE vs TIER2 (ver monetizacion.md)
- [ ] Persistencia localStorage (lista de compras se pierde al refrescar)
- [ ] Auth real con Supabase (activar cuando haya 1 usuario dispuesto a pagar)

## Próximo hito
**3-5 usuarios pagando.** Todo lo técnico está listo. El único paso que falta es outreach.

## Bloqueador real
**Ventas.** Sin ingresos el proyecto muere. Prioridad #1: enviar los WhatsApps del lote 1.
