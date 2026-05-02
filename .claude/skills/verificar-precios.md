# Skill: Verificar Precios de Bombas

Verifica en vivo los precios de las top N bombas del catálogo actual. Usar con `/verificar-precios`.

## Cuándo usar
- Antes de salir a comercializar (parte del /pre-launch-check)
- Cuando hay dudas sobre si los precios del catálogo están desactualizados
- Después de renovar cookies de MaxiCarrefour
- Spot-check periódico de calidad de datos

## Motor
Usa `scripts/verificar_bombas.py` — HTTP puro, sin browser.
- **Yaguar**: WooCommerce API con login curl_cffi (HTTP, sin abrir browser)
- **MaxiCarrefour**: busca en el output JSON local más reciente (sin cookies, sin browser)
- **Maxiconsumo**: curl_cffi con impersonación Safari (igual que el scraper real)

**Chrome DevTools MCP**: útil para inspección visual manual si los precios no coinciden y querés ver el DOM del sitio. No forma parte del flujo automático.

## Pasos

1. **Correr el script**
   ```bash
   python scripts/verificar_bombas.py 10
   ```
   Argumentos opcionales: número de bombas a verificar (default: 10).

2. **Interpretar resultados**
   - `OK` → precio web coincide con catálogo (diferencia <5%)
   - `DIFF_X%` → diferencia entre 5-20% → correr el scraper de ese mayorista
   - `ERROR_X%` → diferencia >20% → bug de matching en el catálogo
   - `NO_ENCONTRADO` → producto no aparece en el buscador o cookies expiradas
   - `N/A (output_viejo_Xh)` → output de MaxiCarrefour tiene más de 48h → correr scraper

3. **Si MaxiCarrefour devuelve output_viejo o sin_output**
   Correr: `python scrape_maxicarrefour.py`
   Si sigue sin funcionar → cookies expiradas → renovar PHPSESSID y cf_clearance en .env

4. **Si Yaguar devuelve N/A en todos**
   Verificar credenciales: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('YAGUAR_USERNAME'))"`

5. **Reporte automático**
   El script guarda el resultado en `data/quality/verificacion_bombas_YYYYMMDD_HHMMSS.json`

## Resultado esperado
- 8/10 o más bombas con estado OK → datos confiables para comercializar
- Si <80% OK → no salir a comercializar hasta corregir los scrapers que fallan
