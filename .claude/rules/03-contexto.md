# Rules: Gestión de Contexto y Tokens

## La statusline de Claude Code (barra inferior del terminal)
Muestra en tiempo real:
- **Tokens usados** en la query actual
- **% de contexto** (0-100% de la ventana disponible)
- **Duración** de la query en segundos

Leerla antes de cada sesión larga. Si está >60%, hacer /compact antes de empezar.

## Cuándo usar cada comando

| Situación | Comando |
|---|---|
| Antes de sesión larga | `/context` — ver breakdown por fuente |
| Contexto >60% o sesión >45 min | `/compact` — comprime historial |
| Contexto >75% | Abrir nueva sesión. No esperar al 100%. |
| Al volver de una sesión larga | `/context` para verificar qué retuvo |

## Cuándo usar cada modelo

| Tarea | Modelo |
|---|---|
| Búsquedas simples, preguntas de 1 línea | Haiku (más barato) |
| Desarrollo normal, análisis, todo lo regular | Sonnet (este) |
| Plan mode en decisiones arquitecturales complejas | Opus |

## Lo que consume más tokens (en orden)
1. Herramientas del sistema (~17k tokens fijos — no controlable)
2. CLAUDE.md global + local
3. MCPs instalados (Chrome DevTools > Puppeteer)
4. memory.md
5. Skills cargadas
6. Tu mensaje actual

No meter documentación completa de APIs en CLAUDE.md. Solo lo que se usa activamente.

## Comprimir prompts de voz
Si el prompt de voz es muy largo:
1. Hablar → transcribir con Haiku → pegar resumen en Sonnet
2. Ahorra tokens en el contexto principal sin perder información

## Sesgo de primacía/actualidad
Claude recuerda bien el inicio y el final de la conversación, casi nada del medio.
Poner guardarrails importantes SIEMPRE primero en el prompt.

## Subagentes y tokens
Subagentes consumen ~7x tokens vs agente único. Usarlos solo cuando:
- Hay tareas paralelizables reales
- El resultado contaminaría el contexto principal
- El subagente puede escribir a archivo en lugar de devolver texto masivo
