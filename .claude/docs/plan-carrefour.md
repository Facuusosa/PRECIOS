# Plan: Sumar Carrefour retail (carrefour.com.ar) como fuente "cadena"

> Segunda cadena minorista después de Coto. Investigado en vivo el 05/07/2026 con 2 subagentes
> (API + estructura/ofertas) y verificado a mano (delegation-verification). Reportes crudos en
> scratchpad de la sesión; los hallazgos permanentes quedan acá y en `02-scrapers.md`.

## ✅ EJECUTADO 05-06/07/2026 — resultados verificados

- **Scraper:** 11.285 productos únicos (98% de los ~11.485 disponibles; el resto es
  solapamiento entre categorías dedupado + sin EAN). 100% EAN, 100% precio>0, 100% imagen.
  3.573 con oferta real (31%): descuento directo + promo cantidad (1.054 con "2do al X%"/NxM).
- **Catálogo:** 4.809 productos con precio góndola Carrefour (de 13.275 totales) — más que
  Coto (4.116). 1.624 de esos con oferta activa. 3.146 con doble góndola (Coto+Carrefour).
  5.779 con mayorista + alguna cadena (margen vs góndola visible). Mayoristas intactos
  (Y 6.591 / MC 4.735 / MCO 4.140).
- **Verificación de precios:** 3/3 exactos contra la API legacy en vivo (endpoint distinto
  al del scraper — verificación independiente por EAN). Y 4/4 del subagente vs web
  renderizada con Puppeteer en la investigación.
- **Frontend:** entrada en `FUENTES` + `carrefour.jpg` (logo completo que dejó Facu en
  public/mayoristas; el isotipo svg descargado se borró). `tsc --noEmit` limpio. El resto (badge CAD, toggle, góndola en detalle, exclusión de bombas) salió
  gratis de la arquitectura FUENTES del rediseño Coto.
- **Pipeline:** `pipeline_local.py` con carrefour en los 5 puntos (mínimo 3.000 matches);
  `verificar_precios_real.py` lo excluye estructuralmente (whitelist de mayoristas).
- **Docs:** CLAUDE.md, 02-scrapers.md (sección Carrefour), HERRAMIENTAS.md y
  `.claude/skills/pipeline-datos.md` (que además no tenía a Coto — corregido).
- **PENDIENTE:** commit+push tras OK de Facu — junto con Coto, que también sigue sin commit.
  Fase B (surtido exclusivo de cadenas, ~6.5k Carrefour + ~11k Coto) sigue encolada.
- Vistas en vivo: verificadas con Coto en su momento; con Carrefour el rendering es el
  mismo camino (FUENTES). Chequeo visual rápido pendiente de la próxima corrida de
  `npm run dev` / QA.

## Contexto

**Por qué.** Facu quiere la góndola de Carrefour retail como segunda referencia "cadena"
(junto a Coto) y, sobre todo, **capturar las ofertas**: la app va a tener una sección
solo-ofertas donde el usuario elige qué ver. Carrefour retail es el sitio B2C
(carrefour.com.ar) — NO confundir con MaxiCarrefour (mayorista B2B, otra plataforma,
cookies, ya integrado).

**Hallazgo técnico (verificado 05/07/2026).** carrefour.com.ar corre sobre **VTEX** con las
APIs de catálogo **públicas y sin auth** (hasta `requests` plano pasa; hay Cloudflare pero no
bloquea `/api/`). EAN 100% (`items[].ean`, 1.100/1.100 muestreados). La fuente más fácil del
proyecto junto con Coto.

## Decisiones cerradas (con su razón)

1. **API: Intelligent Search** — `GET /api/io/_v/api/intelligent-search/product_search/category-1/{slug}?page=N&count=100&hideUnavailableItems=true`
   - `hideUnavailableItems=true` filtra del lado del servidor el **69% del índice que está muerto**
     (39.6k indexados → ~11.5k disponibles reales; los muertos traen Price=0 o precio de años).
   - Teasers de promo **estructurados** (`effects.parameters[PercentualDiscount]`); en la API
     legacy vienen con claves .NET y `Effects` vacío.
   - Caps medidos: `count≤100`, `page≤50` → techo 5.000/ruta. Ninguna categoría disponible
     supera 2.215 → alertar si alguna pasa de 4.500 y ahí bajar a `category-2/{slug}` (probado OK).
   - **Antagónico considerado:** la legacy (`/api/catalog_system/pub/products/search`) es más
     estable a largo plazo, pero no filtra muertos (800 requests + filtrado cliente), capea en
     2.550 por fq y sus teasers son ilegibles. Queda como **fallback documentado** y como
     lookup por EAN para el verificador (`?fq=alternateIds_Ean:{ean}` → 1 resultado exacto).
2. **Categorías: 9 de súper** (slug → disponibles al 05/07): almacen 1.900,
   desayuno-y-merienda 2.002, bebidas 1.687, lacteos-y-productos-frescos 969, congelados 332,
   limpieza 1.361, perfumeria-y-farmacia 2.214, mascotas 480, mundo-bebe 540 ≈ **11.485**.
   Se excluyen carnes/frutas-verduras/panadería (peso variable) y Electro/Hogar/Textil/etc.
3. **Precio** (verificado contra la web renderizada, 4/4 exactos):
   - `Price` = precio EFECTIVO unitario (= spotPrice = sellingPrice). `ListPrice` = regular tachado.
   - `pricePerUnit`/"$ x kilo"/"sin impuestos" de la ficha NO contaminan el API (no hay trampa formatPrice).
   - Un solo seller ("1" CARREFOUR); precio único nacional (regionId solo cambia stock — medido CABA vs Córdoba).
4. **Ofertas — tres tipos, tratamiento distinto:**
   - Descuento directo (`Price < ListPrice`, ~24% del disponible): `precio`=Price,
     `precio_regular`=ListPrice, `oferta`="N% OFF".
   - Promo cantidad "2do al 70%" / 3x2 (~22%): teaser con `conditions.minimumQuantity>=2`.
     NO altera el precio unitario → `precio` sigue = Price; `oferta` = texto ("2do al 70%").
     OJO: el DOM de la ficha muestra el promedio c/u con promo — no compararlo como unitario.
   - **Tarjeta Carrefour 15%: en el 100% de los productos, es medio de pago** (teaser con
     `RestrictionsBins`) → JAMÁS contarla como oferta. Cupones App tampoco.
5. **Merge igual que Coto:** `tipoFuente: 'cadena'`, clave `carrefour`, solo agrega precio a
   EANs ya existentes en el catálogo (exclusivos → Fase B), merge en `main()` DESPUÉS de
   `construir_catalogo()`, fuera de bombas/outliers/validación cruzada/gate en vivo.
6. **Anti-bot:** requests plano alcanza hoy; delay 0.5s + retry con backoff ante 429
   (hubo 1 aislado en ~80 requests). ~130 requests ≈ 2-3 min el scrape completo.

## Fases

### Fase 1 — Scraper `targets/carrefour/scraper_pro.py` + wrapper `scrape_carrefour.py`
Mismo esquema de output que Coto (`output_carrefour_YYYYMMDD_HHMMSS.json`):
`{nombre, precio, precio_regular, oferta, ean, sku, sector, subcategoria, imagen, link, fuente: "Carrefour", stock, fecha_scraping}`
- `sku`=itemId · `imagen`=items[0].images[0].imageUrl · `link`=carrefour.com.ar/{linkText}/p
- `subcategoria` = 2º segmento de `categories[0]` (`/Almacén/Pastas secas/...`)
- Filtros: EAN válido, `AvailableQuantity>0`, `PRECIO_MIN<=precio<=PRECIO_MAX`, dedupe por EAN
  (hay solapamiento entre categorías).
- Sanidad ofertas: si <5% del scrape tiene promo por cantidad, WARN (señal de que Carrefour
  cambió la nomenclatura de teasers).
- MIN_PRODUCTS_EXPECTED = 8.000 (medido ~11.5k al 05/07).
**Verificación:** output con timestamp hoy; >8.000 productos; >95% EAN; 3-4 precios vs web.

### Fase 2 — `actualizar_catalogo.py`
Generalizar el patrón Coto a "cadenas" (anti-duplicación):
- `cargar_cadena(clave)` genérico (reemplaza `cargar_coto()`; sirve a coto y carrefour).
- Merge post-constructor en loop sobre `[("coto",...), ("carrefour",...)]`.
- `nuevo_producto()`: `"carrefour": 0` · stale `_mayoristas` += carrefour · stats con conteo.
**Verificación:** catálogo regenerado; `precios.carrefour>0` en miles; mayoristas no bajan.

### Fase 3 — Frontend
- `FUENTES` en `lib/data.ts`: `{clave:'carrefour', nombre:'Carrefour', tipo:'cadena', logo:'/mayoristas/carrefour.*', url}`.
  Todo lo demás (badge, toggle, exclusión de bombas, bloque góndola) sale gratis del rediseño Coto.
- Logo oficial a `public/mayoristas/`.
**Verificación:** `npx tsc --noEmit`; vistas con Carrefour en góndola; bombas sin Carrefour.

### Fase 4 — Pipeline y docs
- `pipeline_local.py`: `contar_por_fuente`, scrapers dict (`scrape_carrefour.py`),
  `minimos_fuente` (medir matches reales primero), `limpiar_automatico`.
- `verificar_precios_real.py`: confirmar que ignora la clave `carrefour` (whitelist mayoristas).
- Docs: `CLAUDE.md` (fuentes), `02-scrapers.md` (sección Carrefour), `HERRAMIENTAS.md`
  (/pipeline-datos → 5 scrapers), `ESTADO.md`.

### Verificación end-to-end
`python scrape_carrefour.py` → catálogo con carrefour → `tsc` limpio → vistas en vivo →
gates del pipeline no bloquean.

## Riesgos
1. IS es app `api/io` versionable → si muere, fallback legacy (documentado arriba).
2. Nomenclatura de teasers puede cambiar en silencio → WARN <5% promos cantidad.
3. Solapamiento entre categorías → dedupe por EAN (hecho en Fase 1).
4. `PriceValidUntil` viene a 1 año — NO usar como frescura; fecha de scrape propia.

## Checklist de cierre
- [ ] Scraper + wrapper corren y generan output válido (>8k, EAN ~100%, precios vs web OK)
- [ ] `cargar_cadena()` + merge en loop (coto y carrefour por el mismo camino)
- [ ] `carrefour` en: nuevo_producto, stale, stats, pipeline_local (4 puntos), mínimos medidos
- [ ] `FUENTES` + logo; tsc limpio; bombas sin carrefour
- [ ] verificar_precios_real no rompe con la clave nueva
- [ ] Docs actualizados (CLAUDE.md, 02-scrapers.md, HERRAMIENTAS.md, ESTADO.md)
