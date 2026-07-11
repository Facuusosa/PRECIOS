# ALERTAS del pipeline automático

Las escribe `pipeline_local.py` (función `alertar()`) cuando algo falla o queda raro.
Claude las lee al inicio de cada sesión (`/inicio-sesion`, paso 0) y las reporta.
Una vez resueltas, se mueven a la sección de abajo.

<!-- Las alertas nuevas se agregan acá abajo automáticamente -->
## 10/07/2026 23:00 — MCF: sitio B2B REDISEÑADO (MAXI PEDIDO) — renovacion produce sesion sin precios
El sitio comerciante.carrefour.com.ar cambio de UI (~10/07). La renovacion automatica loguea
pero la sesion queda asociada a la tienda WARNES (el .env pide AVELLANEDA) y todos los precios
vienen data-price=private. Dos intentos fallidos el 10/07 (21:16 y 22:38). Las defensas nuevas
funcionaron: el scraper aborto sin guardar output basura; el catalogo publica MCF del 08/07 con
fechas honestas. Screenshot del estado: data/quality/carrefour_login_debug.png
Accion sugerida: diagnostico interactivo del flujo nuevo de seleccion de tienda en
scripts/renovar_cookies_carrefour.py (_rellenar_form + post-login) con la ventana de Chrome
abierta — sesion diurna con Facu, ~30-60 min.


---

## Resueltas

- 02/07 a 09/07 — TODAS las alertas "Scraper maxicarrefour/maxiconsumo FALLO hoy" +
  "FUENTE CONGELADA maxicarrefour" (13 alertas acumuladas). Causa raíz diagnosticada y
  arreglada el 10/07: (a) MCF: un único page.goto de 30s sin reintento moría por timeout
  transitorio de Cloudflare → ahora `_goto_con_reintentos()` 3x60s, cookies renovadas y
  scrape OK (3.948 prods); (b) MCO: crash intermitente cuya causa era invisible porque el
  buffer de la pipe se perdía → wrappers ahora con PYTHONUNBUFFERED=1 + skip por categoría;
  scrape OK (4.090 prods). Además Yaguar venía TRUNCADO desde ~25/06 (sitio cambió, páginas
  repetidas) → scraper reescrito sobre la WooCommerce Store API, 7.384/7.384 (100%).
- 01/07 23:04 — Scrapers maxicarrefour y maxiconsumo FALLARON en la corrida de las 21:15.
  Causa: segunda corrida del mismo día (renovación de cookies desconfió + rate-limit MCO).
  El pipeline usó los outputs frescos de la tarde, verificó 39/39 y publicó OK. No aplica
  a la corrida diaria normal de las 10am. Visto con Facu 01/07.
