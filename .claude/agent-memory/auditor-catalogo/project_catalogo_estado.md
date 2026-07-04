---
name: project_catalogo_estado
description: Estado del catalogo unificado al 27/05/2026 — metricas, cobertura, tasa de matching, veredicto de salud
metadata:
  type: project
---

Estado auditado: 28/05/2026

Total productos: 18.186 (+94 vs auditoria anterior 27/05)
Con 2+ precios comparables: 2.946 (16.2%)
Precios fuera de rango (<$300 o >$300.000): 146
Productos con precio_stale marcado: 1 (subrepresentado -- logica de stale parcialmente activa)
Registros en auditoria_matches.json: 46 (criticos activos)

Patrones criticos confirmados en esta auditoria:
- Yaguar precio >100.000 en catalogo activo: 2 productos (KIT VILEDA $109.999, PANTENE sachet $192.000)
- MC precios <$300 con otra fuente >$500: solo 2 productos (NUGATON obleas) -- mejoro vs anterior
- MC precios de pack/caja (>10x Yaguar): 40 productos, top caso TULIPAN Dispenser 12x3u MC=$21.500 vs Y=$2.012 (10.7x)
- Productos MC precio <$200 con ratio >10x en auditoria: 24 casos -- patron precio-parcial confirmado

Duplicados detectados: 4 productos (2 pares de Guantes TASK Grande/Mediano)
- EAN distintos matchearon al mismo nombre_display
- Cada par tiene fuentes distintas: un id tiene Yaguar, el otro tiene Maxiconsumo
- Impacto: el comerciante ve dos entradas del mismo guante con precios diferentes

**Why:** Auditoria corrida el 28/05 post-deploy fix precios MC.
**How to apply:** Baseline actualizado. Alertas: si precios fuera de rango superan 200, o Yaguar >100k supera 5 productos, o duplicados superan 10 -- revisar pipeline antes de mostrar al usuario.
