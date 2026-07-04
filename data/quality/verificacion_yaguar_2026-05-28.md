# Verificacion Precios Yaguar — 2026-05-28

## Metodologia
- Scraper corrido a las 2026-05-28 (en background, sin output todavia — se uso catalogo del 2026-05-27)
- Comparacion: Top 5 productos donde Yaguar es el mas barato vs competidores (ratio <= 3x para filtrar falsos matches)
- Verificacion: precio extraido de la web real vs precio en catalogo
- Nota: El precio mostrado en Yaguar es POR BULTO. El precio unitario figura como "$ X precio final por unidad"

---

## Producto 1: Salsa Filetto CICA X340 g
- **EAN:** 7794000006294
- **Precio en catalogo:** $1.105
- **Precio en web:** $1.105 (precio final por unidad — bulto 4 unidades = $4.422 total)
- **Diferencia:** $0 (0%)
- **Estado:** OK (diferencia < 5%)
- **Screenshot:** screenshots/yaguar_7794000006294_2026-05-28.png
- **URL verificada:** https://yaguar.com.ar/producto/salsa-cica-filetto-340gr/
- **Ahorro vs Maxiconsumo:** 64.7% ($1.105 vs $3.134)

---

## Producto 2: Salsa Pomarola CICA X340 g
- **EAN:** 7794000006287
- **Precio en catalogo:** $1.105
- **Precio en web:** $1.105 (precio final por unidad — bulto 4 unidades = $4.422 total)
- **Diferencia:** $0 (0%)
- **Estado:** OK (diferencia < 5%)
- **Screenshot:** screenshots/yaguar_7794000006287_2026-05-28.png
- **URL verificada:** https://yaguar.com.ar/producto/salsa-cica-pomarola-340gr/
- **Ahorro vs Maxiconsumo:** 64.7% ($1.105 vs $3.134)

---

## Producto 3: Salsa Pizza CICA X340 g
- **EAN:** 7794000006270
- **Precio en catalogo:** $1.105
- **Precio en web:** URL INACCESIBLE (404 — pagina no encontrada)
- **Diferencia:** N/A
- **Estado:** AMARILLO — producto removido o URL cambiada en Yaguar
- **Screenshot:** screenshots/yaguar_7794000006270_2026-05-28.png
- **URL verificada:** https://yaguar.com.ar/producto/salsa-cica-pizza-340gr/
- **Nota:** El producto aparece en el catalogo con precio $1.105 pero el link de Yaguar da 404. Puede que el producto fue discontinuado o la URL cambio.

---

## Producto 4: Alfajor B/N Negro X50 g
- **EAN:** 7790040141179
- **Precio en catalogo:** $877
- **Precio en web:** $877 (precio final por unidad — bulto 6 unidades = $5.260 total)
- **Diferencia:** $0 (0%)
- **Estado:** OK (diferencia < 5%)
- **Screenshot:** screenshots/yaguar_7790040141179_2026-05-28.png
- **URL verificada:** https://yaguar.com.ar/producto/alfajor-bagley-bn-negro-50gr/
- **Ahorro vs Maxiconsumo:** 63.9% ($877 vs $2.430)

---

## Producto 5: Alfajor B y N Blanco X50 g
- **EAN:** (sin EAN en catalogo)
- **Precio en catalogo:** $877
- **Precio en web:** $877 (precio final por unidad — bulto 6 unidades = $5.260 total)
- **Diferencia:** $0 (0%)
- **Estado:** OK (diferencia < 5%)
- **Screenshot:** screenshots/yaguar_sin_ean_alfajor_blanco_2026-05-28.png
- **URL verificada:** https://yaguar.com.ar/producto/alfajor-bagley-bn-blanco-50gr/
- **Ahorro vs Maxiconsumo:** 63.9% ($877 vs $2.430)

---

## Resumen

| Estado | Cantidad |
|--------|----------|
| OK (diferencia < 5%) | 4 |
| AMARILLO (URL 404, precio no verificable) | 1 |
| ROJO (diferencia critica >15%) | 0 |

**Conclusion:** Los precios de Yaguar en el catalogo son correctos para los productos verificables (4/5 con diferencia $0). Un producto (Salsa Pizza CICA) tiene URL rota en Yaguar — puede estar discontinuado o el link cambio, requiere actualizacion del link en el catalogo.

**Observacion importante:** Yaguar muestra el precio TOTAL DEL BULTO como precio principal. El scraper correctamente extrae el precio unitario ("precio final por unidad"). No hay bug en la extraccion de precios.

**Scraper:** Aun en ejecucion al momento de generar este reporte. Output mas reciente disponible: output_yaguar_20260527_153508.json (datos del 2026-05-27).
