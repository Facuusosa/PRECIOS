# Regla: Precios de productos sin stock en Maxiconsumo

## El problema documentado (28/05/2026)

Maxiconsumo muestra precios incluso para productos en "disponibilidad crítica" (sin stock).
El scraper captura ese precio igual que cualquier otro. El catálogo lo muestra como válido y comparable.

Caso concreto: Queso Rallado La Paulina x40 → precio en catálogo $4.809 vs Yaguar $1.539 y Carrefour $1.569.
El producto estaba sin stock en Maxiconsumo al momento del scraping. El precio es 3x el de la competencia.

## Por qué pasa

1. `scraper_pro.py` hardcodea `stock: True` — nunca valida disponibilidad real
2. `enriquecer_precios.py` no detecta el estado de la página (stock vs sin stock)
3. `actualizar_catalogo.py` tiene lógica de "precio stale" (línea ~1771) pero solo marca flag, no descarta
4. No hay fecha de captura por fuente propagada al catálogo para Maxiconsumo

## Señales de alerta automática a implementar

Cuando en `actualizar_catalogo.py` se procesa un precio de Maxiconsumo, marcarlo como sospechoso si:
- El precio MC es > 2x la mediana de las otras fuentes con precio > 0
- El producto no tiene `fecha_scraping` en la fuente Maxiconsumo
- El precio de MC es > 0 pero el producto estaba en "disponibilidad crítica" en la web

## Fix pendiente en scraper_pro.py

En `parsear_pagina()` (línea 77), después de extraer el precio, buscar indicador de sin stock:
```python
# Detectar disponibilidad crítica: buscar texto o clase CSS en el item
sin_stock = bool(item.find(string=re.compile(r"disponibilidad cr[ií]tica", re.IGNORECASE)))
# Guardar en el producto para que actualizar_catalogo.py pueda filtrarlo
"stock": not sin_stock,
```

## Fix pendiente en actualizar_catalogo.py

Agregar filtro outlier antes de consolidar precios de Maxiconsumo:
- Si hay 2+ mayoristas con precio, calcular mediana
- Si el precio de MC es > 2.5x la mediana → descartarlo (poner a 0) y loguear
- Esto captura automáticamente precios de bulto mal capturados Y precios de productos sin stock

## Cómo detectar este patrón antes de que lo reporte Facu

En cada corrida de `actualizar_catalogo.py`, imprimir al final:
"PRECIOS SOSPECHOSOS MC: N productos donde precio MC > 2x mediana de otras fuentes"

Si N > 0 → revisar manualmente antes de actualizar el catálogo.
