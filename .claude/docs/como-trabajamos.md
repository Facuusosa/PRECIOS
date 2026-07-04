# Cómo Trabajamos — El Equipo de Dos

> Mapa madre de cómo Facu + Claude reemplazan lo que haría un equipo completo.
> No inventa reglas nuevas — conecta las que ya existen en `.claude/rules/`.

## El ciclo de una tarea (7 pasos)

| # | Paso | Pregunta que responde | Dónde vive la regla |
|---|------|------------------------|------------------------|
| 1 | Filtro | ¿Esto acerca al primer pagador o es feature creep? | `01-proyecto.md`, `06-jarvis-razonamiento.md` |
| 2 | Decidir el approach | ¿Es obvio (ejecuto directo) o es grande/ambiguo (protocolo adversarial + Plan mode)? | `06-jarvis-razonamiento.md` |
| 3 | Ejecutar | ¿Qué herramienta y qué modelo (Haiku/Sonnet/Opus) le corresponde? | `06-jarvis-razonamiento.md` |
| 4 | Verificar | Bucle verificador, nunca un solo chequeo | `testing.md` |
| 5 | Auto-review | 6 preguntas antes de decir "listo" | `05-autoreview.md` |
| 6 | Registrar | Error repetido → regla nueva ya. Aprendizaje no obvio → memoria | `04-protocolo.md` |
| 7 | Cerrar sesión | ¿Quedó todo anotado para la próxima? | ritual de cierre |

## Equivalencia: equipo real vs. nosotros dos

| Lo que hace un equipo real | Nuestro reemplazo | Cuándo se dispara |
|---|---|---|
| Kickoff / planificación | Filtro PM + Plan mode | Antes de cualquier feature nueva |
| Debate de arquitectura | Protocolo adversarial (2 subagentes con posturas opuestas) | Decisión difícil, tarea >30 min, dos caminos razonables |
| Code review | Skill `/code-review` + agente `auditor` | Antes de cada commit importante |
| Daily standup | Ritual de apertura de sesión | Inicio de cada sesión |
| Retro / postmortem | Error-to-rule + memoria | Cuando algo falla, o al cierre |
| Documentación del equipo | `.claude/rules/` + memoria persistente | Continuo |
| Sponsor frenando features innecesarias | Filtro anti-dispersión | Cada vez que aparece una idea nueva |

## El límite honesto

"Que no se escape nada" no existe, ni en equipos de 50 personas. Lo que sí existe es bajar mucho el margen de error. El verdadero seguro no es este mapa — es el **ritual de cierre de sesión**, donde repasamos juntos qué quedó suelto antes de que Facu se vaya.
