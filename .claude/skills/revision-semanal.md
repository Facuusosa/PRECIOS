---
name: revision-semanal
description: Revisión semanal del estado técnico y comercial de Brújula de Precios con las 3 acciones prioritarias para la semana
---

# Revisión Semanal — Brújula de Precios

Diagnóstico completo del proyecto. Se corre idealmente cada lunes o cuando Facu pregunta "¿cómo vamos?".

## Proceso de revisión

### 1. Estado técnico
Verificar en este orden:
- Scrapers: ¿cuándo corrieron por última vez? ¿cuántos productos tienen? (Yaguar >3000, MaxiCarrefour >3000, Maxiconsumo >500)
- Catálogo: fecha de `catalogo_unificado.json` — ¿es reciente?
- Cookies MaxiCarrefour: ¿cuándo se renovaron por última vez? (expiran ~30 días)
- Deploy Vercel: ¿la app está online y sin errores?
- Pipeline local: ¿corrió la tarea automática de Windows? (ver logs en Task Scheduler)

### 2. Estado comercial
Reportar:
- ¿Cuántos comercios contactados en total?
- ¿Cuántos respondieron?
- ¿Cuántos están pagando? (goal: ≥1 para salir de Fase 0)
- Revenue ARS este mes: $...

### 3. Semáforo de salud

Usar este formato:
```
TECNICO:   🟢 Todo OK / 🟡 Hay algo que revisar / 🔴 Roto
COMERCIAL: 🟢 Hay movimiento / 🟡 Lento / 🔴 Sin contactos esta semana
RIESGO:    🟢 Ninguno / 🟡 Cookies próximas a vencer / 🔴 Bloqueador activo
```

## Output

```
=== REVISION SEMANAL — [fecha] ===

TECNICO: [semaforo]
- Scrapers: [estado]
- Catálogo: [fecha y cant. productos]
- Cookies Carrefour: [días desde renovación]
- Deploy: [OK / error]

COMERCIAL: [semaforo]
- Contactados: X | Respondieron: X | Pagando: X
- Revenue: $X ARS

TOP 3 ACCIONES ESTA SEMANA
1. [mínimo 2 comerciales, máximo 1 técnica]
2. ...
3. ...

BLOQUEADOR REAL: [qué es lo único que realmente importa ahora]
```

## Regla de las acciones semanales

- Mínimo 2 de las 3 acciones deben ser **comerciales** (contactar, seguir up, mejorar el pitch)
- Máximo 1 acción técnica por semana mientras estamos en Fase 0
- Si Facu propone 3 acciones técnicas → frenar y preguntar "¿cuántos WhatsApps mandaste esta semana?"

## Cómo usar

Escribí `/revision-semanal` y el skill hace la revisión automática leyendo los archivos del proyecto.
