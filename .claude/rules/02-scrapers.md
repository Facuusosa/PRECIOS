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
- MaxiCarrefour cookies expiran cada ~30 días → renovar manualmente (ver docs/operaciones.md)

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
- MaxiCarrefour (Cloudflare): cookies PHPSESSID + cf_clearance, renovar cada ~30 días. Si devuelve `data-price="private"` → cookies expiradas, no tocar el código
- MaxiCarrefour LINKS: imposible obtener URLs de producto. La VTEX API (`/api/catalog_system/pub/products/search/{ean}`) devuelve HTML (login page) incluso con cookies válidas y curl_cffi. El endpoint `/busca/?q=` devuelve 404. No hay URL pública accesible — no gastar tiempo en esto.
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
