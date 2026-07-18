# Regla: Agentes y subagentes — cómo ejecutar correctamente

## Error documentado (27/05/2026)
Agentes lanzados para correr scrapers usaron `Monitor` en lugar de `Bash`.
Resultado: scrapers nunca corrieron, agentes reportaron "monitoreando..." sin output real.

## Regla fija

### Para correr scripts Python o comandos shell desde un agente:
- SIEMPRE usar la herramienta `Bash` con el comando directo
- NUNCA usar `Monitor` para correr scripts — Monitor solo sirve para observar procesos ya iniciados por Bash con `run_in_background: true`
- Si el script tarda mucho, usar `Bash` con `run_in_background: true` + `timeout` generoso

```python
# CORRECTO
Bash(command="cd 'ruta' && python script.py", timeout=1800000)

# INCORRECTO
Monitor(...)  # no lanza nada, solo observa
```

### Para verificar resultado post-ejecución:
1. Leer el archivo output generado con `Glob` + `Read`
2. NO asumir que el script corrió si no hay archivo con timestamp de hoy
3. Si no hay archivo → el script NO corrió, relanzar con Bash

### Al lanzar agentes para scrapers desde el agente principal:
- Prompt del subagente debe decir explícitamente: "usar Bash tool, NO Monitor"
- Incluir el comando exacto a ejecutar
- Incluir el path esperado del output para verificación

## Cuándo usar Monitor
Solo para observar en tiempo real el output de un proceso que YA está corriendo en background.
Ejemplo correcto:
```
Bash(command="python script.py", run_in_background=True)
→ Monitor(path=output_file)  # ahora sí tiene sentido
```

## Error documentado (06/07/2026) — agentes que cortan el turno con el proceso vivo

Al lanzar agentes (Haiku) para scrapers de Maxiconsumo y Coto con instrucción de usar
`run_in_background=True` + `Monitor`, **dos de dos agentes terminaron su turno y notificaron
"completado" mientras el proceso seguía corriendo** (sin archivo output del día generado
todavía). El reporte final decía literalmente "esperando que termine" o "estoy monitoreando" —
la tarea NO estaba terminada pero el agente cerró el turno igual.

**Regla fija:** el agente principal NUNCA da por bueno un reporte de subagente sin verificar el
archivo real (esto ya estaba en `08-subagentes-verificacion.md`, se reconfirma acá). Si el
archivo con timestamp de hoy no existe:
1. Verificar con `tasklist | grep -i python` (o equivalente) si el proceso sigue vivo.
2. Si sigue vivo → NO relanzar el scraper (crearía un segundo proceso concurrente escribiendo
   al mismo archivo — ver incidente de corrupción de Carrefour retail abajo). Usar `SendMessage`
   para reanudar el mismo agente y decirle explícitamente que NO cierre el turno hasta leer el
   archivo output real.
3. Si `Monitor` no logra que el agente espere (pasó 2 veces seguidas con Coto), instruir en su
   lugar un `Bash` **bloqueante** (sin `run_in_background`) que haga polling del archivo
   (`until ls archivo 2>/dev/null; do sleep 15; done`) con timeout amplio — un Bash bloqueante
   no permite que el agente "siga de largo" como sí puede pasar con Monitor.

## Riesgo derivado: doble proceso concurrente corrompe el output JSON

El mismo día, `output_carrefour_*.json` apareció con basura pegada al final (`json.loads`
fallaba con "Extra data", aunque el array principal era íntegro — recuperable con
`json.JSONDecoder().raw_decode()`). Con ~10 `python.exe` corriendo cuando debían ser ~4, todo
indica que el agente relanzó el mismo scraper una segunda vez sin darse cuenta de que el primero
seguía vivo, y dos `open(path, "w")` concurrentes se pisaron. No tocar el scraper (el `open("w")`
es correcto) — el fix es de proceso: antes de relanzar cualquier scraper, verificar con
`tasklist`/`Get-Process` que no haya una instancia ya corriendo.

## Las skills del PROYECTO no se invocan con la tool `Skill` (16/07/2026)

Intentar `Skill(skill: "cerrar-sesion")` (o cualquier otra skill propia de Brújula listada en
`HERRAMIENTAS.md`: `status-proyecto`, `pipeline-datos`, etc.) falla con "Unknown skill" — la
tool `Skill` solo conoce las skills nativas del SDK (`artifact-design`, `impeccable`, etc.),
no los archivos sueltos de `.claude/skills/*.md` del proyecto. Esos se activan cuando el
usuario tipea `/nombre` directo en la CLI (el harness expande el archivo como contexto),
NO son invocables programáticamente por Claude durante la sesión.

**Cómo aplicar:** si Facu pide correr una skill del proyecto, leer el archivo
`.claude/skills/[nombre].md` con la tool `Read` y seguir sus pasos manualmente — no intentar
`Skill(...)` con esos nombres, va a fallar.

## Puppeteer pierde el estado (localStorage) si cambian las `launchOptions` (16/07/2026)

Cada llamada a `puppeteer_navigate` con `launchOptions` distintas a la anterior reinicia el
browser completo (documentado en la propia tool: "If changed and not null, browser restarts").
Si se navega una vez con `{"headless": false, "defaultViewport": null}` para tener una ventana
visible y persistente, y despues se hace otro `navigate` sin especificar `launchOptions` (o con
otras), se pierde el localStorage — pasó 3 veces en una sesión armando una lista de productos,
cada vez hubo que reconstruir desde cero.

**Cómo aplicar:** una vez elegidas las `launchOptions` para una sesión de trabajo con estado
persistente (ej. una lista en "Mi Lista"), repetirlas IDÉNTICAS en cada `navigate` posterior
hasta terminar esa tarea.

## No usar `Read` sobre resultados de tools que devuelven JSON gigante (16/07/2026)

Un resultado de `puppeteer_evaluate` que lee `localStorage` completo (con imágenes, links,
etc.) puede pesar 60-70KB — leerlo con la tool `Read` para pasarlo a otro lado quema decenas
de miles de tokens de contexto de una sola vez, sin necesidad real de "ver" ese contenido.

**Cómo aplicar:** si hace falta extraer/reconstruir datos desde un archivo de resultado
grande, usar `Bash`/`python3` para parsearlo y escribir el resultado a otro archivo
directamente — nunca `Read` el archivo completo en el contexto de la conversación solo para
volcarlo a otro lado.

## `taskkill //IM` por nombre de proceso mata también las apps reales del usuario (17/07/2026)

Al limpiar un Chrome headless que se lanzó manualmente (vía `chrome.exe --headless
--screenshot=...` para rasterizar un SVG a PNG, sin pasar por Puppeteer), se cerró con
`taskkill //F //IM chrome.exe //T` para "limpiar". Ese comando mata **todas** las instancias
de `chrome.exe` del sistema — si Facu tenía el navegador real abierto con pestañas, se cerraron
de golpe sin guardarlas. Mismo riesgo aplica a `node.exe`, `python.exe`, etc.: cualquier proceso
que el usuario pueda tener corriendo por su cuenta.

**Cómo aplicar:** para matar un proceso que YO lancé (headless Chrome, un scraper, un server de
dev), targetear el PID exacto devuelto al lanzarlo (`Start-Process` guarda `.Id`, o `tasklist`
filtrado por línea de comando/hora de inicio) — nunca `taskkill //IM <nombre>` ni
`Stop-Process -Name` a secas cuando el proceso puede tener instancias del usuario corriendo.
Si no se puede aislar el PID con certeza, preguntar antes de matar por nombre.
