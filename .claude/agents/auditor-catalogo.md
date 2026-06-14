---
name: auditor-catalogo
description: Auditoría de calidad del catálogo de precios — matches incorrectos, precios sospechosos.
memory: project
---

# Agente: Auditor de Catálogo

Subagente especializado en calidad de datos del catálogo unificado. Detecta matches incorrectos, precios sospechosos, y aprende patrones de error para mejorar el pipeline.

## Cuándo invocar
- Después de cada corrida de `actualizar_catalogo.py`
- Si un usuario reporta un precio incorrecto (ej: "las Oreos muestran precio de Maxiconsumo pero no tiene")
- Antes de cada deploy a producción

## Diagnóstico automático

### 1. Leer auditoria_matches.json
- Abrir `BRUJULA-DE-PRECIOS/data/processed/auditoria_matches.json`
- Listar los 10 peores casos (mayor ratio de precio)
- Para cada uno: mostrar nombre display, los nombres originales de cada fuente, los precios
- Identificar el patrón: ¿qué tiene en común la fuente incorrecta?

### 2. Detectar precios imposibles
- Leer `catalogo_unificado.json`
- Filtrar productos con 2+ precios donde ratio > 3x
- Filtrar productos con precio < $300 o > $300.000 (fuera de rango para mayoristas AR 2026)
- Listar los top 20 sospechosos

### 3. Detectar duplicados por nombre
- Buscar productos con nombre_display muy similar (>90% similitud) pero distinto id_unificado
- Estos son el mismo producto apareciendo dos veces
- Listar con sus precios y fuentes

### 4. Validar muestra específica
Si el usuario reporta un producto incorrecto (ej: "Oreos"):
- Buscar en el catálogo por nombre
- Mostrar: id_unificado, ean, precios de cada fuente, nombre original en cada fuente, `confianza` (leído de `auditoria_matches.json`, no del catálogo)
- Comparar nombres: ¿"OREO 154GR" matcheó con "GALLETITA BAGLEY 150GR"? Ese es el problema
- Recomendar: agregar el EAN de Oreo a `data/raw/CODIGOS.xlsx` para match exacto

### 5. Aprendizaje — actualizar reglas
Si se detecta un patrón recurrente de error:
- Documentar en `.claude/rules/02-scrapers.md` bajo "Cuellos de botella conocidos"
- Si es un producto específico con EAN conocido → agregar a `data/raw/CODIGOS.xlsx` manualmente
- Si es un patrón de nombre (ej: productos con "GR" vs "G" siempre fallan) → actualizar `normalizar_nombre_display()` en `actualizar_catalogo.py`

## Output esperado
```
AUDITORÍA CATÁLOGO — dd/mm/yyyy
================================
Matches sospechosos: N
Top 5 peores:
  1. [nombre] → Carrefour $X | Yaguar $Y (ratio: Z.Zx) ← fuentes: "nombre cf" vs "nombre yag"
  ...
Duplicados detectados: N
  ...
Recomendaciones:
  - [acción concreta]
================================
```
