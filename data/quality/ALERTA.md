# ALERTAS del pipeline automático

Las escribe `pipeline_local.py` (función `alertar()`) cuando algo falla o queda raro.
Claude las lee al inicio de cada sesión (`/inicio-sesion`, paso 0) y las reporta.
Una vez resueltas, se mueven a la sección de abajo.

<!-- Las alertas nuevas se agregan acá abajo automáticamente -->

---

## Resueltas

- 01/07 23:04 — Scrapers maxicarrefour y maxiconsumo FALLARON en la corrida de las 21:15.
  Causa: segunda corrida del mismo día (renovación de cookies desconfió + rate-limit MCO).
  El pipeline usó los outputs frescos de la tarde, verificó 39/39 y publicó OK. No aplica
  a la corrida diaria normal de las 10am. Visto con Facu 01/07.

## 02/07/2026 14:07 — Scraper maxicarrefour FALLO hoy
Accion sugerida: revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force

## 02/07/2026 14:07 — Scraper maxiconsumo FALLO hoy
Accion sugerida: revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force

## 03/07/2026 18:44 — Scraper maxicarrefour FALLO hoy
Accion sugerida: revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force

## 05/07/2026 11:11 — Scraper maxicarrefour FALLO hoy
Accion sugerida: revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force

## 05/07/2026 11:11 — Scraper maxiconsumo FALLO hoy
Accion sugerida: revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force

## 05/07/2026 11:12 — FUENTE CONGELADA: maxicarrefour sin datos frescos hace 4 dias (se publica igual, fechas honestas)
Accion sugerida: el scraper de maxicarrefour viene fallando — revisar data/quality/pipeline_local.log
