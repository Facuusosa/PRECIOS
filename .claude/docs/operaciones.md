# Docs: Operaciones

## Renovación de cookies MaxiCarrefour (~30 días)
MaxiCarrefour usa Cloudflare — las cookies `cf_clearance` y `PHPSESSID` expiran cada ~30 días.

**Proceso (15 min):**
1. Abrir Chrome → `comerciante.carrefour.com.ar`
2. Loguearse (credenciales propias del negocio)
3. F12 → Network → recargar página → filtrar por `XHR` o cualquier request al dominio
4. Buscar request con cookies → copiar `cf_clearance` y `PHPSESSID` del header `Cookie:`
5. Actualizar `.env` en raíz del proyecto:
   ```
   CARREFOUR_PHPSESSID=nuevo_valor
   CARREFOUR_CF_CLEARANCE=nuevo_valor
   ```
6. Correr `python scrape_maxicarrefour.py` para verificar

**Señal de que expiraron:** el scraper devuelve 0 productos en todos los sectores, o falla con error 403/503.

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

**Última renovación de cookies:** 07/05/2026. Próxima: ~07/06/2026.

## NINI
Removido del MVP. No tiene scraper implementado. Agregar post-v1 si hay demanda.
