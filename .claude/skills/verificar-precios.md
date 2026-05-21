# Skill: Verificar Precios en Vivo

Verifica los precios del catálogo contra los sitios reales de los mayoristas. Usa `/verificar-precios`.

## Cuándo usar
- Antes de salir a comercializar (parte del /pre-launch-check)
- Cuando hay dudas sobre si los precios del catálogo están actualizados
- Después de renovar cookies de MaxiCarrefour
- Spot-check periódico semanal de calidad de datos

## Motor
`scripts/verificar_precios_real.py` — HTTP puro, sin browser, curl_cffi con impersonación Safari.
- **Yaguar**: navega la URL del producto (WooCommerce), extrae precio con BeautifulSoup
- **MaxiCarrefour**: VTEX API `/api/catalog_system/pub/products/search/{ean}` con cookies del .env
- **Maxiconsumo**: navega la URL del producto con curl_cffi impersonando Safari

Tolerancia aceptable: 10% de diferencia entre catálogo y web real.
Umbral de aprobación: ≥80% de productos verificados con estado OK.

## Pasos

1. **Correr el script**
   ```bash
   python scripts/verificar_precios_real.py 20
   ```
   Verifica las top 20 bombas con clasificación ABC=A. Argumento opcional: N de productos a verificar.

2. **Interpretar resultados**
   - `ok` → precio web coincide con catálogo (diferencia ≤10%)
   - `diverge` → diferencia >10% → correr el scraper de ese mayorista
   - `error_http` / `excepcion` → URL inaccesible o cookies expiradas
   - `sin_link` → el producto no tiene URL → no verificable

3. **Acciones según resultado**
   - Si MaxiCarrefour devuelve `error_http 401/403` → cookies expiradas → renovar PHPSESSID y cf_clearance en .env
   - Si Yaguar devuelve `excepcion` o `sin_link` en todos → revisar que el scraper corrió recientemente
   - Si >20% con `diverge` → priorizar scraping del mayorista con más discrepancias

4. **Reporte automático**
   El script guarda el resultado en `data/quality/verificacion_precios_YYYYMMDD_HHMMSS.json`
   Exit code 1 si tasa de aprobación <80%.

## Integración en pipeline

Ya integrado en `scrape_maxiconsumo.py` — corre automáticamente al final del pipeline completo.
Si el exit code es 1, el pipeline imprime "ALERTA: revisar antes de publicar".

## Resultado esperado
- ≥16/20 productos con estado `ok` → datos confiables para comercializar
- Si <80% `ok` → no salir a comercializar hasta corregir los scrapers que fallan
