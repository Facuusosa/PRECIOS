# Skill: /inicio-sesion
**Invocación:** `/inicio-sesion`
**Cuándo usar:** Al abrir el proyecto. Primera acción de cada sesión, sin excepción.
**Modelo:** Sonnet (necesita leer y razonar sobre el estado)

---

## Pasos

### 0. Leer ALERTA.md — SIEMPRE PRIMERO
Leer `data/quality/ALERTA.md`. Es donde el pipeline automático deja las alertas
(scraper caído, fuente congelada, verificación divergente, push bloqueado).
- Si hay entradas nuevas → reportarlas a Facu ANTES que cualquier otra cosa del briefing
- Después de que Facu las vea/resuelva → mover las entradas a la sección `## Resueltas` del mismo archivo
- Si no existe o está vacío → seguir sin mencionar nada

### 1. Leer ESTADO.md
Leer `ESTADO.md` en la raíz del proyecto. Extraer:
- Bloqueador principal
- Próximos 3 pasos
- Items en rojo (🔴) o advertencia (⚠️)

### 2. Leer MEMORY.md
Leer `~/.claude/projects/c--Users-Facun-OneDrive-Escritorio-PROYECTOS-PERSONALES-PRECIOS/memory/MEMORY.md`.
Extraer el contexto más reciente relevante para hoy.

### 3. Estado de cookies MaxiCarrefour
Ya NO se calcula por edad (la sesión PHP muere en horas, no en días — incidente 01/07/2026).
El wrapper `scrape_maxicarrefour.py` valida funcionalidad con un request real antes de cada
scrape y auto-renueva si están muertas. Si las cookies fallan de verdad, va a haber una
entrada en ALERTA.md (paso 0) — no hace falta chequeo manual acá.

### 4. Presentar briefing

Formato exacto (máximo 8 líneas, sin relleno):

```
Buenos días. Estado de Brújula al [fecha]:

[Si hay alertas nuevas en ALERTA.md]: 🔴 ALERTA: [resumen de cada una + acción sugerida]
Bloqueador: [extraído de ESTADO.md]
Propongo arrancar por: [el paso #1 de "Próximos 3 pasos"] — [razón en 1 línea]
[Si hay algo en rojo en ESTADO.md]: ⚠️ [el item rojo más urgente]

¿Arrancamos?
```

### 5. Esperar validación
No ejecutar nada hasta que Facu diga "sí", "arrancamos", o dé una instrucción concreta.
Si Facu dice otra cosa → seguir su dirección.

---

## Reglas del briefing
- Máximo 8 líneas — si hay más, resumir
- Siempre terminar con "¿Arrancamos?" o "¿Por dónde empezamos?"
- Nunca decir "Leí los archivos" — ir directo al estado
- Si hay alertas nuevas en ALERTA.md → mencionarlas PRIMERO, antes del bloqueador de producto
- Si el contexto ya está >60% al abrir → mencionar: "Contexto al X%. ¿/compact antes de arrancar?"
