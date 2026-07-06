# HERRAMIENTAS DE BRÚJULA DE PRECIOS

Manual de skills, agentes y flujos. Actualizar cada vez que se crea, modifica o elimina una herramienta.

---

## FLUJOS — Cuándo usar qué

### Inicio de sesión (30 segundos, siempre)
```
/status-proyecto
```
Si hay ROJO → atacar eso antes de hacer cualquier otra cosa.

### Flujo semanal (20-30 min)
```
/pipeline-datos         → scrapers frescos
/verificar-precios      → spot-check 10 bombas
push catálogo a Vercel  → datos frescos en producción
```

### Flujo de outreach (cuando hay comercios para contactar)
```
/investigar-y-contactar [nombre] [tipo] [zona]
→ aprobación de Facu
→ enviar
```
Procesar de a 5 comercios. No mandar sin revisar el borrador.

### Flujo pre-lanzamiento masivo (antes de mandar 50+ mensajes)
```
/pre-launch-check
→ si GO: push catálogo + outreach
→ si NO-GO: corregir lo que falló
```

### Flujo de mantenimiento del proyecto (cuando hay acumulación de basura)
```
Agente: limpiador
→ escanea, reporta, espera confirmación, limpia
→ actualiza este archivo si hay cambios en herramientas
```

### Cierre de sesión importante (siempre que se cambió algo relevante)
```
/cerrar-sesion
```

---

## SKILLS DEL PROYECTO

Skills propias de Brújula de Precios. Viven en `.claude/skills/` como archivos `.md` sueltos (no en subcarpeta).

### /status-proyecto
**Qué hace:** Semáforo de 30 segundos — Yaguar / MaxiCarrefour / Maxiconsumo / Coto / Catálogo / Cookies CF / Deploy. Estado VERDE/AMARILLO/ROJO por componente con próximos 3 pasos concretos.
**Cuándo:** Al inicio de cada sesión.
**Archivo:** `.claude/skills/status-proyecto.md`

---

### /pipeline-datos
**Qué hace:** Corre los 5 scrapers en orden (Yaguar → MaxiCarrefour → Maxiconsumo → Coto → Carrefour), verifica counts mínimos (Y>3000, C>3000, M>500, Coto>10000, Carrefour>8000), confirma que `catalogo_unificado.json` se actualizó.
**Cuándo:** Una vez por semana o cuando el catálogo tiene más de 3 días.
**Archivo:** `.claude/skills/pipeline-datos.md`

---

### /investigar-y-contactar
**Qué hace:** Para un comercio específico — busca en Google/Facebook quiénes son, extrae ejemplos de precios relevantes para su tipo de negocio, redacta mensaje personalizado (tono cálido, sin marketing), muestra borrador, espera aprobación, crea draft Gmail o genera texto para WhatsApp.
**Cuándo:** Cuando hay comercios para contactar. Procesar de a 5 por sesión.
**Archivo:** `.claude/skills/investigar-y-contactar.md`
**Nota:** El skill más importante para generar ingresos. Priorizar siempre.

---

### /verificar-precios
**Qué hace:** Corre `scripts/verificar_bombas.py` con las top N bombas. Verifica precio web vs catálogo. Resultado por bomba: OK / DIFF_X% / ERROR_X% / NO_ENCONTRADO. Genera reporte en `data/quality/`.
**Cuándo:** Antes de mostrar la app a alguien, después de renovar cookies, spot-check semanal.
**Criterio GO:** 8/10 bombas con estado OK.
**Archivo:** `.claude/skills/verificar-precios.md`

---

### /pre-launch-check
**Qué hace:** Auditoría completa antes de outreach masivo. Orquesta: (1) antigüedad catálogo, (2) agente auditor, (3) verificar bombas, (4) agente QA en producción. Genera reporte GO/NO-GO con criterios claros.
**Cuándo:** Antes de mandar lotes grandes de outreach o antes de una release importante.
**Criterio GO:** Catálogo <24hs + sin CRÍTICO en auditor + ≥8/10 bombas OK + ≥4/5 vistas VERDE + >10.000 productos.
**Archivo:** `.claude/skills/pre-launch-check.md`

---

### /cerrar-sesion
**Qué hace:** Protocolo de cierre. Revisa la sesión, actualiza `rules/` si se descubrió algo nuevo, actualiza `docs/` si cambió algún proceso, escribe en memoria persistente el estado actual del proyecto.
**Cuándo:** Al terminar cualquier sesión donde se modificó código, scrapers, o se tomaron decisiones importantes.
**Archivo:** `.claude/skills/cerrar-sesion.md`

---

### /auditoria-seguridad
**Qué hace:** Busca credenciales hardcodeadas en todo el código, verifica `.gitignore`, confirma que todos los scripts usan `os.getenv()`, revisa frontend por datos sensibles en `console.log`. Checklist de 5 items pre-deploy.
**Cuándo:** Antes de cada deploy a producción.
**Archivo:** `.claude/skills/auditoria-seguridad.md`

---

### /contexto-check
**Qué hace:** Corre `/context`, muestra breakdown de tokens por fuente, recomienda continuar / hacer `/compact` / abrir sesión nueva según el porcentaje. Sugiere modelo óptimo (Haiku/Sonnet/Opus) para la tarea que viene.
**Cuándo:** Antes de sesiones largas o si algo parece lento.
**Archivo:** `.claude/skills/contexto-check.md`

---

### /disenar-pantalla
**Qué hace:** Screenshot loop para mejorar UI. Toma screenshot de la vista actual, busca referencia en skills.sh → 21st.dev → ReactBits, propone mejora concreta, implementa, toma otro screenshot, itera hasta aprobación.
**Cuándo:** Cuando hay trabajo específico de diseño visual.
**Orden de referencias:** skills.sh → 21st.dev → ReactBits → construir desde cero.
**Archivo:** `.claude/skills/disenar-pantalla.md`

---

### /railway-deploy ⚠️ ARCHIVADO
**Estado:** Railway dado de baja el 13/06/2026. El scraping corre LOCAL via `pipeline_local.py` + Task Scheduler de Windows.
**Reactivar:** solo si hay ingresos y se quiere nube 24/7. Ver `archive/README.md` para instrucciones.
**Archivo:** `.claude/skills/railway-deploy.md`

---

### /actualizar-familias
**Qué hace:** Detecta pack mixing en el catálogo, sugiere FAMILIAs nuevas usando `analizar_familias.py`, aplica sugerencias de alta confianza automáticamente, re-corre el catálogo y reporta mejora en tasa de matching.
**Cuándo:** Cuando la tasa de matching baja o cuando se sospecha que hay productos del mismo tipo que no se están comparando.
**Archivo:** `.claude/skills/actualizar-familias.md`

---

### /buscar-comercios
**Qué hace:** Busca kioscos, almacenes y minimercados en una zona específica via WebSearch, estructura los resultados y los guarda en `data/outreach/comercios_[zona]_[fecha].json`.
**Cuándo:** Cuando se necesita ampliar la lista de prospectos para outreach.
**Archivo:** `.claude/skills/buscar-comercios.md`

---

### /verificar-app
**Qué hace:** Check rápido de la app en producción con Puppeteer — verifica Inicio, Catálogo, Calculadora y Lista. Sin precios hardcodeados, solo verifica que los componentes carguen y funcionen.
**Cuándo:** Post-deploy rápido o antes de enviar mensajes a comercios.
**Archivo:** `.claude/skills/verificar-app.md`

---

### /bucle-optimizador
**Qué hace:** Audita código, datos y frontend buscando mejoras con ROI. Propone top 3 oportunidades ordenadas por Impacto × Facilidad. En modo loop (via `/loop`), solo escribe en `audit_log.md` sin implementar.
**Cuándo:** Cuando hay tiempo para mejoras no urgentes o para encontrar cuellos de botella no obvios.
**Archivo:** `.claude/skills/bucle-optimizador.md`

---

### /brain-dump
**Qué hace:** Tomás todo lo que tenés en la cabeza — caótico, sin orden — y lo clasifica en: ACCIONES FASE 0, ACCIONES FASE 1+, IDEAS PARA DESPUÉS, DECISIONES PENDIENTES. Lo ordena por impacto y devuelve una lista accionable.
**Cuándo:** Cuando tenés muchas cosas en la cabeza y no sabés por dónde empezar. Antes de una sesión de trabajo para organizarte.
**Cómo usar:** Escribí todo lo que tenés sin filtro y pegalo.
**Archivo:** `.claude/skills/brain-dump.md`

---

### /revision-semanal
**Qué hace:** Diagnóstico completo del proyecto — estado técnico (scrapers, catálogo, cookies, deploy), estado comercial (contactados, respondieron, pagando, revenue ARS), y top 3 acciones para la semana (mínimo 2 comerciales, máximo 1 técnica). Formato semáforo VERDE/AMARILLO/ROJO.
**Cuándo:** Cada lunes. O cuando Facu pregunta "¿cómo vamos?".
**Archivo:** `.claude/skills/revision-semanal.md`

---

### /buscar-x
**Qué hace:** Busca en X/Twitter tecnicas, ejemplos y patrones recientes sobre un tema de UI/UX o frontend antes de implementar. Corre 2-3 queries con WebSearch, sintetiza los hallazgos, reporta la tecnica mas relevante y la aplica (o confirma que no hay nada mejor que el enfoque actual).
**Cuándo:** Antes de implementar cualquier animacion nueva o componente UI que no existe en el proyecto.
**Regla:** Maximo 5 minutos de busqueda. Si 3 queries no dan nada util, seguir con el plan sin bloquearse.
**Archivo:** `.claude/skills/buscar-x.md`

---

## AGENTES

Los agentes son subagentes que corren fuera del contexto principal. Consumen más tokens que los skills pero protegen el contexto de resultados grandes.

### auditor
**Qué hace:** Auditoría profunda del proyecto completo — salud del catálogo, scrapers, frontend (errores TypeScript), seguridad (credenciales hardcodeadas), deuda técnica. Output estructurado: CRÍTICO / ATENCIÓN / OK.
**Cuándo:** Antes de releases importantes, cuando hay dudas de calidad, o cuando algo raro está pasando.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/auditor.md` y auditá el proyecto completo"

---

### auditor-catalogo
**Qué hace:** QA específico de los datos del catálogo — detecta matches incorrectos (ratio >3x entre fuentes), precios fuera de rango ($300-$300k), duplicados por nombre similar.
**Cuándo:** Cuando un usuario reporta un precio incorrecto, después de cada corrida del unificador, antes de cada deploy.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/auditor-catalogo.md` y auditá el catálogo"

---

### qa-verificador
**Qué hace:** QA completo de la app en producción con Puppeteer. Navega todas las vistas, verifica calculadora de margen, detecta errores JS, **escribe el reporte a `data/quality/qa-reporte-[fecha].md`** sin contaminar el contexto.
**Cuándo:** Como parte de `/pre-launch-check` o cuando se necesita evidencia documentada del estado de la app.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/qa-verificador.md` y verifica la app en [URL]"

---

### limpiador
**Qué hace:** Limpieza y mantenimiento del proyecto en dos modos: AUTO (borra sin preguntar: `__pycache__`, JSON vacíos, archivos debug) + REVIEW (muestra reporte y pide confirmación para outputs viejos, archivos huérfanos).
**Cuándo:** Cuando el proyecto acumula basura. Recomendado: una vez por mes.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/limpiador.md` y limpiá el proyecto"

---

### pm-implacable
**Qué hace:** Evalúa cualquier idea o tarea con una sola pregunta: "¿Esto acerca al primer pagador o lo aleja?". Output: CONSTRUIR AHORA / ENCOLAR FASE 1 / ENCOLAR FASE 2 / DESCARTAR + razón en 1 línea.
**Cuándo:** Antes de empezar cualquier tarea nueva no planificada. Cuando aparece una idea nueva.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/pm-implacable.md` y evaluá [idea]"

---

### experto-seguridad
**Qué hace:** Auditoría de seguridad del proyecto — busca credenciales hardcodeadas, verifica que `.env` no esté en git, revisa cookies de scrapers, chequea frontend por datos sensibles, verifica Railway/Vercel. Output: CRITICO / IMPORTANTE / BAJO RIESGO.
**Cuándo:** Antes de cada release o deploy. Cuando se agregan credenciales nuevas. Una vez por mes.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/experto-seguridad.md` y auditá el proyecto"

---

### diseñador-ux
**Qué hace:** Diseñador UX/UI senior con foco en mobile comercial. Evalúa pantallas en orden de impacto (tipografía → colores → hover states → layout → estados vacíos), recomienda cambios concretos con código, y sabe qué componentes ReactBits usar (y cuáles NO, como SplitText).
**Cuándo:** Cuando hay que revisar el diseño de una vista, elegir entre opciones de layout, o mejorar la calidad visual de un componente específico.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/diseñador-ux.md` y revisá [vista/componente]"

---

## SKILLS DE DISEÑO INSTALADAS (09/06/2026)

### emil-design-eng (skill — invocable como /emil-design-eng)
**Qué hace:** Filosofía de Emil Kowalski (creador de Sonner/Vaul) con números exactos: animaciones <300ms, easing custom `cubic-bezier(0.23,1,0.32,1)`, nunca ease-in, press `scale(0.97)` 160ms, stagger 30-80ms, prefers-reduced-motion siempre.
**Cuándo:** SIEMPRE que se escriba o revise una animación/transición/micro-interacción.

### impeccable (skill — invocable como /impeccable)
**Qué hace:** 23 comandos de polish de diseño de Paul Bakaus (36.8k stars). Crítica de jerarquía, ruido visual, anti-patrones de IA, accesibilidad, estados vacíos.
**Cuándo:** Auditoría de calidad visual de una vista antes de darla por terminada.

---

## ROLES DE CLAUDE — Cuándo se activan

| Rol | Se activa cuando... | Podés pedirlo con... |
|---|---|---|
| **JARVIS** | Siempre — es el default. Ejecuta, implementa, propone próximo paso. | — |
| **ANALISTA CRÍTICO** | Después de cada plan, antes de ejecutar. Busca fallas y supuestos no verificados. | "Analiza esto de forma crítica" |
| **UX EXPERT** | Cuando hay cambios de frontend. Se pone en la piel del comerciante de barrio. | "Evaluá esto como UX" |
| **CFO / FINANCISTA** | Cuando aparecen números: precios, márgenes, costos, viabilidad. | "Hacé los números" |
| **PM IMPLACABLE** | Cuando hay riesgo de construir por construir. Primera pregunta: "¿acerca al primer pagador?" | "Evalualo como el PM implacable" |
| **EXPERTO EN SEGURIDAD** | Antes de releases, cuando se agregan credenciales, cuando algo tiene riesgo. | "Auditá la seguridad" |
| **COACH DE CRECIMIENTO** | Cuando se usa una técnica no obvia. La nombra y explica en 1 línea. | — |
| **PROFESOR DE IA** | Cuando aparece un tecnicismo de Claude Code, IA, agentes, MCPs. Lo explica integrado al trabajo real. | "Explicame qué es esto" |

---

## SKILLS DEL SDK — Catálogo completo (83 skills)

Skills pre-instaladas del SDK de Claude. Viven en `.claude/skills/[nombre]/SKILL.md`.
Se invocan con `/nombre` o Claude las activa automáticamente según contexto.

---

### CATEGORÍA 1 — ADQUIRIR USUARIOS

Skills para conseguir que comerciantes conozcan Brújula. Prioridad máxima en Fase 0.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/cold-email` | Escribir el primer email a alguien que no te conoce. Incluye cómo hacer seguimiento cuando no responden. | Contactar almaceneros por email por primera vez |
| 2 | `/copywriting` | Escribir textos persuasivos desde cero: que generen interés y acción | Pitch de WhatsApp, landing page, mensajes de presentación |
| 3 | `/copy-editing` | Revisar y mejorar textos que ya existen: hacerlos más claros y más efectivos | Cuando el mensaje de outreach no genera respuestas |
| 4 | `/social-content` | Crear posteos para Instagram, TikTok, LinkedIn, Twitter/X | Posts mostrando comparativas de precios: "Yaguar vs Maxiconsumo en aceite" |
| 5 | `/content-strategy` | Planificar qué publicar y dónde para que los clientes lleguen solos a buscar Brújula | Blog o redes para posicionarse como referencia de precios mayoristas |
| 6 | `/community-marketing` | Entrar en grupos y comunidades online, aportar valor antes de vender | Grupos de Facebook de almaceneros, foros de kiosqueros |
| 7 | `/email-sequence` | Crear una serie de emails automáticos: uno al registrarse, otro a los 3 días, otro si no usó la app | Follow-up a comercios que no respondieron el primer contacto |
| 8 | `/ad-creative` | Generar muchas variaciones de un anuncio (distintos titulares, imágenes, textos) para testear cuál convierte más | Cuando se corran ads en Instagram o Google (Fase 1+) |
| 9 | `/paid-ads` | Estrategia y gestión de campañas pagas: Google Ads, Meta (Facebook/Instagram), LinkedIn | Cuando haya presupuesto para publicidad (Fase 1+) |
| 10 | `/co-marketing` | Encontrar otras empresas para hacer acciones conjuntas donde los dos ganan | Alianzas con apps de gestión para kioscos (se promocionan mutuamente) |
| 11 | `/referral-program` | Diseñar un sistema donde los usuarios actuales traen nuevos usuarios a cambio de un beneficio | "Traé un comerciante y los dos ganan 1 mes gratis" (Fase 2) |
| 12 | `/directory-submissions` | Listar el producto en directorios donde la gente busca herramientas (ProductHunt, G2, etc.) | Cuando haya una página pública de Brújula para indexar |
| 13 | `/launch-strategy` | Planificar cómo anunciar al mundo que Brújula existe | Cuando haya 10+ usuarios y se quiera escalar |
| 14 | `/free-tool-strategy` | Crear una herramienta gratis que atraiga usuarios y los convierta en clientes pagos | Calculadora de margen pública en Google: la gente la usa y descubre Brújula |
| 15 | `/lead-magnets` | Crear un recurso gratuito (guía, plantilla, etc.) para captar emails de potenciales clientes | "Guía: márgenes reales para almacenes en 2026" |
| 16 | `/sales-enablement` | Crear materiales para mostrar en una reunión de venta: una hoja con el valor, respuestas a objeciones comunes | Una página A4 con "cuánto ahorra un almacén por mes con Brújula" |
| 17 | `/internal-comms` | Escribir comunicaciones internas de empresa con formatos específicos | No aplica en Fase 0 — es para equipos grandes |

---

### CATEGORÍA 2 — DISEÑO Y FRONTEND

Skills para el aspecto visual y de interfaz de la app.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/design-taste-frontend` | Sube el nivel visual de cualquier componente: botones que "responden" al toque, pantallas de error que no parecen rotas, layouts que no parecen genéricos de plantilla | Mejorar cualquier componente — es la skill de diseño de uso más frecuente |
| 2 | `/high-end-visual-design` | Diseño de agencia premium: mucho espacio en blanco, animaciones con física real, cards con profundidad y capas | Para landing page o pantalla de onboarding donde se quiera impresionar (Fase 1) |
| 3 | `/minimalist-ui` | Estilo limpio tipo Notion o Linear: colores neutros cálidos, tipografía con jerarquía clara, sin gradientes ni sombras exageradas | Vistas de configuración y perfil — que se sientan ordenadas y simples |
| 4 | `/frontend-design` | Crear interfaces web de calidad de producción — componentes completos con todos los estados | Componentes nuevos cuando no hay referencia clara de dónde partir |
| 5 | `/gpt-taste` | Diseño de nivel internacional (los sitios que ganan premios de diseño). Animaciones muy elaboradas con GSAP. | Para cuando se quiera un WOW visual real — raro en Brújula Fase 0 |
| 6 | `/industrial-brutalist-ui` | Estética ruda: tipografía gruesa sin decoración, colores planos, interfaz que parece una terminal | No aplica a Brújula — es un estilo muy específico |
| 7 | `/image-to-code` | Dale una imagen o un mockup y la convierte a código React. Flujo: imagen → Claude la analiza → implementa | Cuando haya mockups de Figma o screenshots de apps que querés replicar |
| 8 | `/redesign-existing-projects` | Toma una pantalla existente y la mejora en orden de impacto: fuente → colores → hover states → layout → componentes → estados vacíos/error | Para elevar cualquier vista después de que esté implementada |
| 9 | `/web-design-guidelines` | Revisa el código de la interfaz para asegurarse de que sea accesible (contraste, tamaños táctiles, lectores de pantalla) | Auditoría de accesibilidad antes de lanzar |
| 10 | `/imagegen-frontend-web` | Genera imágenes de referencia de cómo podría verse un diseño web antes de codearlo | Crear mockups visuales antes de empezar a programar una pantalla nueva |
| 11 | `/imagegen-frontend-mobile` | Genera imágenes de referencia de cómo podría verse una pantalla en el celular | Cuando se diseñe especialmente para mobile |
| 12 | `/canvas-design` | Crear materiales visuales en formato imagen o PDF | Flyers, posts, materiales de marketing de Brújula |
| 13 | `/algorithmic-art` | Arte generativo: dibujos y animaciones creadas con código matemático | No aplica a Brújula |
| 14 | `/stitch-design-taste` | Genera un archivo especial (DESIGN.md) que le describe a la IA de Google cómo tiene que verse tu app para que las pantallas que genere sean consistentes con tu estilo | Para usar junto con Google Stitch — generación de pantallas con IA |
| 15 | `/brandkit` | Crea el kit visual de la marca: logo, paleta de colores, tipografías, ejemplos de uso | Cuando se quiera formalizar la identidad visual de Brújula |
| 16 | `/brand-guidelines` | Aplica los colores y tipografía oficiales de Anthropic | No aplica a Brújula — es específico para Anthropic |
| 17 | `/theme-factory` | Aplica un tema de colores y tipografía a documentos HTML, presentaciones y docs | Crear presentaciones de Brújula con el look de la marca |
| 18 | `/image` | Crear, generar o editar imágenes para marketing usando IA | Crear imágenes para posts de Instagram, WhatsApp o la landing |

---

### CATEGORÍA 3 — CONVERSIÓN Y CRO

Skills para mejorar que quien llega a la app termine comprando o usando el producto.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/paywall-upgrade-cro` | Mejorar la pantalla donde le pedís al usuario que pague: que el botón genere más clics, que el precio no asuste, que se entienda qué gana si paga | Vista Cuenta → sección "Mi Plan" — el CTA de DESBLOQUEAR MAXICARREFOUR |
| 2 | `/page-cro` | Mejorar una página para que más gente haga lo que querés que haga (registrarse, hacer clic, comprar) | Vista Inicio cuando sea pública — que más comerciantes se registren |
| 3 | `/onboarding-cro` | Mejorar los primeros 60 segundos de un usuario nuevo para que entienda rápido por qué vale la pena quedarse | Cuando haya registro real — que el usuario vea valor antes de irse (Fase 1) |
| 4 | `/form-cro` | Optimizar cualquier formulario (que no sea de registro) para que la gente lo complete más | El formulario de nombre del negocio en Vista Cuenta |
| 5 | `/signup-flow-cro` | Mejorar el flujo completo de registro para que menos gente abandone en el camino | Cuando se agregue login real (Fase 1) |
| 6 | `/popup-cro` | Crear o mejorar popups y modales para que conviertan más — que la gente haga clic en el botón principal | Modal que aparece cuando el usuario toca una feature bloqueada por plan |
| 7 | `/ab-test-setup` | Probar dos versiones de algo (botón, título, diseño) con usuarios reales para ver cuál funciona mejor | Cuando haya suficientes usuarios para que los tests tengan sentido (Fase 1+) |
| 8 | `/analytics-tracking` | Agregar el código necesario para rastrear qué hace la gente en la app: qué pantallas visita, dónde abandona | Cuando se quiera entender el comportamiento real de los usuarios |
| 9 | `/churn-prevention` | Evitar que los usuarios pagos se vayan: cancelaciones, pagos fallidos, usuarios que dejaron de usar la app | Cuando haya usuarios pagando y alguno quiera cancelar |
| 10 | `/customer-research` | Hablar con usuarios reales o analizar sus respuestas para entender qué necesitan | Antes de construir features nuevas — para no construir lo que nadie pidió |
| 11 | `/pricing-strategy` | Definir cuánto cobrar y qué incluir en cada plan: qué da el FREE, qué el PRO, cómo posicionar los precios | Si hay dudas sobre si $6.999 es mucho o poco, o qué debería incluir el PREMIUM |
| 12 | `/marketing-psychology` | Usar cómo funciona la mente humana para mejorar el marketing: mostrar el precio caro antes del real (hace que parezca barato), crear urgencia, mostrar cuánta gente ya lo usa | Mejorar el copy de la sección Mi Plan — el "por qué pagar" tiene que convencer |
| 13 | `/product-marketing-context` | Crear un documento de referencia que define qué es Brújula, para quién es y por qué es mejor que las alternativas — para que todo el messaging sea consistente | Cuando se quiera definir el posicionamiento oficial de Brújula |

---

### CATEGORÍA 4 — SEO Y VISIBILIDAD ONLINE

Skills para que Brújula aparezca cuando alguien busca algo relacionado.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/seo-audit` | Auditar y diagnosticar problemas SEO con recomendaciones accionables | Ver si Brújula aparece en búsquedas de "precios mayoristas" |
| 2 | `/ai-seo` | Optimizar contenido para aparecer en respuestas de LLMs (ChatGPT, Claude, Gemini) | Cuando haya contenido público sobre precios mayoristas |
| 3 | `/programmatic-seo` | Crear páginas SEO a escala usando templates y datos (por keywords, ubicaciones) | Ej: "Precios Maxiconsumo semana del 14/05" — 1 página por semana |
| 4 | `/schema-markup` | Agregar o corregir schema markup y structured data para rich results en Google | Cuando haya una landing pública indexable |
| 5 | `/site-architecture` | Planificar jerarquía de páginas, navegación y estructura de URLs | Si se crean páginas públicas adicionales a la app |
| 6 | `/aso-audit` | Auditar y optimizar listings en App Store o Google Play | Cuando haya app mobile (Fase 2+) |
| 7 | `/web-artifacts-builder` | Suite de herramientas para crear artefactos multi-componente en React/Tailwind | Crear demos o páginas de presentación rápidas |

---

### CATEGORÍA 5 — ANÁLISIS Y ESTRATEGIA

Skills para entender el mercado y tomar mejores decisiones.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/competitor-profiling` | Investigar y perfilar competidores a partir de sus URLs | Analizar PreciosClaros u otros comparadores similares |
| 2 | `/competitor-alternatives` | Crear páginas de comparación vs competidores para SEO y ventas | "Brújula vs PreciosClaros — qué sirve para almaceneros" |
| 3 | `/marketing-ideas` | Generar ideas de marketing y crecimiento para SaaS — punto de partida cuando no se sabe por dónde empezar | Cuando se acaben las ideas de outreach |
| 4 | `/revops` | Diseñar operaciones de revenue y lifecycle management de leads | Cuando haya un equipo de ventas real (Fase 2+) |

---

### CATEGORÍA 6 — TÉCNICO NEXT.JS Y VERCEL

Skills para el stack frontend del proyecto.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/next-best-practices` | Best practices de Next.js: file conventions, RSC boundaries, datos, metadata, imágenes/fuentes | Revisar que el frontend siga las mejores prácticas |
| 2 | `/next-cache-components` | Next.js 16 Cache Components: PPR, `use cache`, cacheLife, cacheTag, updateTag | Optimizar performance del catálogo (muchos productos) |
| 3 | `/next-upgrade` | Actualizar Next.js a la última versión siguiendo migration guides y codemods | Cuando salga una versión nueva de Next.js |
| 4 | `/vercel-react-best-practices` | Performance y best practices de React/Next.js según Vercel Engineering | Optimizar carga de la app |
| 5 | `/vercel-composition-patterns` | Patrones de composición React para componentes flexibles y escalables | Cuando un componente se vuelve muy complejo |
| 6 | `/vercel-react-view-transitions` | Implementar animaciones nativas con la View Transition API de React | Animaciones de navegación entre vistas |
| 7 | `/vercel-react-native-skills` | Best practices de React Native y Expo para apps mobile | Cuando haya app mobile (Fase 2+) |
| 8 | `/vercel-cli-with-tokens` | Deploy y gestión de proyectos en Vercel con autenticación por token via CLI | Deploy manual desde terminal |
| 9 | `/deploy-to-vercel` | Deploy de aplicaciones y sitios web a Vercel | Deploy de Brújula |

---

### CATEGORÍA 7 — HERRAMIENTAS IA Y SDK

Skills para construir con Claude y el ecosistema de IA.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/claude-api` | Construir, debuggear y optimizar apps con la API de Claude / Anthropic SDK | Cuando se integre IA en Brújula (Fase 2) |
| 2 | `/mcp-builder` | Crear MCP servers (Model Context Protocol) para que Claude interactúe con APIs externas | Crear un MCP de Brújula para uso interno |
| 3 | `/skill-creator` | Crear skills nuevas, mejorar skills existentes, medir performance de skills | Automatizar flujos nuevos que se repiten |
| 4 | `/full-output-enforcement` | Forzar que Claude genere código completo sin truncar ni poner placeholders | Cuando Claude pone "...resto del código..." |
| 5 | `/webapp-testing` | Interactuar y testear apps web locales con Playwright | Alternativa a qa-verificador para testing local |

---

### CATEGORÍA 8 — BASE DE DATOS (Fase 1)

Skills para cuando se agregue Supabase.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/supabase` | Trabajar con Supabase: Database, Auth, Edge Functions, Realtime, Storage, Vectors | Cuando llegue la Fase 1 y se migre de localStorage a Supabase |
| 2 | `/supabase-postgres-best-practices` | Optimización de performance y best practices de Postgres para Supabase | Junto con la skill anterior, en Fase 1 |

---

### CATEGORÍA 9 — DOCUMENTOS Y ARCHIVOS

Skills para generar o manipular documentos.

| # | Skill | Descripción | Cuándo usarla en Brújula |
|---|---|---|---|
| 1 | `/docx` | Crear, leer, editar o manipular documentos Word (.docx) | Exportar reportes de precios a Word (Fase 2) |
| 2 | `/pdf` | Leer/extraer/crear PDFs, OCR, agregar marcas de agua, encriptar | Exportar catálogo de precios en PDF para comerciantes |
| 3 | `/xlsx` | Abrir, leer, editar o crear archivos Excel (.xlsx, .xlsm, .csv) | Ya se usa para CODIGOS.xlsx y FAMILIAS_CUSTOM.xlsx |
| 4 | `/pptx` | Crear, leer, editar o combinar presentaciones PowerPoint (.pptx) | Presentación de Brújula para inversores o socios (Fase 2) |
| 5 | `/doc-coauthoring` | Guiar un workflow estructurado para co-autoría de documentación | Documentar procesos internos de Brújula |
| 6 | `/video` | Crear o producir contenido de video con herramientas de IA | Video demo de la app para Instagram/TikTok |
| 7 | `/slack-gif-creator` | Crear GIFs animados optimizados para Slack | No aplica en Fase 0 |

---

## REGLAS DE PROCESO — Comportamiento obligatorio de Claude

Viven en `.claude/rules/`. Claude las lee al inicio de cada sesión.

| Archivo | Qué establece |
|---------|--------------|
| `00-facu.md` | Perfil de Facu, rol Jarvis, comportamiento esperado |
| `01-proyecto.md` | Qué es Brújula, MVP, señales de desvío, guardrails |
| `02-scrapers.md` | Estándares de output, credenciales, anti-bloqueo |
| `03-contexto.md` | Gestión de tokens, cuándo usar Haiku/Sonnet/Opus |
| `04-protocolo.md` | Bucle verificador, Git worktrees, workflow de voz |
| `05-autoreview.md` | **Auto-review antes de declarar terminado** — 6 criterios obligatorios que Claude debe correr antes de decir "listo", ExitPlanMode, o "terminé". Incluye declaración visible del checklist. |
| `code-style.md` | TypeScript, Python, comentarios, Windows/encoding |
| `docs/frontend/react.md` | Stack React, estructura de componentes, animaciones (carga bajo demanda: leer al tocar UI) |
| `docs/frontend/styles.md` | Tailwind v4, design tokens, dark mode, accesibilidad (carga bajo demanda: leer al tocar UI) |
| `security.md` | Credenciales, git, scrapers, frontend, validación |
| `testing.md` | Bucle verificador universal (no solo scrapers) |

---

## GUÍA DE PROMPTING — Cómo hablarle a Claude

### Regla básica: contexto + tarea + restricciones

**Mal prompt:** "mejorá la vista de perfil"
**Buen prompt:** "mejorá la sección Mi Plan en vista-cuenta.tsx usando los principios de paywall-upgrade-cro — mantené el mismo diseño, no agregues Tailwind, y el CTA debe ir a WhatsApp"

### Cuándo usar skill vs agente vs mensaje directo

| Si necesitás... | Usá... |
|---|---|
| Ejecutar un flujo repetitivo (scraping, outreach, verificación) | Skill (`/nombre`) |
| Una tarea larga que no debería contaminar el contexto (auditoría, QA) | Agente ("Actúa como el agente en...") |
| Una consulta, pregunta, o tarea de código puntual | Mensaje directo — sin skill ni agente |

### Forzar un rol específico

"Analiza esto como el PM Implacable" → Claude filtra por revenue primero.
"Miralo desde UX" → Claude piensa como el comerciante de barrio.
"Hacé los números" → Claude activa el modo CFO.

### Cómo pedir código sin que Claude se vuelva loco

- Ser específico sobre el archivo: "en `vista-cuenta.tsx`, en la sección Mi Plan..."
- Especificar el stack: "sin Tailwind, inline styles como el resto del archivo"
- Especificar restricciones: "no cambies la interfaz BrujulaConfig"
- Pedir solo lo necesario: "solo el botón CTA, no reescribas toda la sección"

### El prompt de brain dump (cuando tenés todo mezclado)

Escribís todo lo que tenés en la cabeza sin orden, pegás el texto y escribís `/brain-dump`. Claude lo clasifica y ordena por vos.

---

## CÓMO MANTENER ESTE ARCHIVO

Regla simple: **si cambia una herramienta, cambia este archivo.**

- **Creás un skill del proyecto** → agregarlo en "SKILLS DEL PROYECTO" con descripción, cuándo usarlo y archivo.
- **Mejorás un skill** → actualizar la descripción si cambió el comportamiento.
- **Eliminás un skill** → borrarlo de acá también.
- **Creás un agente nuevo** → agregarlo en AGENTES con cómo invocarlo.
- **Cambia un flujo** → actualizar la sección FLUJOS.

El agente `limpiador` actualiza este archivo después de cada limpieza. En otras sesiones, actualizarlo manualmente como parte de `/cerrar-sesion`.
