# Reglas: Scrapers

## Estándar de output (OBLIGATORIO en los 3 scrapers)
- Nunca usar `capture_output=True` en wrappers — output siempre en tiempo real
- Formato por sector: `[X/N] Sector: {nombre}`
- Progreso cada 5 páginas: `Pag 5/36: 120 unicos acumulados`
- Al terminar sector: `{nombre}: {total} productos totales`

## Credenciales
- Todas en `.env` — nunca hardcodeadas en el código
- Yaguar: `YAGUAR_USERNAME`, `YAGUAR_PASSWORD`
- Carrefour: `CARREFOUR_PHPSESSID`, `CARREFOUR_CF_CLEARANCE`

## Cookies MaxiCarrefour — validez y renovación (actualizado 01/07/2026)
- **La sesión PHP (PHPSESSID) muere en HORAS por inactividad, no en 30 días.** Medido:
  scrape 16:52 OK, a las 19:47 el mismo request devolvía `data-price="private"`.
  NUNCA validar cookies por edad — solo por funcionalidad (request real que exija precio).
- **Señal de sesión muerta (cambió ~21/06/2026):** antes el sitio devolvía `item_card_public`;
  ahora devuelve `item_card` normal con `data-price="private"`. Cualquier chequeo de sesión
  debe buscar AMBAS señales. Este cambio silencioso dejó el scraper roto 11 días (incidente
  01/07: la app publicó precios MCF del 20/06 sin que nadie se enterara).
- **Renovación AUTOMÁTICA, no manual:** `scrape_maxicarrefour.py` valida funcionalidad con
  `_cookies_vigentes()` antes de cada scrape; si están muertas llama solo a
  `scripts/renovar_cookies_carrefour.py --force` (Chrome con perfil persistente en
  `data/carrefour_profile` — el reCAPTCHA suele pasar sin humano por el historial del perfil;
  si falla, beep + 90s para click manual). Modo 100% sin humano disponible: `CAPSOLVER_API_KEY`
  en `.env` (no activado — activar solo si el auto-click empieza a fallar seguido).
- La tarea nocturna `renovar_cookies_diario.bat` (20hs, umbral 25 días) queda como respaldo;
  el control real es el pre-scrape.
- Consecuencia para verificación de precios MCF: solo funciona con sesión caliente —
  `verificar_precios_real.py` debe correr PEGADO al scrape (por eso vive en `pipeline_local.py`).

## Pipeline de ejecución
```
python scrape_yaguar.py         → scraper + actualizar_catalogo.py
python scrape_maxicarrefour.py  → scraper + actualizar_catalogo.py
python scrape_maxiconsumo.py    → scraper + enriquecer_precios.py + actualizar_catalogo.py
```

## Cada scraper debe
- Guardar output con timestamp: `output_{mayorista}_{YYYYMMDD_HHMMSS}.json`
- Loguear errores por sector sin detener los demás
- Retornar exit code 0 solo si produjo datos válidos

## Anti-bloqueo — reglas permanentes
- Yaguar (WordPress): delay mínimo 0.5s entre requests, sin headers raros
- **Yaguar throttle por sesión (documentado 17/06/2026 — bug que truncaba el 84% del catálogo):**
  tras ~74 páginas seguidas a 1 req/s, Yaguar devuelve páginas con status 200 pero SIN
  `e-loop-item` (página vacía) como rate-limit suave. El scraper viejo hacía `if not prods:
  break` y lo confundía con "fin de catálogo" → cortaba Almacén en pág 75 de ~460 (traía 2.386
  de ~14.700). El throttle está atado a la SESIÓN, no a la IP: **re-login con sesión fresca lo
  libera al instante; esperar NO sirve (medido: ni 60s)**. Fix en `scrapear_categoria`: si una
  página viene vacía y `pagina < max_pagina`, llamar `crear_sesion()` (re-login) y reintentar;
  solo cortar si tras re-login sigue vacía. La sesión fresca se propaga a los sectores
  siguientes (`scrapear_categoria` devuelve `(productos, session)`). Costo: ~1 re-login cada
  ~74 páginas; el scrape completo de Yaguar pasa de ~23min a ~40-60min pero trae el catálogo
  entero. Regla derivada: una página vacía ANTES de `max_pagina` casi nunca es fin real — es
  throttle; nunca `break` directo sin reintentar con sesión nueva.
- MaxiCarrefour (Cloudflare): cookies PHPSESSID + cf_clearance, renovar cada ~30 días. Si devuelve `data-price="private"` → cookies expiradas, no tocar el código
- MaxiCarrefour LINKS: no hay URLs de producto individuales sin login. El buscador `/search/{ean}` da 1 resultado exacto PERO solo para ~48% de los EANs: Carrefour rota EANs y el del catálogo no siempre está indexado (medido 14/06/2026 sobre 50 productos). SOLUCIÓN HÍBRIDA (`_carrefour_links_hibrido` en `actualizar_catalogo.py`): verifica cada EAN contra la API del buscador `…/products?currentUrl=search/{ean}&method=productsList` (si la respuesta tiene `item_card` el EAN existe) → `/search/{ean}` directo; si no → `/search/{nombre_url_encoded}` (muestra resultados relacionados, nunca pantalla vacía). Es ~4853 requests, +~2min al pipeline; robusto: ante error de red conserva `/search/{ean}`. NO usar solo nombre (decenas de resultados) ni solo EAN (54% pantalla vacía). El endpoint `/busca/?q=` da 404 y la VTEX API requiere auth. La ficha `/p/{ean}` existe pero usa el EAN interno del buscador (≠ EAN físico del catálogo), no sirve desde el catálogo.
- Maxiconsumo (Magento): curl_cffi con `impersonate="safari15_3"` — NUNCA usar requests normal, Cloudflare lo bloquea
- Si scraper devuelve 0 productos: primero sospechar bloqueo/cookies, no tocar código

## Cuellos de botella conocidos
- Yaguar y Maxiconsumo NO tienen EAN → matching via Listado Maestro (fuzzy Jaccard) + CODIGOS.xlsx
- MaxiCarrefour 100% EAN
- Fuzzy threshold Paso 1b: `_FUZZ1B_TH = 0.60` | Fuzzy Paso 6c: `_TH6 = 0.75` (subido de 0.65 el 21/05 para evitar falsos matches tipo Fernet 1882 ↔ Fernet Branca)
- Yaguar: combina 8 archivos (multi-file, igual que Maxiconsumo) para maximizar cobertura
- Tasa de matching actual: ~18% de productos con 2+ precios comparables (3,018 productos)
- Con 3 precios: 772 | ABC=A con 3 precios: 94 (estos son los Top Bombas)

## Bucle verificador post-scraping
Después de correr cualquier scraper, verificar:
1. ¿Se generó el archivo output con timestamp?
2. ¿Cuántos productos tiene? ¿Es un número razonable?
3. ¿Los precios son > 0 en la mayoría de los productos?
4. ¿actualizar_catalogo.py corrió y actualizó catalogo_unificado.json?
Si algo falla → identificar causa → corregir → volver a correr.
