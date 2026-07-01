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

## Fixes — IMPLEMENTADOS (verificado en código el 01/07/2026)

1. **Scraper saltea sin stock**: `targets/maxiconsumo/scraper_pro.py:91-93` detecta
   "disponibilidad crítica" en el item y lo saltea directamente (no lo captura).
2. **Filtro outlier por mediana**: `actualizar_catalogo.py:1886-1902` — si el precio MC
   es > 2.5x la mediana de las otras fuentes (`OUTLIER_MC_RATIO = 2.5`), se descarta y
   se loguea "PRECIOS SOSPECHOSOS MC descartados: N". Corre en cada corrida del catálogo.
3. Existe además validación cruzada general (~línea 1439): outlier < mediana/4 o > 2.5x
   con 3 fuentes se descarta; con 2 fuentes y ratio >2.5x se marca sospechoso para revisión.

Si el log del pipeline muestra "PRECIOS SOSPECHOSOS MC descartados: N" con N alto (>20),
revisar si Maxiconsumo cambió el HTML del indicador de stock.

## Capa extra desde 01/07/2026

La verificación en vivo (`scripts/verificar_precios_real.py`, integrada como gate pre-push
en `pipeline_local.py`) compara el top 20 ABC=A contra la web real de los 3 mayoristas.
Un precio sin stock inflado que se cuele por las capas anteriores diverge contra la web
y bloquea la publicación.
