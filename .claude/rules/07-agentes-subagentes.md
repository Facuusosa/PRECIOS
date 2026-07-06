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
