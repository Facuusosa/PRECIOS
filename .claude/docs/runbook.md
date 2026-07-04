# Runbook de Emergencias — Brujula de Precios

## Cookies MaxiCarrefour vencidas
Sintoma: scraper devuelve 0 productos o error 403
Fix: python scripts/renovar_cookies_carrefour.py
Manual: comerciante.carrefour.com.ar -> F12 -> Application -> Cookies -> copiar PHPSESSID + cf_clearance al .env

## Matcheo Maxiconsumo bajo (con 2+ precios < 2.500)
Causa: Maxiconsumo no expone EAN en sus paginas web. El matching es 100% por nombre contra Listado Maestro.
Palancas disponibles:
  - Bajar _FUZZ1B_TH en actualizar_catalogo.py (actualmente 0.65, minimo recomendado 0.60)
  - Agregar mapeos manuales en CODIGOS.xlsx (sheet MAXICONSUMO)
  - Enriquecer mapeo_brujula.json manualmente para productos de alta rotacion

## Scraper Yaguar devuelve < 1.000 productos
Fix 1: Verificar YAGUAR_USERNAME y YAGUAR_PASSWORD en .env
Fix 2: Intentar login manual en yaguar.com.ar para ver si hay CAPTCHA o cambio de flujo
Fix 3: Aumentar DELAY_ENTRE_PAGINAS a 2.0s en targets/yaguar/scraper_pro.py

## Catalogo desactualizado (> 7 dias)
Correr: python scrape_yaguar.py
Correr: python scrape_maxicarrefour.py
Correr: python scrape_maxiconsumo.py

## Pipeline automático no corrió (Task Scheduler)
Causa: la PC estaba apagada a las 10:00 (StartWhenAvailable lo recupera al prender)
Fix: correr manualmente `python pipeline_local.py` o doble-click en `actualizar_brujula.bat`
Verificar en: Programador de tareas de Windows → "Brujula - Actualizar precios" → Historial

## Frontend no carga productos
Verificar que BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json existe y no esta vacio
Correr: python actualizar_catalogo.py (si el archivo falta o tiene 0 productos)

## Validacion de calidad post-scraping
python scripts/validar_catalogo.py     <- debe pasar sin ALERTA
python scripts/verificar_precios_real.py 10  <- tasa esperada >= 80%
