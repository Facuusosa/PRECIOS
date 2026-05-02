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

## SKILLS

### /status-proyecto
**Qué hace:** Semáforo de 30 segundos — Yaguar / MaxiCarrefour / Maxiconsumo / Catálogo / Cookies CF / Deploy. Estado VERDE/AMARILLO/ROJO por componente con próximos 3 pasos concretos.
**Cuándo:** Al inicio de cada sesión.
**Archivo:** `.claude/skills/status-proyecto.md`

---

### /pipeline-datos
**Qué hace:** Corre los 3 scrapers en orden (Yaguar → MaxiCarrefour → Maxiconsumo), verifica counts mínimos (Y>3000, C>3000, M>500), confirma que `catalogo_unificado.json` se actualizó.
**Cuándo:** Una vez por semana o cuando el catálogo tiene más de 3 días.
**Archivo:** `.claude/skills/pipeline-datos.md`

---

### /investigar-y-contactar
**Qué hace:** Para un comercio específico — busca en Google/Facebook quiénes son, extrae ejemplos de precios relevantes para su tipo de negocio, redacta mensaje personalizado (tono cálido, sin marketing), muestra borrador, espera aprobación, crea draft Gmail o genera texto para WhatsApp.
**Cuándo:** Cuando hay comercios para contactar. Procesar de a 5 por sesión.
**Archivo:** `.claude/skills/investigar-y-contactar.md`
**Nota:** Este es el skill más importante para generar ingresos. Priorizar siempre.

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

### /railway-deploy
**Qué hace:** Configura y administra scrapers en Railway (Hobby $5/mes ya contratado). Subcomandos: `setup` / `status` / `logs` / `trigger`. Cron configurado: 6am UTC diario.
**Cuándo:** Solo para setup inicial o troubleshooting cuando el pipeline en Railway falla.
**Archivo:** `.claude/skills/railway-deploy.md`

---

### /actualizar-familias
**Qué hace:** Detecta pack mixing en el catálogo, sugiere FAMILIAs nuevas usando `analizar_familias.py`, aplica sugerencias de alta confianza automáticamente, re-corre el catálogo y reporta mejora en tasa de matching.
**Cuándo:** Cuando la tasa de matching baja o cuando se sospecha que hay productos del mismo tipo que no se están comparando.
**Requiere:** `analizar_familias.py` + `data/raw/FAMILIAS_CUSTOM.xlsx` en el proyecto.
**Archivo:** `.claude/skills/actualizar-familias.md`

---

### /buscar-comercios
**Qué hace:** Busca kioscos, almacenes y minimercados en una zona específica via WebSearch, estructura los resultados y los guarda en `data/outreach/comercios_[zona]_[fecha].json`.
**Cuándo:** Cuando se necesita ampliar la lista de prospectos para outreach.
**Base de contactos:** `data/outreach/comercios_*.json` (el xlsx original fue borrado).
**Archivo:** `.claude/skills/buscar-comercios.md`

---

### /verificar-app
**Qué hace:** Check rápido de la app en producción con Puppeteer — verifica Inicio, Catálogo, Calculadora y Lista. Sin precios hardcodeados, solo verifica que los componentes carguen y funcionen.
**Cuándo:** Post-deploy rápido o antes de enviar mensajes a comercios.
**Diferencia con qa-verificador:** Este skill es rápido y devuelve resultado al contexto. El agente `qa-verificador` hace QA completo y escribe un reporte a `data/quality/` sin contaminar el contexto.
**Archivo:** `.claude/skills/verificar-app.md`

---

### /bucle-optimizador
**Qué hace:** Audita código, datos y frontend buscando mejoras con ROI. Propone top 3 oportunidades ordenadas por Impacto × Facilidad. En modo loop (via `/loop`), solo escribe en `audit_log.md` sin implementar — Facu revisa y aprueba.
**Cuándo:** Cuando hay tiempo para mejoras no urgentes o para encontrar cuellos de botella no obvios.
**Nota:** `audit_log.md` actualmente vacío — nunca se corrió en modo loop.
**Archivo:** `.claude/skills/bucle-optimizador.md`

---

## AGENTES

Los agentes son subagentes que corren fuera del contexto principal. Consumen más tokens que los skills pero protegen el contexto de resultados grandes.

### auditor
**Qué hace:** Auditoría profunda del proyecto completo — salud del catálogo, scrapers, frontend (errores TypeScript), seguridad (credenciales hardcodeadas), deuda técnica. Output estructurado: CRÍTICO / ATENCIÓN / OK. Termina siempre con un próximo paso concreto.
**Cuándo:** Antes de releases importantes, cuando hay dudas de calidad, o cuando algo raro está pasando.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/auditor.md` y auditá el proyecto completo"
**Archivo:** `.claude/agents/auditor.md`

---

### auditor-catalogo
**Qué hace:** QA específico de los datos del catálogo — detecta matches incorrectos (ratio >3x entre fuentes), precios fuera de rango ($300-$300k), duplicados por nombre similar. Si el usuario reporta un producto incorrecto, lo valida y sugiere agregar el EAN a `CODIGOS.xlsx`.
**Cuándo:** Cuando un usuario reporta un precio incorrecto, después de cada corrida del unificador, antes de cada deploy.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/auditor-catalogo.md` y auditá el catálogo"
**Archivo:** `.claude/agents/auditor-catalogo.md`

---

### qa-verificador
**Qué hace:** QA completo de la app en producción con Puppeteer. Navega todas las vistas, verifica calculadora de margen, detecta errores JS, **escribe el reporte a `data/quality/qa-reporte-[fecha].md`** (no al contexto principal). Devuelve solo el resumen al agente principal.
**Cuándo:** Como parte de `/pre-launch-check` o cuando se necesita evidencia documentada del estado de la app.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/qa-verificador.md` y verifica la app en [URL]"
**Archivo:** `.claude/agents/qa-verificador.md`

---

### limpiador
**Qué hace:** Limpieza y mantenimiento del proyecto en dos modos: **AUTO** (borra sin preguntar lo que es 100% seguro: `__pycache__`, JSON vacíos, archivos debug/test, entradas git huérfanas, carpetas vacías) + **REVIEW** (muestra reporte y pide confirmación por categoría para outputs viejos, archivos huérfanos, referencias rotas en skills, docs desactualizados). Al terminar, actualiza este archivo.
**Cuándo:** Cuando el proyecto acumula basura. Recomendado: una vez por mes o después de sprints de desarrollo intenso.
**Cómo invocar:** "Actúa como el agente definido en `.claude/agents/limpiador.md` y limpiá el proyecto"
**Archivo:** `.claude/agents/limpiador.md`

---

## CÓMO MANTENER ESTE ARCHIVO

Regla simple: **si cambia una herramienta, cambia este archivo.**

- **Creás un skill nuevo** → agregarlo en la sección SKILLS con descripción, cuándo usarlo y archivo.
- **Mejorás un skill** → actualizar la descripción si cambió el comportamiento. Agregar nota si cambiaron los requisitos.
- **Eliminás un skill** → borrarlo de acá también.
- **Creás un agente nuevo** → agregarlo en AGENTES con cómo invocarlo.
- **Cambia un flujo** → actualizar la sección FLUJOS.

El agente `limpiador` es responsable de actualizar este archivo después de cada limpieza. En otras sesiones, actualizarlo manualmente como parte de `/cerrar-sesion`.
