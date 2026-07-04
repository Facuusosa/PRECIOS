# Guía Claude Code — 100% del Masterclass

*Basado en el video de ~4 horas. Referencia operativa, no tutorial.*

---

## 1. CLAUDE.md — El corazón del sistema

CLAUDE.md es lo primero que Claude lee antes de tu primer mensaje. No es documentación — es la **trayectoria del barco**. Todo lo que escribas ahí define cómo Claude se comporta en TODA la sesión.

Hay tres niveles:
- **Global** (`~/.claude/CLAUDE.md`): aplica a todos tus proyectos. Acá va tu perfil, tu rol, reglas de comportamiento general.
- **Proyecto** (`.claude/` dentro del repo): contexto específico del proyecto — stack, entrypoints, reglas de negocio.
- **Enterprise**: para organizaciones, se inyecta a nivel de equipo (no aplica a uso individual).

**Comando `/init`**: si arrancás un proyecto nuevo o heredás uno viejo, corré `/init` y Claude lee todo el codebase y genera un CLAUDE.md automáticamente en segundos. No escribir desde cero.

**Reglas de mantenimiento:**
- 200-500 líneas máximo. Alta densidad, cero relleno.
- No meter documentación completa de APIs. Solo lo que se usa activamente.
- Cuando Claude repite el mismo error dos veces → crear regla nueva en ese momento, no al final de la sesión.
- Los guardrails más importantes van AL PRINCIPIO (sesgo de primacía/actualidad).

---

## 2. Estructura `.claude/` — La carpeta de control
.claude/
├── CLAUDE.md          → contexto del proyecto
├── memory.md          → scratchpad persistente entre sesiones (88 tokens)
├── settings.json      → configuración de permisos y features
├── rules/             → reglas específicas (una por tema)
├── agents/            → definiciones de agentes especializados
└── skills/            → herramientas invocables con /nombre

**`memory.md`**: Claude lo lee automáticamente al inicio de cada sesión. Solo 88 tokens. Usarlo para guardar estado operativo, decisiones tomadas, contexto que no querés repetir cada vez.

**`settings.json`**: controla permisos, hooks de sonido (beeps cuando termina cada pestaña), y features experimentales como Agent Teams.

---

## 3. Skills — Herramientas lazy-loaded

Una skill es un archivo `SKILL.md` + una carpeta `scripts/` con el código real.
.claude/skills/
└── nombre-skill/
├── SKILL.md        → orquestador/checklist (instrucciones para Claude)
└── scripts/        → código Python, bash, etc.

**Clave**: las skills cargan solo **59-63 tokens** (solo el frontmatter) hasta que las invocás con `/nombre`. Ahí Claude lee el SKILL.md completo y ejecuta lo que corresponda.

Esto contrasta con MCP tools que cargan completamente siempre. Una skill = costo mínimo en standby, costo completo solo cuando se usa.

**Patrón de creación**: probá con MCP (5 min de setup) → cuando funciona, convertilo a skill (llamadas directas a la API, sin el overhead del MCP). Una skill bien escrita usa 90% menos tokens que el MCP equivalente.

---

## 4. MCP (Model Context Protocol) — Conectores a herramientas externas

MCPs conectan Claude directamente con APIs externas: Chrome DevTools, Gmail, Slack, GitHub, bases de datos.

**El favorito del instructor**: **Chrome DevTools MCP**. Controla Chrome, toma screenshots, hace clicks, lee el DOM. 100x más rápido que Selenium o Playwright para automatización visual.

**Estrategia MCP vs Skill:**
- MCP: prototipado rápido, 5 minutos de setup, descubrís si el approach funciona.
- Skill: producción, cuando confirmaste que el approach es correcto. Menos tokens, más control.
- No usés MCP en producción para algo que hacés todos los días → convertilo a skill.

**Advertencia de tokens**: algunos MCPs son enormes. ClickUp solo = 20k tokens por sesión. Elegí bien qué MCPs tenés activos.

---

## 5. Modos de permiso — Cuándo Claude pide permiso

Cuatro modos:

| Modo | Comportamiento |
|------|----------------|
| **Ask before edit** | Pide permiso antes de tocar cualquier archivo. Default. |
| **Auto-edit** | Edita sin pedir permiso. Para sesiones rápidas de confianza alta. |
| **Plan mode** | Solo lee, no edita nada. Explora y planifica. |
| **Bypass permissions** | Sin restricciones. Solo cuando sabés exactamente lo que hacés. |

**Plan mode es el más valioso para empezar cualquier tarea grande.** 1 minuto en plan mode = 10 minutos ahorrados construyendo en la dirección equivocada. Claude lee todos los archivos relevantes sin tocar nada, te presenta un plan, vos aprobás o ajustás, y recién ahí construye.

---

## 6. Screenshot loop — Construir UI sin escribir CSS a mano

El patrón más potente para frontend:

1. Conseguir imagen de referencia (screenshot de lo que querés)
2. Claude construye una primera versión
3. Claude toma screenshot de lo construido
4. Compara las dos imágenes, lista las diferencias
5. Aplica los fixes
6. Vuelve al paso 3

Con 4-5 iteraciones llegás al ~99% de match con el original. No se necesita saber CSS ni diseño.

**Tres enfoques de diseño del instructor:**
1. Screenshot loop (referencia visual)
2. Voice dump a 200 palabras por minuto — describir lo que querés, Claude interpreta
3. Tomar componentes de **21st.dev** o **godly.website** como punto de partida

---

## 7. Múltiples pestañas — Trabajo paralelo

Máximo 3-4 pestañas simultáneas activas. Más que eso y ninguna avanza bien.

**Truco de los beeps**: en `settings.json` configurar hooks que tocan un sonido distinto cuando termina cada pestaña. Sin mirar la pantalla sabés cuál terminó.

**Regla de uso**: cada pestaña necesita una tarea clara antes de abrirla. Si una pestaña lleva +10-15 minutos sin hacer nada → hay demasiadas abiertas.

---

## 8. Gestión de tokens y contexto

**Comando `/context`**: muestra el breakdown exacto de qué consume qué. Correrlo antes de sesiones largas.

**Breakdown típico:**
- Herramientas del sistema: ~16,800 tokens fijos (no controlable)
- CLAUDE.md global + proyecto
- MCPs activos (pueden ser enormes)
- memory.md: 88 tokens
- Skills activas: 59-63 tokens cada una (hasta que se invocan)
- Historial de mensajes

**Auto-compact**: se dispara automáticamente cuando quedan ~33k tokens libres. `/compact` para hacerlo manual.

**Cuándo actuar:**
- Contexto >60%: `/compact`
- Contexto >75%: nueva sesión
- No esperar al 100%

**Sesgo de primacía/actualidad**: Claude recuerda bien el inicio y el final de la conversación, casi nada del medio. Guardrails importantes → siempre primero en CLAUDE.md.

---

## 9. Dónde encontrar técnicas actuales

**X (Twitter) + Grok** es la mejor fuente de técnicas avanzadas y actualizadas de Claude Code. La documentación oficial siempre va atrás. Los power users postean sus descubrimientos ahí antes que en cualquier otro lado.

Buscar: "Claude Code tips", "Claude Code advanced", perfiles conocidos de la comunidad.

---

## 10. Extended thinking — Razonamiento profundo

Extended thinking NO está en el contexto principal de la conversación. Corre en un proceso separado. Claude "piensa" en profundidad antes de responder.

Se puede limitar entre 8k y 32k tokens de pensamiento según la complejidad de la tarea.

Cuándo usarlo: decisiones arquitecturales complejas, análisis de trade-offs, problemas que requieren razonamiento de varios pasos. No usarlo para tareas mecánicas.

---

## 11. Subagentes — Paralelización con costo real

Un subagente es un Claude separado que corre una tarea y devuelve el resultado.

**Costo: ~7x tokens vs agente único.** No es metáfora — es literal. Usarlos solo cuando tiene sentido real.

**Matemática de probabilidad (importante):**
10 subagentes con 95% de éxito cada uno = 59% de éxito total.
La probabilidad se multiplica: 0.95^10 = 0.598.
Esto significa: cuanto más complejas las tareas de cada subagente, más chances de que el sistema completo falle. Las definiciones de tarea deben ser simples y claras.

**Tres tipos de subagentes recomendados:**

| Tipo | Cuándo usarlo |
|------|---------------|
| **Research agent** | Aísla contexto ruidoso. Investiga una cosa específica sin contaminar la sesión principal. |
| **Code Reviewer** | Ojos frescos, sin sesgo. Ve el código como si fuera la primera vez. |
| **QA agent** | Corre tests y escribe el reporte a un archivo. No contamina el contexto principal con logs y output. |

**Para tareas paralelizables**: si tenés la misma tarea sobre N datos (revisar 100 emails, analizar 50 archivos) → subagentes. Para tareas secuenciales → un solo agente.

---

## 12. Agent Teams — Múltiples instancias en simultáneo

*Feature experimental. Habilitar en `settings.json`:*
```json
{
  "CLAUDE_AGENT_TEAMS_EXPERIMENTAL": "1"
}
```

Cada "teammate" es una instancia completa de Claude Code con su propio CLAUDE.md, sus propios MCPs, sus propias skills. No son subagentes limitados — son instancias completas.

**Sistema de comunicación**: un "notepad" o bulletin board compartido. Los agentes postean mensajes ("terminé el módulo A, encontré estos issues"), otros los leen y actúan. No es chat en tiempo real — es más como un tablón de anuncios.

**Dos modos de trabajo:**
- **Process mode**: Alt+Tab entre ventanas. Cada agente en su terminal. Caótico pero funciona.
- **Split panel mode**: Todos los agentes visibles al mismo tiempo en paneles. Más limpio, mejor para monitoreo.

**Mejor caso de uso según el instructor**: NOT para construir websites (aunque funciona). El real valor es en auditorías sobre codebases existentes — múltiples agentes escaneando distintas partes del código en paralelo.

---

## 13. Agentes adversariales — El patrón GAN

Análogo a las redes generativas adversariales (GANs) en machine learning: dos elementos en oposición se vuelven mejores juntos.

**Patrón:**
1. Tener un output (hallazgos de seguridad, una decisión técnica, un análisis)
2. Lanzar dos agentes con posturas opuestas:
   - **Diablo 1**: "esto no es un problema real, argumentá por qué es falso positivo"
   - **Diablo 2**: "esto sí es un problema crítico, argumentá por qué necesita arreglo urgente"
3. El debate obliga a ambos a justificar con argumentos concretos
4. El output del debate es de calidad notablemente mayor

**Demo del video (repo OpenClaw):**
- 10 agentes escanean el codebase simultáneamente
- 4 agentes documentan todos los hallazgos
- 2 agentes adversariales debaten cuáles son reales
- 15 agentes fixers aplican correcciones confirmadas
- Duración: 15 minutos. Costo: **$80**

El instructor: *"Son casi como un arma nuclear, solo que dirigida directamente a tu bolsillo."* Reservar para casos donde la calidad justifica el costo: antes de demos con clientes, releases críticos, auditorías de seguridad serias.

**El patrón adversarial NO requiere Agent Teams.** Con dos subagentes en una sesión normal alcanza. Agent Teams lo escala, pero la idea en sí es aplicable con mucho menos costo.

---

## 14. Git Worktrees — Agentes en paralelo sin conflictos

El problema sin worktrees: dos agentes trabajando sobre el mismo repo eventualmente tocan el mismo archivo y se pisan.

La solución: crear carpetas completamente separadas, una por feature, cada una en su propia rama de git.

```bash
# Crear worktrees
git worktree add ../brujula-auth feature/auth
git worktree add ../brujula-scraper feature/scraper

# Trabajar: un Claude Code en cada carpeta
# Al terminar: mergear a main
git worktree remove ../brujula-auth
git worktree remove ../brujula-scraper
```

Cada agente trabaja en su carpeta, nunca ve la del otro, cero conflictos.

**Señal de cuándo usar worktrees**: tarea A y tarea B no tocan los mismos archivos. Si se tocan, resolverlo antes de separar.

---

## 15. Modal.com — Desplegar skills como URLs públicas

Modal.com permite tomar cualquier función Python y convertirla en una URL pública sin servidor ni infraestructura.

**Costo**: mínimo. El instructor mostró su cuenta después de meses de uso — había gastado $0.50 de $5 de crédito inicial.

**Setup:**
1. Crear cuenta en modal.com
2. Generar API token
3. Pegárselo a Claude (o en CLAUDE.md)
4. Decirle "configurá Modal para este proyecto"
5. Claude instala el paquete, configura el ambiente, escribe `modal_app.py` solo

**Demo clave**: tomó el skill de scraping de leads → lo desplegó como URL pública → creó un formulario (rubro a buscar, ciudad, cantidad de leads) → el usuario completa el form → 90 segundos después → descarga un CSV.

Sin terminal. Sin instalar nada. Solo una URL.

**Integración con no-code:**
La URL de Modal se puede enchufar como webhook a: **make.com**, **Zapier**, **N8n**, **Lindy**. Ejemplo: "cada lunes a las 9am, correr el scraper para este rubro, mandar el CSV por email." Todo configurado una vez, corre solo para siempre.

Modal es la "última milla": Claude Code construye las herramientas, Modal las hace accesibles al mundo, las plataformas no-code las orquestan.

---

## 16. Workflow de voz — 3x más rápido que escribir

Para prompts largos o complejos:
1. Activar dictado (Windows: Win+H | Mac: Fn doble)
2. Hablar sin preocuparse por redacción
3. Pegar el texto crudo — Claude procesa aunque esté desordenado

Para prompts muy largos que consumen muchos tokens:
1. Hablar → pegar en sesión con **Haiku** (modelo barato)
2. Pedirle: "Resumí esto en un prompt conciso para Sonnet"
3. Copiar el resumen → pegar en la sesión principal con Sonnet

Ahorra tokens sin perder información.

---

## 17. Fast mode y selección de modelos

**Fast mode (Opus a 2.5x velocidad)**: Opus 4.6 al doble de velocidad por ~3x el costo normal. Para cuando necesitás la mayor inteligencia posible sin esperar.

**Tabla de selección de modelos:**

| Tarea | Modelo |
|-------|--------|
| Búsquedas simples, preguntas de una línea | Haiku |
| Desarrollo, análisis, todo lo regular | Sonnet |
| Decisiones arquitecturales complejas | Opus (o Plan mode en Sonnet) |
| Subagentes de research (muchos datos) | Sonnet (barato a escala) |

---

## Resumen operativo — Qué usar cuándo

| Situación | Herramienta |
|-----------|-------------|
| Nueva sesión de trabajo | Lee memory.md, `/context` para ver consumo |
| Tarea grande sin claridad | Plan mode primero |
| UI/frontend | Screenshot loop |
| Prototipo con API externa | MCP |
| Producción con API externa | Skill (convertida del MCP) |
| Tareas repetibles en N datos | Subagentes |
| Features independientes simultáneas | Git Worktrees |
| Exploración de diseño | Agent Teams (3 variantes en paralelo) |
| Auditoría de calidad/seguridad seria | Agent Teams + adversarial ($$$) |
| Skill accesible sin terminal | Modal.com |
| Prompt largo o complejo | Voz → Haiku → Sonnet |
| Contexto >60% | `/compact` |
| Contexto >75% | Nueva sesión |
| Claude repite mismo error | Nueva regla en `.claude/rules/` YA |