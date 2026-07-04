# Mapa de decisión — qué herramienta de Claude usar según el escenario

Chuleta de referencia de Facu. La idea: mirar la columna "escenario", encontrar el tuyo,
usar la herramienta de al lado. No hay que memorizar — se aprende usándolo.

Claude opera en **modo copiloto explícito**: cada vez que use una de estas herramientas,
la nombra y explica por qué la eligió (2 líneas), integrado en el trabajo. Ver
`.claude/rules/10-coaching-copiloto.md`.

---

## Tabla rápida

| Escenario real | Herramienta | Por qué esa (y no otra) |
|---|---|---|
| Tarea de 3+ archivos, refactor, o código que no conozco | **Plan mode** (`Shift+Tab` x2) | Planifica sin tocar nada; vos aprobás antes de que ejecute |
| Repetís el mismo paso a paso más de una vez | **Skill** (`.claude/skills/`) | Lo escribís 1 vez y se reusa; Claude la invoca sola cuando aplica |
| Algo que DEBE pasar siempre (lint, verificación, backup) | **Hook** (`.claude/settings.json`) | Garantía determinística. CLAUDE.md es "sugerencia"; el hook es "obligatorio" |
| Investigar / tarea que genera mucho output | **Subagente** (agente en paralelo) | Trabaja en su propio contexto y te trae solo el resumen; no ensucia el tuyo |
| Conectar Drive, Figma, Vercel, una base de datos | **MCP server** | Acceso directo a la herramienta; sin copiar y pegar datos |
| Contexto lleno (>60%) o cambiás de tema | **/compact** (comprimir) o **/clear** (reset) | Recuperás calidad de respuesta; el contexto lleno degrada todo |
| Ver cuánto contexto/tokens estás usando | **/context** | Muestra el breakdown; correlo antes de sesiones largas |
| Pregunta simple o tarea mecánica | Modelo **Haiku** | ~20x más barato y más rápido; no malgastás Sonnet/Opus |
| Trabajo normal de desarrollo/análisis | Modelo **Sonnet** | El equilibrio calidad/costo; el default |
| Decisión difícil con tradeoffs reales | Modelo **Opus** + patrón adversarial | Mejor razonamiento; para lo que se justifica el costo |
| Querés un formato de salida exacto (JSON, tabla) | **Dar 2-3 ejemplos** en el prompt | Lo más confiable para controlar formato; Claude copia el patrón |
| Decisión con trampa (ej: precios de distinto tamaño) | Pedir **razonar paso a paso** | Ves el error en el razonamiento antes de que llegue al resultado |
| Volver atrás tras 2 correcciones fallidas | **Esc + Esc** (rewind) | Contexto limpio + mejor prompt gana a insistir sobre uno malo |
| 2 tareas independientes a la vez | **Git Worktrees** + pestañas | Corren en paralelo sin pisarse los archivos |

---

## Las 4 reglas de oro de prompting (aplican a todo lo de arriba)

1. **Claro y específico** — describí la salida exacta que querés. Tratá a Claude como un
   empleado brillante pero nuevo: si un colega sin contexto se confundiría, Claude también.
2. **Dale ejemplos** — 2 a 5 casos reales. Es la palanca más fuerte para controlar formato y tono.
3. **Explicá el POR QUÉ** — "verificá precios en vivo *porque* un dato viejo le hace vender a
   pérdida al cliente" rinde más que la regla pelada. Claude generaliza desde la intención.
4. **Decí lo que SÍ querés**, no lo que no querés — "devolvé JSON" > "no uses markdown".

---

## Diferencias que se confunden seguido

- **Skill vs Hook:** la skill es un workflow que Claude *puede* usar; el hook es una acción que
  el sistema *siempre* ejecuta. ¿Debe pasar sí o sí? → hook. ¿Es un paso a paso reusable? → skill.
- **Skill vs Slash command:** el slash command nativo es lógica fija y rápida (`/compact`); la
  skill es un prompt inteligente que se adapta y Claude puede autoinvocar.
- **Subagente vs Plan mode:** el subagente hace trabajo aparte (investigar); el plan mode planifica
  el trabajo que vas a hacer vos+Claude en el contexto principal.
- **CLAUDE.md vs memoria:** CLAUDE.md son instrucciones que vos escribís; la memoria son notas que
  Claude se guarda solo entre sesiones. Tip oficial: CLAUDE.md largo (>~200 líneas) hace que Claude
  ignore partes — mantenerlo podado.

---

Fuente: documentación oficial de Anthropic (code.claude.com/docs y platform.claude.com/docs),
relevada el 30/06/2026.
