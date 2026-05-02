# Reglas: Proyecto y MVP

## Qué es Brújula
App web para comerciantes (kioscos, almacenes, minimercados) que centraliza precios de 3 mayoristas con calculador de margen automático.

## MVP — incluye (rediseño completo 26/04/2026)
- Calculador de margen funcional
- 3 mayoristas: Yaguar, Maxicarrefour, Maxiconsumo
- 6 vistas: Inicio, Catálogo, Detalle, Comparativa, Herramientas, Perfil
- FEATURE GATING: FREE = 2 mayoristas, TIER2+ = 3

## MVP — NO incluye
- Mapa/direcciones (Tier3)
- Historial de precios (Tier2)
- Alertas (post-estabilización)
- BD real (MVP: localStorage)
- Auth real (MVP: dummy)

## Señales de desvío — frenar siempre
- "Agregar IA predictiva" → Tier3, después de v1
- "App móvil nativa" → web responsive es suficiente
- "Agregar más mayoristas ahora" → primero estabilizar 3
- "Perfeccionar scrapers" → si funciona, next. Solo tocar si >2 crashes/día

## Guardrails
- Si scraper falla → log, skip, continuar con los que quedan
- Si mayorista bloquea → usar datos cacheados + avisar "datos desactualizados"
- Si algo toma >4 horas → probablemente overkill
- Funcional > perfecto. Lanzar imperfecto > esperar perfecto.
