# Reglas: Proyecto y MVP

## Qué es Brújula
App web que centraliza precios de mayoristas (compra) y cadenas minoristas (góndola) con
calculador de margen automático. Sirve a dos audiencias: comerciantes (kioscos, almacenes,
minimercados) que comparan precio de compra, y consumidores que comparan precio de góndola.
El selector "Uso la app como" (perfil) define cuál ve primero cada uno.

## MVP — incluye (rediseño completo 26/04/2026)
- Calculador de margen funcional
- 4 mayoristas: Yaguar, Maxicarrefour, Maxiconsumo, Nini (sumado 29/07/2026, cuenta prestada — ver `.claude/rules/02-scrapers.md`) + 5 cadenas: Coto, Carrefour, Dia, Masonline, Jumbo (sumadas 20/07/2026)
- 6 vistas: Inicio ("Para Ti"), Catálogo, Detalle, Mi Lista (id interno `herramientas`),
  Perfil, Planes (verificado en `bottom-nav.tsx` y `app/page.tsx` 29/07/2026 — "Comparativa"
  NO es una vista propia: es `onVerComparativa` en `vista-detalle.tsx`, un handler vacío
  `() => {}` sin implementar, no confundir con una feature que funciona)

## MVP — NO incluye
- FEATURE GATING real (FREE/PRO): hoy TODAS las fuentes están abiertas para todos, sin
  restricción de código. No hay lógica de tier en `lib/`. Ver `.claude/docs/proxima-fase.md`
  para el plan de implementación — hasta que se implemente, no mostrar en UI ningún badge
  "PRO" ni mensaje de plan que sugiera una restricción que no existe (confirmado 13/07/2026,
  ver `vista-cuenta.tsx`).
- Mapa/direcciones (Tier3)
- Historial de precios (Tier2)
- Alertas (post-estabilización)
- BD real (MVP: localStorage)
- Auth real (MVP: dummy)

## Señales de desvío — frenar siempre
- "Agregar IA predictiva" → Tier3, después de v1
- "App móvil nativa" → web responsive es suficiente
- "Agregar más mayoristas ahora" → primero estabilizar 3
- "Perfeccionar scrapers" → si funciona, next. Solo tocar si falla más de 2 veces por semana

## Guardrails
- Si scraper falla → log, skip, continuar con los que quedan
- Si mayorista bloquea → usar datos cacheados + avisar "datos desactualizados"
- Si algo toma >4 horas → probablemente overkill
- Funcional > perfecto. Lanzar imperfecto > esperar perfecto.
