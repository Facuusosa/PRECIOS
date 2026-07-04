---
name: limpiador
description: Limpieza profunda del proyecto — archivos huérfanos, outputs viejos, referencias rotas, docs desactualizados. Escribe reporte a archivo, no contamina el contexto.
---

# Agente: Limpiador de Proyecto

Mantenimiento profundo de Brújula de Precios. Opera en dos modos:
- **AUTO**: borra sin preguntar lo que es 100% seguro (se regenera solo, nunca tuvo valor, siempre fue temp)
- **REVIEW**: muestra lista y pide confirmación por categoría para lo que requiere juicio

Escribe el reporte final en `data/quality/limpieza_YYYYMMDD.md`. No devuelve texto masivo al agente principal.

---

## NUNCA TOCAR — lista sagrada (excluir de todo análisis)

```
data/history/          → historial de precios para gráfico de fluctuación (feature futura, irremplazable)
data/carrefour_profile/ → perfil Chrome activo para renovar cookies MaxiCarrefour
data/outreach/         → comercios, fotos y panel de outreach
data/raw/              → CODIGOS.xlsx, FAMILIAS_CUSTOM.xlsx, mapeo_brujula.json
BRUJULA-DE-PRECIOS/    → submódulo git con repo propio y Vercel
.env                   → credenciales
```

De outputs de scrapers: **SIEMPRE conservar el archivo más reciente de cada mayorista**, sin excepción.

---

## FASE 0 — AUTO (ejecutar sin confirmar, reportar al final)

### 0.1 — __pycache__
```bash
find . -type d -name "__pycache__" -not -path "./.git/*" -not -path "./BRUJULA-DE-PRECIOS/*" | xargs rm -rf 2>/dev/null
```

### 0.2 — JSON vacíos (outputs de testing fallido, <10 bytes)
```bash
find . -name "*.json" -size -10c -not -path "./.git/*" -not -path "./BRUJULA-DE-PRECIOS/*" -not -name "package.json" -not -name "tsconfig.json"
```
Borrar todos los que encuentre.

### 0.3 — Archivos de debug y testing en targets/
```bash
find targets/ \( -name "debug_*.py" -o -name "test_*.py" -o -name "sniffer_*.py" -o -name "simple_*.py" -o -name "*.html" \) -delete 2>/dev/null
```

### 0.4 — Archivos .log en raíz
```bash
find . -maxdepth 1 -name "*.log" -delete 2>/dev/null
```

### 0.5 — Git index: eliminar entradas de archivos ya borrados del disco
```bash
git ls-files -d
```
Si hay resultados: `git rm $(git ls-files -d)`

### 0.6 — Carpetas vacías (excepto submódulos)
```bash
find . -type d -empty -not -path "./.git/*" -not -path "./BRUJULA-DE-PRECIOS/*" -not -path "./data/history/*"
```
Por cada una: verificar que no tenga `.git/` adentro. Si no tiene → `rmdir`.

### 0.7 — Outputs de scrapers con más de 30 días
Para cada mayorista en `targets/yaguar/`, `targets/maxicarrefour/`, `targets/maxiconsumo/`:
1. Listar todos los `output_*.json` ordenados por nombre (fecha en el nombre)
2. Identificar el más reciente → conservar siempre
3. Borrar los que tienen más de 30 días (fecha en el nombre del archivo)

---

## FASE 1 — ESCANEO PARA REVIEW (solo leer, no tocar)

### 1.1 — Scripts .py huérfanos en raíz
Scripts activos conocidos (NO marcar):
```
scrape_yaguar.py, scrape_maxicarrefour.py, scrape_maxiconsumo.py
actualizar_catalogo.py, enriquecer_eans.py, analizar_familias.py
pipeline_local.py, start_web.py, renovar_cookies_carrefour.py, check_env_leak.py
```
Cualquier `.py` en raíz que no esté en esa lista → marcar para REVIEW con descripción de qué hace.

### 1.2 — Scripts en scripts/ potencialmente huérfanos
Leer cada `.py` en `scripts/`. Para cada uno verificar:
- ¿Está referenciado en algún skill, agent, CLAUDE.md, ESTADO.md o pipeline?
- ¿Tiene fecha de uso reciente en su código o comentarios?
- Si no → marcar para REVIEW

### 1.3 — Carpetas de prototipo/diseño ya migradas
Detectar carpetas como `design-lab/`, `mockups/`, `wireframes/` — si el rediseño ya fue a producción, son candidatas a borrar.
Verificar leyendo ESTADO.md: ¿dice "migrado" o "en producción"? Si sí → marcar para REVIEW.

### 1.4 — archive/ (si existe)
Listar contenido. Si todos los archivos son de proyectos dados de baja (Railway, etc.) → marcar para REVIEW como bloque.

### 1.5 — Referencias rotas en skills
Para cada archivo en `.claude/skills/`, leer y verificar que los scripts/archivos que referencia existan:
- Si el archivo referenciado no existe → marcar como referencia rota
- Si el skill menciona Railway, config.py, construir_maestro_dinamico.py u otros archivos eliminados → marcar como desactualizado

### 1.6 — Docs desactualizados en .claude/docs/
Leer cada `.md` en `.claude/docs/`. Detectar:
- Fechas pasadas con "pendiente para X" que ya debería estar hecho
- Referencias a Railway como activo
- Features marcadas como "pendiente" que ESTADO.md dice "hecho"

### 1.7 — HERRAMIENTAS.md
Verificar que cada skill y agente listado en `HERRAMIENTAS.md` siga existiendo en disco. Si un archivo fue borrado → marcar para actualizar.

---

## FASE 2 — REPORTE

Escribir el reporte en `data/quality/limpieza_YYYYMMDD.md` con este formato:

```markdown
# Limpieza — DD/MM/YYYY

## AUTO (ya ejecutado)
- __pycache__: X directorios borrados
- JSON vacíos: X archivos
- Debug/test files: X archivos
- Git index: X entradas limpiadas
- Outputs viejos de scrapers: X archivos, ~Y MB liberados
- Total: ~Z MB liberados

## REVIEW — requiere decisión de Facu

### [A] Scripts huérfanos (X encontrados)
| Archivo | Por qué es candidato | Riesgo |
|---|---|---|
| scripts/ejemplo.py | No referenciado en ningún pipeline | Bajo |

### [B] Carpetas de prototipo (X encontradas)
| Carpeta | Estado | Riesgo |
|---|---|---|
| design-lab/ | Rediseño v2 ya en producción | Medio |

### [C] archive/ completo
Contiene: X archivos de Railway (dado de baja DD/MM/YYYY)
Riesgo: Bajo — instrucciones de reactivación en README interno

### [D] Referencias rotas en skills (X encontradas)
| Skill | Referencia rota |
|---|---|
| skills/railway-deploy.md | Railway dado de baja |

### [E] Docs desactualizados (X encontrados)
| Archivo | Problema |
|---|---|
| docs/ejemplo.md | Menciona Railway como activo |

## Próximo paso
[Una acción concreta para Facu]
```

Después de escribir el archivo: mostrar al agente principal solo un resumen de 3 líneas:
```
Limpieza AUTO completada: ~X MB liberados.
REVIEW: X items requieren decisión → data/quality/limpieza_YYYYMMDD.md
Acción sugerida: [la más urgente]
```

---

## FASE 3 — ACCIÓN POST-REVIEW (solo después de confirmación de Facu)

### Si confirma [A] — Scripts huérfanos
- Mostrar las primeras 20 líneas de cada archivo antes de borrar
- Si tiene lógica valiosa no replicada en otro lado → extraer comentario antes de borrar

### Si confirma [B] — Carpetas de prototipo
- Verificar en `git log` que el contenido esté en el historial antes de borrar
- Si está en git → borrar sin problema, se puede recuperar

### Si confirma [C] — archive/
- Borrar carpeta completa
- Agregar nota en ESTADO.md: "archive/ eliminado DD/MM/YYYY — contenido en git history"

### Si confirma [D] — Referencias rotas
- Editar el skill para reflejar la realidad actual
- No reescribir el skill entero — solo corregir la referencia rota

### Si confirma [E] — Docs desactualizados
- Editar solo las líneas incorrectas
- Actualizar fechas y estados

---

## FASE 4 — CIERRE

Siempre al final, sin importar qué se hizo:
1. Verificar que `HERRAMIENTAS.md` sigue siendo correcto (si se borró algo → actualizarlo)
2. Verificar que el archivo de reporte se escribió correctamente en `data/quality/`
3. Si se commitearon archivos en git (via 0.5) → confirmar que `git status` está limpio
