# Reglas: Protocolo de trabajo

## Bucle verificador
Ver `testing.md` — aplica a TODA tarea, no solo código ni scrapers.

## Cuando Claude repite el mismo error → agregar regla YA
Si el mismo error ocurre dos veces, crear/actualizar la regla en `.claude/rules/` antes de continuar.
No esperar al final de la sesión. Regla nueva = problema resuelto para siempre.

## Actualizar al final de sesiones importantes
Correr `/cerrar-sesion` — el skill hace todo el proceso.

Manual si no está disponible:
1. Regla permanente → `.claude/rules/` o `.claude/docs/`
2. Estado operativo → memoria en `~/.claude/projects/.../memory/`
3. Guardar decisiones y el por qué — lo que NO está en el código ni en git
4. Podar reglas viejas — los rules/ son código vivo, no un archivo histórico

## Buscar en X antes de disenar
Antes de implementar cualquier animacion nueva o componente UI, correr `/buscar-x [tema]`.
Objetivo: encontrar la tecnica mas actual en 5 minutos o menos antes de construir desde cero.
Si no se encuentra nada mejor en 3 queries → continuar con el plan sin bloquearse.

## Auditoría profunda
Correr el agente `auditor` cuando hay dudas de calidad o antes de release:
"Actúa como el agente definido en `.claude/agents/auditor.md` y auditá el proyecto completo"

## Gestión de contexto
Ver reglas completas en `03-contexto.md`.
Resumen: /context para ver consumo, /compact si >60%, nueva sesión si >75%.

## Git Worktrees — features paralelas
Cuando hay 2 features independientes (ej: auth + scraper simultáneamente):
```bash
git worktree add ../brujula-auth feature/auth
git worktree add ../brujula-scraper feature/scraper
```
Dos terminales con Claude Code separados → sin conflictos.
Al terminar: `git worktree remove ../brujula-auth` y merge a main.
Señal de cuando usar worktrees: tarea A y tarea B no tocan los mismos archivos.

## Múltiples pestañas — reglas
- Máximo 3-4 pestañas simultáneas activas
- Si Claude lleva >10-15 min sin hacer nada en una pestaña → demasiadas abiertas
- El hook de beep identifica cuál pestaña terminó (distintas frecuencias por sesión)
- Cada pestaña debe tener una tarea clara antes de abrirla

## Workflow de voz (3x más rápido que escribir)
Cuando el prompt es largo o complejo, usar voz en lugar de escribir:
1. Activar dictado (Windows: Win+H | Mac: Fn doble)
2. Hablar todo lo que querés pedirle a Claude — sin preocuparse por la redacción
3. Pegar el texto crudo en Claude
4. Claude procesa aunque esté desordenado

Para prompts muy largos que van a consumir muchos tokens:
1. Hablar → pegar texto en una sesión con **Haiku** (modelo barato)
2. Pedirle: "Resumí esto en un prompt conciso y claro para Sonnet"
3. Copiar el resumen → pegar en la sesión principal con Sonnet
Esto ahorra tokens sin perder información.

## Mantenimiento automático de HERRAMIENTAS.md

Cada vez que se crea o modifica una skill en `.claude/skills/` o un agente en `.claude/agents/`, actualizar `HERRAMIENTAS.md` en la raíz del proyecto **sin que Facu tenga que pedirlo**.

HERRAMIENTAS.md es la referencia de Facu para entender qué herramientas tiene. Debe estar siempre al día.

## Cuándo invocar el agente de seguridad

Invocar `experto-seguridad` antes de:
- Cada release importante o deploy
- Agregar credenciales nuevas al proyecto
- Modificar `.env` o `config.py`
- Una vez por mes como auditoría preventiva

"Actúa como el agente definido en `.claude/agents/experto-seguridad.md`"

## Patrón antagónico (decisiones de arquitectura importantes)
Cuando hay una decisión difícil (ej: elegir entre dos enfoques técnicos):
Lanzar 2 subagentes con posturas opuestas:
- Subagente A: defiende la opción 1
- Subagente B: defiende la opción 2
Dejar que debatan y reportar al agente principal.
El resultado es de mayor calidad que una sola perspectiva.
COSTO: ~7x tokens — solo para decisiones que realmente lo justifican.
