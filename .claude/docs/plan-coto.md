# Plan: Sumar Coto Digital como fuente "cadena minorista"

> Plan de ejecución autosuficiente. Objetivo: que se ejecute de punta a punta sin decisiones pendientes.

> **EJECUTADO 05/07/2026** — las 5 fases completas y verificadas (ver checklist al pie y `ESTADO.md`).
> Dos correcciones sobre lo investigado, aprendidas en la verificación de Fase 1:
> 1. **El precio es `price[].listPrice`, NO `formatPrice`** — formatPrice es el precio por
>    unidad de medida (litro/kg). El plan original lo confundió; se detectó comparando contra
>    la web renderizada (Glade 360ml: formatPrice 527.75 ×0.36 = listPrice 189.99).
> 2. **La API capea 10.000 resultados navegables por group_id** — Almacén (11.4k) se barre
>    también por subgrupos (`groups[0].children`). Además se saltean productos sin
>    `store_availability` (traen listPrice de años atrás): quedan ~15k con stock de ~31k.
> El merge de Fase 2 se hizo en `main()` post-`construir_catalogo()` (no como paso interno):
> exclusión estructural de las validaciones mayoristas en 1 punto en vez de 4 parches.
> Logo: `coto.svg` oficial del sitio (no png). Fase B (~11k EAN exclusivos) sigue encolada.

## Contexto

**Por qué.** Brújula hoy compara 3 mayoristas (Yaguar, MaxiCarrefour, Maxiconsumo) para comerciantes. Facu suma **Coto** (cadena minorista) para un producto **dual**: el **consumidor final** usa la app gratis y genera boca-a-boca (marketing), y el **comerciante** la paga como herramienta (ve el precio góndola de Coto como techo de margen: "compro a $X mayorista, Coto lo vende a $Y al público").

**Hallazgo técnico (investigado en vivo el 03-04/07/2026).** El catálogo de Coto no se scrapea del HTML: su buscador está tercerizado en **Constructor.io** (`ac.cnstrc.com`), API JSON pública. Consecuencias:
- **Cero credenciales.** Solo una API key pública embebida en el JS del sitio: `key_r6xzz4IAoTWcipni`. Sin login, sin cookies, sin WAF (la API está en dominio de terceros, fuera del Fortinet de Coto). Es la fuente **más fácil y de menor mantenimiento** del proyecto.
- **EAN 100%** (`product_main_ean`) → integración por EAN directo, igual que MaxiCarrefour, sin fuzzy.
- 200 resultados/página, paginación profunda OK, sin rate-limit observado (12 requests seguidos = 12×200 OK).
- Catálogo "súper" (Almacén, Bebidas, Frescos, Limpieza, Perfumería, Congelados) ≈ **32.700 productos**.

**Decisión de producto (tomada con Facu).** UI = **etiqueta + filtro**: cada fuente tiene un tipo (`mayorista` | `cadena`), badge visible por fila, y toggle global Todos / Mayoristas / Cadenas. Un solo catálogo. La preferencia "soy comerciante / consumidor" vive en Perfil y setea el filtro por defecto.

## Decisiones cerradas (con su razón)

1. **Categorías**: solo las 6 de súper (~32.700). Se excluyen Hogar/Textil/Electro (~57k) por no tener contraparte mayorista.
2. **Precio por sucursal**: **mediana** de `price[].formatPrice` sobre las sucursales (Coto da ~34 precios por producto, casi siempre iguales pero con outliers reales; la mediana es robusta).
3. **EAN exclusivos de Coto → NO crear productos nuevos en esta fase.** Coto solo agrega precio a productos que ya existen en el catálogo (algún mayorista los tiene). **Razón:** el catálogo se importa como **JSON estático dentro del bundle** de Next (`import catalogoUnificado` en [lib/data.ts:1](BRUJULA-DE-PRECIOS/lib/data.ts#L1)); pasar de ~14k a ~40k productos inflaría el bundle y haría lenta la app. Además, un producto solo-góndola no sirve al comerciante. Los ~29k productos exclusivos de Coto (surtido para el consumidor) quedan **encolados para una Fase B** con carga diferida (lazy-load / API), fuera de este plan.
4. **Coto = gratis para todos.** Es el imán del consumidor. No se implementa gating real de tier acá (vive en `proxima-fase.md`); solo se actualizan textos de la vista Planes.

## Riesgo crítico (revisor senior)

`calcularBombas()` en [lib/data.ts:599](BRUJULA-DE-PRECIOS/lib/data.ts#L599) compara TODOS los precios de un producto entre sí. Si Coto (cadena, sistemáticamente más cara) entra al mismo array sin distinción, genera "bombas" falsas del 30-40% que son la brecha natural mayorista↔minorista → rompe la confianza del comerciante y choca con `09-calidad-datos-catalogo.md`. **Mitigación (Fase 3):** `calcularBombas()` calcula min/max/ahorro SOLO sobre `tipoFuente==='mayorista'`.

---

## Fase 1 — Scraper `targets/coto/scraper_pro.py` + wrapper `scrape_coto.py`

**API (probada).** GET a `https://ac.cnstrc.com/browse/group_id/{catv}` con querystring:
`key=key_r6xzz4IAoTWcipni` · `i={client_id}` · `s=1` · `c=ciojs-client-2.1436.1` · `num_results_per_page=200` · `page={n}` · `_dt={epoch_ms}`. Header `User-Agent` de browser. Sin cookies.

**Categorías (group_id):** Almacén `catv00001254` · Frescos `catv00001255` · Bebidas `catv00001256` · Limpieza `catv00001258` · Perfumería `catv00001257` · Congelados `catv00001296`. (`total_num_results` por categoría acota el nº de páginas: `ceil(total/200)`.)

**Extracción por producto** (de `response.results[].data`):
- `ean` = `product_main_ean` (saltear si vacío/0)
- `nombre` = `sku_description`
- `precio` = **mediana** de `[p["formatPrice"] for p in data["price"]]` (saltear si ≤ 0)
- `imagen` = `image_url` (o `product_medium_image_url`)
- `link` = construir desde `data["url"]` (formato `_/R-{id}-{id}-200`) → `https://www.cotodigital.com.ar/sitios/cdigi/productos/{slug}/{data.url}`; validar el patrón contra `productos.xml` del sitemap. Fallback: `https://www.cotodigital.com.ar/sitios/cdigi/nuevositio` + búsqueda por EAN.
- `sector` / `subcategoria`: dejar `""` (el Maestro los resuelve por EAN en `actualizar_catalogo.py`; si se quiere, mapear desde `data["groups"][0]["path_list"]`).

**Output**: `targets/coto/output_coto_YYYYMMDD_HHMMSS.json`, **mismo esquema que los demás scrapers** (verificado en `output_maxicarrefour_*.json`):
```json
{"nombre": str, "precio": float, "ean": str, "sku": str, "sector": str,
 "subcategoria": str, "imagen": str, "link": str, "fuente": "Coto",
 "stock": bool, "fecha_scraping": "YYYY-MM-DD"}
```
(`sku` = `sku_plu`; `stock` = `len(store_availability) > 0`.)

**Estándares obligatorios** (`02-scrapers.md` + `code-style.md`): output en tiempo real (sin `capture_output`); progreso `[X/6] Categoria: {nombre}` y cada 5 páginas `Pag N/M: {acum} unicos`; **nada de caracteres no-ASCII en `print()`** (usar `->`, `OK`); dedupe por EAN. `scrape_coto.py` (raíz) = wrapper: corre el scraper y luego `python actualizar_catalogo.py` (patrón de `scrape_maxicarrefour.py`).

**Verificación Fase 1**: existe el output con timestamp de hoy; >20.000 productos; >95% con EAN y precio > 0; abrir la web de Coto y comparar 4-5 precios a mano.

## Fase 2 — Integración al catálogo `actualizar_catalogo.py`

- **`cargar_coto()`** (nueva, modelo `cargar_maxiconsumo()` [:658](actualizar_catalogo.py#L658) pero por EAN): combina los `output_coto_*.json` recientes + `data/history/coto/` si existe; dedupe por EAN quedándose con el más reciente. Log `Coto: N productos`.
- **`nuevo_producto()`** [:769](actualizar_catalogo.py#L769): agregar `"coto": 0` al dict `precios` (línea 778).
- **Paso nuevo "Coto (100% EAN)"** después del Paso 2 (~[:1057](actualizar_catalogo.py#L1057)), espejando el bloque MaxiCarrefour [:1004-1006](actualizar_catalogo.py#L1004):
  ```python
  for p in coto_data:
      ean = str(p.get("ean","")).strip()
      precio = p.get("precio", 0)
      if not ean or precio <= 0: continue
      if ean in catalogo:                       # decisión #3: solo a existentes
          catalogo[ean]["precios"]["coto"] = precio
          catalogo[ean]["fuentes"]["coto"] = {"nombre": p.get("nombre",""),
              "imagen": p.get("imagen",""), "link": p.get("link",""),
              "fecha_scraping": p.get("fecha_scraping","")}
      # else: EAN solo-Coto -> NO crear (Fase B)
  ```
  Contar matches para el log.
- **`construir_catalogo()`** firma [:748](actualizar_catalogo.py#L748): agregar param `coto_data`.
- **`main()`** [:1945](actualizar_catalogo.py#L1945): `coto = cargar_coto()`; pasarlo a `construir_catalogo(...)`.
- **Marcado stale** [:1986](actualizar_catalogo.py#L1986): agregar `"coto"` a `_mayoristas`.
- **Outlier MC** (regla `08-precios-sin-stock.md`, ~[:1886](actualizar_catalogo.py#L1886)) y **validación cruzada** (~1439): confirmar que operan SOLO sobre las claves mayoristas y **excluyen `coto`** (Coto es legítimamente más caro; no debe descartar precios mayoristas ni ser descartado por caro).

**Verificación Fase 2**: `catalogo_unificado.json` regenerado; contar productos con `precios.coto > 0` (esperado varios miles); el conteo de los 3 mayoristas NO baja; ningún producto queda con `precios` conteniendo `coto` como única fuente.

## Fase 3 — Modelo de datos frontend `lib/data.ts`

- `interface Precio` [:4](BRUJULA-DE-PRECIOS/lib/data.ts#L4): agregar `tipoFuente: 'mayorista' | 'cadena'`.
- Constante nueva `FUENTES` (única fuente de verdad, ver Fase 4): `[{clave, nombre, tipo, logo}]` para yaguar/maxicarrefour/maxiconsumo (`mayorista`) y coto (`cadena`).
- `nombreMayorista` [:193](BRUJULA-DE-PRECIOS/lib/data.ts#L193): agregar `coto: 'Coto'`.
- `preciosMapped` [:200](BRUJULA-DE-PRECIOS/lib/data.ts#L200): setear `tipoFuente` en cada precio (derivado de la clave via `FUENTES`).
- **`calcularBombas()` [:599](BRUJULA-DE-PRECIOS/lib/data.ts#L599): filtrar `preciosValidos` a solo `tipoFuente==='mayorista'`** antes de min/max/ahorro (mitiga el Riesgo crítico). El orden de prioridad "3 mayoristas" [:637](BRUJULA-DE-PRECIOS/lib/data.ts#L637) sigue contando solo mayoristas.

**Verificación Fase 3**: `npx tsc --noEmit` sin errores; las bombas del Inicio no incluyen Coto.

## Fase 4 — Vistas y componentes frontend

**Asset requerido:** logo de Coto en `public/mayoristas/coto.png` (los logos viven ahí: `maxiconsumo.webp`, `yaguar.png`, `maxicarrefour.jpg`, ver [bomba-list-item.tsx:10-14](BRUJULA-DE-PRECIOS/components/bomba-list-item.tsx#L10)). Conseguir el logo oficial de Coto.

**Centralizar primero (anti-duplicación).** La lista de fuentes/logos está hardcodeada en **7 componentes**: `vista-inicio.tsx`, `vista-catalogo.tsx`, `vista-detalle.tsx`, `vista-lista.tsx`, `vista-cuenta.tsx`, `vista-planes.tsx`, `bomba-list-item.tsx`. Reemplazar los arrays sueltos (`LOGOS` en bomba-list-item:10, `MAYORISTAS_FILTER` en vista-catalogo:38, literales `['MaxiCarrefour','Yaguar','Maxiconsumo']`) por lecturas de `FUENTES` de `lib/data.ts`. Así sumar Coto = un solo lugar.

Cambios por vista:
- **Badge MAY/CAD por fila de precio**: [vista-detalle.tsx:293](BRUJULA-DE-PRECIOS/components/vista-detalle.tsx#L293) (sección "Dónde comprarlo" 290-365) y [bomba-list-item.tsx:250](BRUJULA-DE-PRECIOS/components/bomba-list-item.tsx#L250): badge chico según `precio.tipoFuente`.
- **Detalle — separar compra vs góndola**: agrupar mayoristas ("Comprás") y cadenas ("Precio góndola") en 290-365; `mejorPrecio`/"MÁS BARATO" [:63-68](BRUJULA-DE-PRECIOS/components/vista-detalle.tsx#L63) se calcula solo sobre mayoristas.
- **Calculador de margen** [vista-detalle.tsx:438-500](BRUJULA-DE-PRECIOS/components/vista-detalle.tsx#L438): compra = mejor mayorista (ya lo hace); si hay precio Coto, mostrar "Coto vende a $Y → tu margen vs góndola".
- **Toggle Todos/Mayoristas/Cadenas**: extender el filtro de [vista-catalogo.tsx:38-42 y 350-384](BRUJULA-DE-PRECIOS/components/vista-catalogo.tsx#L350) (`mayoristaSel`) para filtrar por `tipoFuente`; "desde $X" y conteos respetan el filtro.
- **Inicio/bombas**: sin cambio de lógica tras Fase 3. Opcional: mostrar precio Coto como "referencia góndola" en `bomba-list-item.tsx`.
- **Perfil** [vista-cuenta.tsx:373-403](BRUJULA-DE-PRECIOS/components/vista-cuenta.tsx#L373): "Mis mayoristas" lista las 4 fuentes con badge; agregar preferencia "Soy comerciante / consumidor" en `brujula_config` (localStorage, [:80](BRUJULA-DE-PRECIOS/components/vista-cuenta.tsx#L80)) que setea el filtro por defecto del catálogo.
- **Planes** [vista-planes.tsx:220-293](BRUJULA-DE-PRECIOS/components/vista-planes.tsx#L220): actualizar textos para reflejar que Coto (cadena) es gratis; NO implementar gating real.

**Verificación Fase 4 (screenshot loop)**: las 6 vistas cargan; badge MAY/CAD visible y legible; toggle filtra bien; Detalle separa compra/góndola; calculador muestra margen vs Coto; bombas sin Coto. Revisar calidad visual del badge/toggle con el agente `diseñador-ux`.

## Fase 5 — Integración al pipeline y verificación end-to-end

**`pipeline_local.py`** — agregar Coto en 4 puntos:
- `contar_por_fuente()` [:73,82](pipeline_local.py#L73): agregar `"coto"` al dict y al loop.
- `main()` scrapers [:180-183](pipeline_local.py#L180): `"coto": run_scraper("scrape_coto.py")`.
- `minimos_fuente` [:214](pipeline_local.py#L214): `"coto": 15000` (umbral anti-reciclaje).
- `limpiar_automatico()` [:140](pipeline_local.py#L140): agregar `"coto"` a la tupla.
- `verificar_precios_real.py` (gate top-20 ABC=A): **Coto NO entra al gate** en esta fase (es referencia, no precio de compra crítico). Confirmar que el script no rompe al ver la clave `coto`.

**Verificación end-to-end**:
1. `python scrape_coto.py` → output OK (Fase 1).
2. `python actualizar_catalogo.py` → catálogo con `precios.coto` (Fase 2).
3. En `BRUJULA-DE-PRECIOS`: `npx tsc --noEmit` y `npm run lint` sin errores.
4. `npm run dev` → las 6 vistas cargan; recorrer el checklist de Fase 4.
5. Correr `pipeline_local.py` en seco (o revisar que los gates no bloqueen por Coto).

## Assets y notas
- **Logo Coto**: `public/mayoristas/coto.png` (pendiente de conseguir — bloquea el badge/logo en UI).
- Imágenes de producto de Coto quedan en `static.cotodigital3.com.ar` (rastro del competidor). Usar el precio; imágenes solo como fallback secundario, nunca primarias (respeta `project_fotos_productos`).
- El sitemap de Coto es de feb-2025; se usa la **API en vivo** para los datos, el sitemap solo para validar el formato del link.
- Modelo por tarea: scraper/pipeline/frontend en Sonnet; verificaciones mecánicas inline.

## Checklist de cierre (para el ejecutor)
- [x] `targets/coto/scraper_pro.py` + `scrape_coto.py` corren y generan output válido (15.043, 100% EAN, 4/4 vs web)
- [x] `cargar_coto()` + merge EAN en `main()` post-constructor (mejor que param en `construir_catalogo` — ver nota de ejecución)
- [x] `"coto"` agregado en: `nuevo_producto`, marcado stale, `pipeline_local` (4 puntos; mínimo 3.000 matches, no 15.000 — el gate mide catálogo, no output)
- [x] Outlier/validación cruzada excluyen `coto` (estructural: corren antes del merge)
- [x] `interface Precio.tipoFuente`, `FUENTES` (reemplaza `nombreMayorista`), `calcularBombas` solo mayoristas
- [x] `FUENTES` reemplaza los hardcodes en los 7 componentes (+ `app/page.tsx` y `RelCard`, fuera del plan)
- [x] `public/mayoristas/coto.svg` presente (oficial del sitio; SVG en vez de png)
- [x] Toggle de tipo, Detalle compra/góndola (bloque GÓNDOLA separado en vez de badge por fila), calculador vs góndola, Perfil preferencia
- [x] `tsc` limpio; 6 vistas verificadas en vivo; bombas sin Coto (`lint` roto de antes: eslint no está en devDependencies)
- [x] Actualizados `HERRAMIENTAS.md`, `CLAUDE.md` (fuentes activas → +Coto) y `02-scrapers.md` (pipeline + sección Coto)
