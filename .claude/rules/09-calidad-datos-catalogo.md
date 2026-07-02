# Regla: Calidad de datos del catálogo

## Cache público de Yaguar ≠ precio real (01/07/2026 — caso Fernet Branca 750)

Síntoma: Facu (anónimo, browser real) veía $17.772 en la ficha de Yaguar; el catálogo
decía $15.131. Medido con test A/B: la vista anónima venía de Cloudflare con
`cf-cache-status: HIT, age=217.422s` (2.5 días) — precio VIEJO cacheado. El server real
(`BYPASS`, y también la vista logueada — confirmado por Facu logueándose) da $15.131.

- **El precio real de Yaguar es el del server/logueado, NO el de la vista pública anónima**
  (que puede estar cacheada días). El scraper entra logueado → captura el real. Correcto.
- Si un usuario reporta "Yaguar muestra otro precio": preguntar si está logueado ANTES de
  tocar nada. Anónimo + precio distinto = casi seguro cache viejo de Cloudflare.
- Test rápido para confirmar: request con cookie `wordpress_logged_in_test=test` (bypasea
  cache) vs request anónimo puro; mirar `cf-cache-status` y `age` en los headers.
- Mejora pendiente (encolada, no urgente): "modo percepción" en el verificador — leer
  también la vista anónima cacheada y reportar productos donde cache ≠ server, para saber
  qué precios van a confundir a comerciantes que navegan sin loguearse.

## Matching de cantidad: comparar SIEMPRE en cantidad canónica (13/06/2026)

Síntoma reportado por Facu: "mi página muestra una cosa y el link del mayorista muestra
otra". Causa raíz verificada (caso Agua Glaciar): la app mostraba 1.5L a $1.700 pero el
link de Maxiconsumo iba a Glaciar **2L** a $1.405 — fuente mal matcheada a otro tamaño.

El `Paso 6d` de `actualizar_catalogo.py` dejaba pasar 75 casos así (Yaguar 35, MaxiCarrefour
24, Maxiconsumo 16) por dos fallas: (1) umbral `ratio >= 2.0` — Glaciar 1.5↔2L es 1.33x y no
se detectaba; (2) extracción de números con `_QTY_RE` sobre `clave_nombre`, que no entiende
`L`/`LT` ni decimales.

**Fix aplicado:** `_cantidad_canonica()` extrae del nombre CRUDO (no `clave_nombre`) y
normaliza volumen->ml y peso->g. El 6d ahora elimina la fuente si difiere >10% del ancla en
la misma dimensión. El 10% tolera ruido de parsing (950↔930ml = 2%) sin dejar pasar tamaños
distintos. Resultado: 103 fuentes incompatibles eliminadas, casos fuente-vs-fuente a 0.

- Para comparar tamaños SIEMPRE normalizar a unidad canónica; nunca comparar "números
  compartidos" en el string (2L y 2u comparten el 2 y no son lo mismo).
- Quedan ~34 casos display-vs-fuente: el PRECIO es correcto (las fuentes coinciden entre sí)
  pero el `nombre_display` está mal escrito (ej. Quitamanchas "1.5 ml" debió ser "1.5 L") o
  expresa la cantidad distinto (Bon o Bon "18u x 15g" = 270g). Es cosmético, no de precio.

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
