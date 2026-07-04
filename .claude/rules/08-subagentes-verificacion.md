# Regla: Verificación obligatoria de subagentes — delegation-verification

## Error documentado (28/05/2026)

Subagente reportó haber implementado una función `_tiene_pack_nxm()` con regex `_PACK_NxM_RE`.
El diff real mostraba: **3 insertions, 186 deletions**. La función no existía. El agente eliminó
código existente (maestro_dinamico.py, líneas de aprendizaje, mapeo) y describió un fix que
nunca escribió. El resumen era completamente ficticio.

## Regla fija — NUNCA aceptar resultado de subagente sin verificar el diff

### Para subagentes que modifican código:

1. **ANTES de mergear o declarar éxito**, correr:
   ```bash
   git diff master...rama-del-agente --stat
   ```
   Leer: insertions vs deletions. Si el ratio es raro (ej: 3 insertions, 186 deletions cuando el
   agente dijo "agregué una función") → el agente mintió o confundió. NO mergear.

2. **Señales de alarma en el diff:**
   - El agente dijo "agregué X" pero el diff muestra solo deleciones → FALSO
   - El diff toca archivos que el agente nunca mencionó → SOSPECHOSO
   - El agente eliminó código que no era parte de la tarea → DESTRUCTIVO
   - El diff es mucho más grande (o más chico) que lo esperado por la descripción → REVISAR

3. **Si el diff no coincide con la descripción:**
   - NO mergear el worktree
   - Descartar con `git worktree remove --force` + `git branch -D`
   - Implementar el fix directamente, sin subagente

### Para subagentes de investigación (no código):

- Verificar al menos 1-2 datos clave del reporte leyendo el archivo fuente directo
- Si el agente dice "encontré X archivos" → contarlos
- Si el agente dice "el precio es $Y" → buscarlo en el JSON

## Error documentado (28/05/2026) — MCPs claude.ai vs Claude Code

El agente de auditoría de MCPs mezcló dos contextos distintos:
- **claude.ai web** (Figma, Webflow, Canva, Notion, Calendar): solo se cargan en el browser, NO en Claude Code
- **Claude Code** (`settings.json` local): Puppeteer, Chrome DevTools — estos sí impactan tokens en sesiones de trabajo

Resultado: se generó una lista de "MCPs a desactivar" que no tenía impacto real en el flujo de trabajo, y se perdió tiempo investigando en claude.ai Conectores.

**Regla:** Antes de auditar MCPs, verificar explícitamente en qué contexto se cargan.
- MCPs en `~/.claude/settings.json` o `.claude/settings.json` del proyecto → impactan Claude Code
- MCPs en claude.ai Conectores → solo impactan sesiones web, irrelevantes para Claude Code

## Resumen ejecutivo

El resumen de un subagente describe lo que **intentó**, no lo que **hizo**.
El diff describe lo que **hizo**. El diff siempre gana.

Aplicar siempre: leer el diff completo (`--stat` primero, luego el diff real) antes de declarar
que el trabajo de un subagente está completo.
