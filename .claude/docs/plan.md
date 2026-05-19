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

---

## Mapa de fases (reemplaza proxima-fase.md y monetizacion.md)

### FASE 0 → criterio de salida: 1 usuario pagando
No construir nada nuevo salvo vista-cuenta.tsx. Foco total en outreach.

### FASE 1 → criterio de salida: $50k ARS/mes
Supabase Auth → migrar localStorage → feature gating real → cobro manual primero → MercadoPago cuando >10 pagadores.

### FASE 2 → criterio de salida: $200k ARS/mes
Historial, mapa, alertas, Excel, automatización cobros.

---

## Tiers de precios (fuente: monetizacion.md — archivado)

| Tier | Precio | Features principales |
|---|---|---|
| FREE | $0 | 2 mayoristas (Yaguar + Maxiconsumo), hasta 10 guardados, sin login |
| TIER 2 | $6.999 ARS/mes | 3 mayoristas, listas ilimitadas, alertas, login real |
| TIER 3 | $14.999 ARS/mes | TIER2 + mapa, historial, reportes Excel, soporte prioritario |

**Análisis CFO:** necesitás 29 usuarios TIER2 (o 14 TIER3) para $200k/mes. Mix realista: 22 usuarios entre ambos tiers.

---

## Decisiones fijadas

| Decisión | Respuesta |
|---|---|
| Supabase | SÍ, cuando haya 1 pagador. Nunca antes. |
| Auth stack | Supabase Auth |
| Pagos | Manual primero → MercadoPago en ~10 pagadores |
| FREE vs TIER2 | FREE = Yaguar + Maxiconsumo. MaxiCarrefour en TIER2+ |
