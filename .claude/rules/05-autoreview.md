# Regla: Auto-review antes de declarar terminado

## El problema que esto resuelve
Claude presenta algo como "listo" → usuario lo acepta → Claude dice "podría mejorarse".
Eso es una falla, no una feature. Destruye confianza y malgasta tiempo.

## El bucle obligatorio

Correr SIEMPRE antes de ExitPlanMode, antes de escribir "terminé", antes de escribir "listo":

1. **¿Hay herramientas disponibles que no usé?** (agentes, skills, MCPs)
   → Si hay una skill que hace esto → usarla
   → Si hay un agente disponible → invocarlo o incluirlo en el plan

2. **¿Hay duplicación?** (código, secciones del plan, pasos repetidos)
   → Consolidar antes de presentar

3. **¿Los pasos tienen especificidad suficiente?** (rutas exactas, líneas, ejemplos de código)
   → Si no → agregarlos

4. **¿Hay criterio de verificación para cada paso?**
   → Si no → agregar "cómo saber que funcionó"

5. **¿Modelo correcto para cada tarea?**
   → Tarea mecánica / reporte a archivo → Haiku
   → Análisis, diseño, arquitectura → Sonnet
   → Si el plan no especifica modelo → especificarlo

6. **¿Qué señalaría un revisor senior (PM / ingeniero / diseñador UX)?**
   → Responder eso internamente, aplicarlo, no mencionarlo externamente

Solo después de pasar los 6 criterios → declarar terminado.

## Regla complementaria: NUNCA después de presentar

Si se puede mejorar → mejorarlo ANTES de presentar.
"Podría mejorarse si..." después de presentar = error de proceso.
Cuando esto ocurra → agregar lo que faltó a este checklist.

## Aplica a

- Planes (antes de ExitPlanMode)
- Código (antes de decir "listo")
- Respuestas largas (antes de enviar)
- Propuestas de arquitectura (antes de recomendar)
