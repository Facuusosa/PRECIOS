# SIGUIENTE PASO — 20/04/2026

## ESTADO ACTUAL
- Cookies MaxiCarrefour: renovadas hoy (vencen ~20/05)
- Scrapers: último run exitoso el 19/04 (datos de ayer)
- Mensajes outreach: corregidos y listos en `data/outreach/whatsapp_lote1_20260420.txt`
- Pipeline Railway: corregido (antes fallaba silenciosamente)

---

## PASO 1 — Correr scrapers frescos (en orden)

```bash
python scrape_maxicarrefour.py
```
Esperar que termine. Debe decir >3000 productos.
Si dice 0 → cookies expiradas de nuevo (raro, acaban de renovarse).

```bash
python scrape_yaguar.py
```
Esperar. Debe decir >3000 productos.

```bash
python scrape_maxiconsumo.py
```
Esperar. Debe decir >500 productos.

---

## PASO 2 — Verificar calidad del catálogo

```bash
python scripts/validar_catalogo.py
```
Buscar en el output:
- Total productos: >15,000 ✓
- Con 2+ precios: >3,000 ✓

---

## PASO 3 — Verificar precios de bombas (spot-check automático)

```bash
python scripts/verificar_bombas.py 10
```
Esperar que compare los 10 productos con mayor diferencial.
- 8/10 OK → datos confiables, seguir
- <8/10 → revisar qué mayorista falla

---

## PASO 4 — QA en producción (decirle a Claude)

```
Actúa como el agente definido en `.claude/agents/qa-verificador.md` y verifica la app en https://v0-brujula-de-precios.vercel.app
```
Esperar reporte. 4/5 vistas VERDE → seguir.

---

## PASO 5 — Deploy con datos frescos

```bash
cd BRUJULA-DE-PRECIOS
git add data/processed/catalogo_unificado.json
git commit -m "data: actualizacion precios 20/04"
git push origin main
cd ..
```
Vercel se redeploya solo en 2-3 minutos (integración automática GitHub→Vercel).

---

## PASO 6 — Enviar los primeros 5 WhatsApps

Abrir `data/outreach/whatsapp_lote1_20260420.txt` — copiar y enviar los mensajes 1 al 5.
Cuando termines, decirle a Claude "marcar los primeros 5 como enviados" y lo hace en el xlsx.

---

## ATAJO: hacer todo de un disparo (si Claude está abierto)

```
/pre-launch-check
```
Orquesta los pasos 2, 3, 4 y genera reporte go/no-go automáticamente.
El paso 1 (scrapers) hay que correrlo manualmente primero.

---

## RENOVACIÓN DE COOKIES MAXICARREFOUR (próxima: ~20/05)
1. Chrome → `comerciante.carrefour.com.ar` → iniciar sesión
2. F12 → Network → cualquier request → pestaña Headers → buscar Cookie
3. Copiar `PHPSESSID=...` y `cf_clearance=...`
4. Actualizar `.env` con los nuevos valores
5. Correr `python scrape_maxicarrefour.py` para verificar
