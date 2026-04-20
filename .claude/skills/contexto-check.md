# Skill: /contexto-check
## Descripcion
Verifica el estado del contexto actual antes de una sesion larga. Muestra consumo de tokens por fuente, recomienda accion (compact/nueva sesion/continuar) y sugiere modelo optimo para la tarea que viene.

## Pasos

1. Correr `/context` y mostrar el breakdown completo de tokens por fuente
2. Calcular: esta la sesion a mas del 60%? mas del 75%?
3. Basado en el porcentaje, recomendar:
   - <40%: Continuar normalmente
   - 40-60%: Considerar /compact si la sesion va a ser larga
   - 60-75%: Hacer /compact ahora antes de continuar
   - >75%: Abrir nueva sesion (no esperar al 100% — la calidad se degrada)
4. Identificar que esta consumiendo mas tokens innecesariamente (documentacion grande, MCPs cargados que no se usan, memory.md muy extenso)
5. Preguntar: cual es la tarea que sigue? Recomendar modelo:
   - Busqueda simple / pregunta puntual -> usar Haiku
   - Desarrollo normal -> Sonnet (actual)
   - Arquitectura compleja / plan mode -> Opus
6. Reportar en formato limpio:
   ```
   CONTEXTO: [XX%] [VERDE/AMARILLO/ROJO]
   Accion recomendada: [continuar / /compact / nueva sesion]
   Mayor consumidor: [fuente]
   Modelo recomendado para proxima tarea: [Haiku/Sonnet/Opus]
   ```
