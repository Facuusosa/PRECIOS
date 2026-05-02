# Skill: Pre-Launch Check

Auditoría completa antes de salir a comercializar. Orquesta pipeline, auditor técnico, verificación de bombas y QA en producción. Usar con `/pre-launch-check`.

## Cuándo usar
- Antes de enviar cualquier lote de WhatsApps/outreach
- Después de renovar cookies de MaxiCarrefour
- Una vez por semana como chequeo de salud del sistema

## Pasos

### 1. Verificar antigüedad del catálogo
```bash
python -c "
import json, os
from datetime import datetime
from pathlib import Path
cat = Path('BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json')
edad_horas = (datetime.now() - datetime.fromtimestamp(cat.stat().st_mtime)).total_seconds() / 3600
print(f'Catalogo: {edad_horas:.0f}hs de antiguedad')
print('OK' if edad_horas < 24 else 'DESACTUALIZADO - correr pipeline primero')
"
```
Si el catálogo tiene >24hs → correr `/pipeline-datos` antes de continuar.

### 2. Auditoría técnica
Invocar: "Actúa como el agente definido en `.claude/agents/auditor.md` y auditá el proyecto completo"

Esperar el reporte. Si hay items CRÍTICO → corregir antes de continuar.

### 3. Verificación de precios de bombas
```bash
python scripts/verificar_bombas.py 10
```
- 8/10 OK → continuar
- <8/10 OK → investigar qué mayorista falla → correr su scraper → reintentar

### 4. QA en producción
Invocar: "Actúa como el agente definido en `.claude/agents/qa-verificador.md` y verifica la app en https://v0-brujula-de-precios.vercel.app"

Esperar el reporte. Si hay vistas ROJO → corregir antes de continuar.

### 5. Generar reporte go/no-go
```bash
python -c "
import json
from datetime import datetime
from pathlib import Path

cat = Path('BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json')
with open(cat, encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
multi = sum(1 for p in data if sum(1 for v in p['precios'].values() if v and v > 0) >= 2)
print(f'Total productos: {total:,}')
print(f'Con 2+ precios: {multi:,} ({100*multi/total:.1f}%)')
print(f'Catalogo actualizado: {datetime.fromtimestamp(cat.stat().st_mtime).strftime(\"%d/%m/%Y %H:%M\")}')
"
```

Guardar el reporte en `reports/pre_launch_YYYYMMDD.md` con:
- Fecha y hora
- Resultado de cada paso (OK/FAIL)
- Counts del catálogo
- Decisión: GO / NO-GO

## Criterio GO (todos deben cumplirse)
- Catálogo con <24hs de antigüedad
- Auditor: sin items CRÍTICO
- Bombas: ≥8/10 verificadas OK
- QA: ≥4/5 vistas VERDE
- Total productos: >10,000

## Criterio NO-GO (cualquiera bloquea)
- Catálogo desactualizado >48hs
- Credencial hardcodeada detectada (CRÍTICO en auditor)
- Calculadora de margen ROJA en QA
- <60% de bombas verificadas

## Si sale GO
```bash
# Deploy con datos frescos (si cambiaron desde el último deploy)
cd BRUJULA-DE-PRECIOS
git add data/processed/catalogo_unificado.json
git commit -m "data: actualizacion manual YYYY-MM-DD"
git push origin main
# Vercel se redeploya automáticamente via webhook GitHub
```
Luego continuar con `/enviar-outreach` para el primer lote de WhatsApps.
