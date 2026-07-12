# ALERTAS del pipeline automático

Las escribe `pipeline_local.py` (función `alertar()`) cuando algo falla o queda raro.
Claude las lee al inicio de cada sesión (`/inicio-sesion`, paso 0) y las reporta.
Una vez resueltas, se mueven a la sección de abajo.

<!-- Las alertas nuevas se agregan acá abajo automáticamente -->

## 12/07/2026 18:48-18:50 — Scraper maxiconsumo FALLO (corrida automatica de la tarde)
No investigado todavia — el catalogo publicado usa el output de maxiconsumo del 11/07 21:49
como fallback (sigue siendo dato de ayer, no critico). Si se repite mañana, sospechar el mismo
timeout transitorio de red visto el 11/07 (curl: Operation timed out en paginacion) y relanzar
`python scrape_maxiconsumo.py` solo.

---

## Resueltas

- 10/07 a 12/07 — MCF: sitio B2B REDISEÑADO (MAXI PEDIDO) — renovacion producia sesion sin
  precios (logueaba en sucursal WARNES en vez de AVELLANEDA, data-price=private). Diagnostico
  interactivo con Facu 12/07: `_rellenar_form()` SI completaba bien el formulario (matcheaba
  "AVELLANEDA" correctamente), pero el intento de click automatico en "#btn_step2" tiraba
  timeout (boton seguia `btn-disabled-outlined`) y el codigo igual reportaba "EXITOSO" en base
  a `_esta_autenticado()` — mismo patron que el incidente del 10/07 documentado en
  02-scrapers.md. Al re-ejecutar `renovar_cookies_carrefour.py --force` una segunda vez el
  mismo dia, el login SI prendio bien: scraper trajo 4.614 productos, 100% con precio real
  (verificado contra la web en vivo, 59/59 correctos). No se identifico una causa raiz de
  codigo para arreglar de forma permanente — parece ser inestabilidad puntual del reCAPTCHA/
  timing del sitio nuevo, no un bug fijo del scraper. Si vuelve a fallar: reintentar
  `--force` una segunda vez antes de asumir que hay que tocar codigo.
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
