# Skill: /railway-deploy
## Descripcion
Configura y administra el deployment de scrapers en Railway. Convierte el pipeline local (correr scrapers manualmente) en un cron job automatico en la nube. Railway plan Hobby ($5/mes) ya contratado.

## Casos de uso
- `/railway-deploy setup` → configurar Railway por primera vez
- `/railway-deploy status` → verificar que los crons estan corriendo
- `/railway-deploy logs` → ver output del ultimo run
- `/railway-deploy trigger` → forzar un run manual del pipeline

## Pasos — Setup inicial (solo la primera vez)

### 1. Crear railway.toml en la raiz del proyecto
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "echo Railway listo"

[[services]]
name = "pipeline-scraper"
```

### 2. Crear script de pipeline para Railway
Archivo: `railway_pipeline.py`
- Corre los 3 scrapers en secuencia
- Actualiza el catalogo
- Sube el JSON resultante a Vercel via API (o guarda en Railway volume)
- Loguea resultado con timestamp

### 3. Configurar cron en Railway
En el dashboard de Railway:
- Nuevo servicio → Cron Job
- Command: `python railway_pipeline.py`
- Schedule: `0 6 * * *` (6am todos los dias)
- Variables de entorno: copiar del .env local

### 4. Variables de entorno a configurar en Railway
```
YAGUAR_USERNAME=
YAGUAR_PASSWORD=
CARREFOUR_PHPSESSID=
CARREFOUR_CF_CLEARANCE=
PYTHONUTF8=1
```

## Verificacion post-setup
1. Hacer trigger manual desde Railway dashboard
2. Ver logs → confirmar que los 3 scrapers corrieron
3. Confirmar que catalogo_unificado.json tiene datos frescos
4. Si falla → revisar variables de entorno primero (99% de los casos)

## Importante
- Las cookies de MaxiCarrefour (PHPSESSID + CF_CLEARANCE) expiran cada ~30 dias
- Renovarlas en Railway dashboard cuando expiren (misma fecha que en .env local)
- Maxiconsumo necesita curl_cffi con impersonate="safari15_3" — verificar que el pip install incluye esa dependencia
- Los outputs con timestamp van a /tmp en Railway (no persisten entre runs) — el catalogo actualizado debe subirse a algun storage

## Para el catalogo actualizado
Opciones para que el frontend de Vercel acceda al catalogo fresco:
1. **Railway Volume** → Railway guarda el JSON, frontend lo consume via URL publica
2. **GitHub push** → pipeline hace commit del JSON al repo → Vercel auto-redeploy
3. **Vercel API** → subir el JSON directo via Vercel Blob Storage API

Opcion 2 (GitHub push) es la mas simple para empezar.
