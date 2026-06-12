# Regla: Calidad de datos del catálogo

## Regla de oro (12/06/2026): ningún fallback puede alterar metadata de frescura

`_fallback_mc_desde_catalogo()` pisaba `fecha_scraping` con la fecha de hoy "para que el
stale-detection no los marque". Resultado: el scraper MC falló 14 días seguidos en Railway
y 5.128 precios del 28/05 circularon como frescos hasta que Facu los detectó a ojo.

- Un fallback SIEMPRE conserva la fecha real del dato que recicla.
- Si un dato parece fresco, verificar contra la FUENTE (web del mayorista), no contra
  su propia metadata — la fecha del catálogo puede mentir si algún paso la reescribe.
- Señal de reciclaje: precios de una fuente 100% idénticos entre dos corridas separadas
  por días (con inflación, imposible). Test: comparar output viejo vs catálogo actual.
- Diferencia sistemática de ~3% exacta entre nuestra app y el portal logueado del
  comerciante = percepciones IIBB según CUIT del cliente, NO error de scraping.

## Errores documentados (28/05/2026)

### Error 1 — encontrar_mejor priorizaba cantidad sobre recencia
`actualizar_catalogo.py` elegía el archivo con más productos válidos, ignorando la fecha.
Resultado: si el scraper de ayer tenía 2 productos más que el de hoy, se usaba el de ayer.
**Fix aplicado:** nuevo criterio de 5% de tolerancia — si el archivo más reciente está dentro
del 5% del score máximo, gana el más reciente.

### Error 2 — Precios stale en catálogo sin indicador
Productos con precio de hace >30 días aparecían como información vigente en el frontend.
Ejemplo: Cerveza Quilmes Yaguar $1.410 del 20/04 (38 días viejo) mostrada como precio actual.
**Fix aplicado:** `actualizar_catalogo.py` ahora agrega `precio_stale: true` y
`dias_desde_scraping: N` en la fuente del producto cuando la fecha supera 30 días.

## Cómo usar precio_stale en el frontend

En `BRUJULA-DE-PRECIOS/lib/data.ts` y las vistas del catálogo:
- Si `fuente.precio_stale == true` → mostrar el precio con indicador visual (gris, tachado, o
  badge "desactualizado") en lugar de precio vigente
- No usar precios stale en el cálculo de "mejor precio" ni en el ranking de bombas

## Señales de alerta para detectar precios incorrectos

- Ahorro cross-mayorista >60%: investigar antes de mostrar como bomba real
- `fecha_scraping` de hace >30 días: el precio puede no reflejar la realidad
- Productos donde nombre_yaguar o nombre_maxiconsumo están vacíos pero hay precio de ese
  mayorista: el match fue fuzzy no confirmado — riesgo de falso positivo

## Frecuencia recomendada de scraping

- MaxiCarrefour: cookies duran ~30 días → scraper cada 7 días ideal
- Yaguar: scraper cada 7 días (libre, sin auth)
- Maxiconsumo: scraper cada 7 días (libre con curl_cffi)
