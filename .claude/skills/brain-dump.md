---
name: brain-dump
description: Procesá texto caótico de Facu y clasificalo en acciones concretas por fase
---

# Brain Dump — Procesador de ideas caóticas

Tomás todo lo que Facu escribió sin orden y lo convertís en estructura accionable.

## Cómo funciona

1. Leer TODO el texto sin interrumpir
2. Clasificar cada elemento en una de estas 4 categorías:
   - **ACCION** — algo concreto que se puede hacer ahora
   - **DECISION** — algo que requiere deliberar y elegir
   - **PROBLEMA** — algo que está roto o bloqueando
   - **IDEA FUTURA** — buena idea pero no es el momento
3. Asignar fase: **FASE 0** (ahora, antes del primer pago), **FASE 1** (cuando haya 1 pagador), **FASE 2** (escala)
4. Ordenar por impacto dentro de cada categoría

## Output obligatorio

```
=== ACCIONES FASE 0 (hacer ahora) ===
[ ] [accion concreta en 1 línea]
[ ] ...

=== ACCIONES FASE 1+ (cuando haya plata) ===
[ ] ...

=== IDEAS PARA DESPUÉS (no perder, no actuar) ===
- ...

=== DECISIONES PENDIENTES ===
- Qué: ...
  Opciones: A) ... B) ...
  Sugerencia: ...

=== PROBLEMAS DETECTADOS ===
- ...
```

## Regla de priorización

Las acciones Fase 0 se ordenan por:
1. ¿Bloquea directamente el primer pago? → arriba de todo
2. ¿El usuario lo nota si no está? → segundo
3. ¿Cuánto tiempo toma? → menos tiempo = más arriba si el impacto es igual

## Cómo usar

Escribí todo lo que tenés en la cabeza, sin orden, en uno o varios párrafos. Pegalo directo y dejá que el brain-dump lo procese.

Ejemplo de input válido:
"che necesito arreglar los scrapers pero también quiero agregar supabase y el tema de las cookies se venció creo, también pensé en hacer una versión mobile de la app, pero primero debería mandar los whatsapps del lote 1 que están listos desde hace días"

El skill hace el resto.
