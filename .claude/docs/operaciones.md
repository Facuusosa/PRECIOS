# Docs: Operaciones

## Cookies MaxiCarrefour — AUTOMÁTICO desde 01/07/2026
La sesión PHP muere en HORAS (no 30 días) — detalle y lecciones en `.claude/rules/02-scrapers.md`.
El flujo es automático: `scrape_maxicarrefour.py` valida las cookies con un request real antes
de cada scrape (`_cookies_vigentes()`: si ve `data-price="private"` están muertas) y si hace
falta corre `scripts/renovar_cookies_carrefour.py --force` (Chrome con perfil persistente,
auto-click del captcha; beep + 90s para click manual solo si el auto-click falla).

**Intervención manual solo si:** hay alerta "Scraper maxicarrefour FALLO" en
`data/quality/ALERTA.md` dos días seguidos → correr a mano
`python scripts/renovar_cookies_carrefour.py --force` con Chrome a la vista.
Plan B 100% sin humano: `CAPSOLVER_API_KEY` en `.env` (~US$1 por 1.000 captchas).

**Proceso manual de emergencia (si todo lo anterior falla, 15 min):**
loguearse en `comerciante.carrefour.com.ar` → F12 → Network → copiar `PHPSESSID` y
`cf_clearance` de un request → pegarlos en `.env` → `python scrape_maxicarrefour.py`.

## Pipeline de datos
```bash
python scrape_yaguar.py        # ~20-30 min
python scrape_maxicarrefour.py # ~15-20 min
python scrape_maxiconsumo.py   # ~10-15 min (incluye enriquecer + actualizar)
python actualizar_catalogo.py  # solo si Yaguar/Carrefour corrieron sin Maxiconsumo
```

## Credenciales (.env)
```
YAGUAR_USERNAME=...
YAGUAR_PASSWORD=...
CARREFOUR_PHPSESSID=...
CARREFOUR_CF_CLEARANCE=...
```
Nunca en el código. Siempre en `.env` (está en `.gitignore`).

## Verificación post-scraping
1. ¿Se generó `output_mayorista_TIMESTAMP.json`?
2. ¿Cuántos productos? (Yaguar >3000, Carrefour >3000, Maxiconsumo >500)
3. ¿Precios > 0 en la mayoría?
4. ¿`catalogo_unificado.json` tiene fecha de hoy?

**Renovación de cookies:** automática pre-scrape (ver sección de arriba). La tarea de las
20:00 (`renovar_cookies_diario.bat`) queda como respaldo secundario.

## Pipeline diario automático (desde 01/07/2026)
Tarea Windows "Brujula - Actualizar precios", 10:00, WakeToRun + StartWhenAvailable:
corre sola con la PC (requiere sesión de Windows iniciada). Secuencia: 3 scrapers →
catálogo → anti-reciclaje → frescura por fuente → verificación en vivo top 20 contra
las 3 webs (diverge >20% → NO publica) → push → Vercel. Fallos → `data/quality/ALERTA.md`
+ beep; Claude los reporta en `/inicio-sesion` (paso 0).

## NINI
Removido del MVP. No tiene scraper implementado. Agregar post-v1 si hay demanda.
