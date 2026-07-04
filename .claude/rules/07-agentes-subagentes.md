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
