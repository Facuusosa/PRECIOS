# Reglas: Scrapers

## Estándar de output (OBLIGATORIO en todos los scrapers)
- Nunca usar `capture_output=True` en wrappers — output siempre en tiempo real
- Formato por sector: `[X/N] Sector: {nombre}`
- Progreso cada 5 páginas: `Pag 5/36: 120 unicos acumulados`
- Al terminar sector: `{nombre}: {total} productos totales`

## Credenciales
- Todas en `.env` — nunca hardcodeadas en el código
- Yaguar: `YAGUAR_USERNAME`, `YAGUAR_PASSWORD`
- **MaxiCarrefour (mayorista B2B)** — el nombre de variable quedó como "CARREFOUR_*" por
  motivos históricos, NO confundir con Carrefour retail (cadena, sin auth, ver su sección
  más abajo): `CARREFOUR_PHPSESSID`, `CARREFOUR_CF_CLEARANCE` (sesión) +
  `CARREFOUR_CUIT`, `CARREFOUR_NOMBRE`, `CARREFOUR_EMAIL`, `CARREFOUR_TELEFONO`,
  `CARREFOUR_PROVINCIA`, `CARREFOUR_SUCURSAL` (login automático, usadas por
  `scripts/renovar_cookies_carrefour.py`) + `CAPSOLVER_API_KEY` (opcional, resolución de
  reCAPTCHA sin click manual — no activada hoy)
- Maxiconsumo, Coto, Carrefour retail, Dia, Masonline, Jumbo: sin credenciales (APIs
  públicas, ver sección propia de cada una)
- **Nini (mayorista, cuenta PRESTADA por un tercero — NUNCA usar para comprar):**
  `NINI_USERNAME`, `NINI_PASSWORD` — ver sección propia más abajo

## Oferta (precio_regular/oferta) por fuente — auditado 20/07/2026
- **MaxiCarrefour: SÍ tiene oferta real, capturada desde 20/07.** El mismo HTML de listado
  (`sec/{slug}`, sin requests extra) trae `discount_percentage`, `discounted_number_price`
  (`<s>precio regular</s>`) y `sale_name`/`data-salename` ("Folleto Maxi", "Oportunidad Maxi").
  `parsear_pagina()` en `scraper_pro.py` los captura; `actualizar_catalogo.py:1481` los propaga
  a `fuentes.maxicarrefour.precio_regular`/`.oferta` igual que las cadenas. ~13% del catálogo.
- **Yaguar: NO tiene oferta hoy.** La Store API de WooCommerce trae nativamente
  `prices.regular_price`/`sale_price`/`on_sale` en cada producto — el campo existe y se
  capturaría gratis si el sitio activa descuentos — pero barrido de ~4.800/7.384 productos +
  las 143 categorías completas + tags de producto: cero coincidencias con oferta/liquidación/
  descuento. No hay nada que arreglar en el scraper; es un hecho del sitio, no un bug.
- **Maxiconsumo: NO tiene oferta capturable, y no es un bug de scraping.** El sitio tiene
  páginas `/ofertas` y `/promociones`, pero son folletos/revistas semanales en PDF o imagen
  escaneada (`media/pdf_files/...`), no HTML estructurado — extraerlas requeriría OCR, fuera
  de alcance. La página `/ofertas-fin-de-semana.html` sí es una categoría normal de Magento,
  pero el mismo SKU tiene precio IDÉNTICO ahí y en la categoría normal (verificado: $2.899,90
  en ambos) — es una vidriera curada, no un descuento real. La estructura de "precio por bulto
  cerrado vs. unitario" que trae CADA producto del sitio (100% de la muestra) tampoco es
  oferta — es cómo Maxiconsumo vende siempre (descuento por volumen permanente).

## Cookies MaxiCarrefour — validez y renovación (actualizado 01/07/2026)
- **La sesión PHP (PHPSESSID) muere en HORAS por inactividad, no en 30 días.** Medido:
  scrape 16:52 OK, a las 19:47 el mismo request devolvía `data-price="private"`.
  NUNCA validar cookies por edad — solo por funcionalidad (request real que exija precio).
- **Señal de sesión muerta (cambió ~21/06/2026):** antes el sitio devolvía `item_card_public`;
  ahora devuelve `item_card` normal con `data-price="private"`. Cualquier chequeo de sesión
  debe buscar AMBAS señales. Este cambio silencioso dejó el scraper roto 11 días (incidente
  01/07: la app publicó precios MCF del 20/06 sin que nadie se enterara).
- **Renovación AUTOMÁTICA, no manual:** `scrape_maxicarrefour.py` valida funcionalidad con
  `_cookies_vigentes()` antes de cada scrape; si están muertas llama solo a
  `scripts/renovar_cookies_carrefour.py --force` (Chrome con perfil persistente en
  `data/carrefour_profile` — el reCAPTCHA suele pasar sin humano por el historial del perfil;
  si falla, beep + 90s para click manual). Modo 100% sin humano disponible: `CAPSOLVER_API_KEY`
  en `.env` (no activado — activar solo si el auto-click empieza a fallar seguido).
- **Env var vieja heredada pisaba la cookie fresca (causa raiz real, cerrada 24/07/2026):**
  el fix del 16/07 (revalidar con `_cookies_vigentes()` tras renovar) redujo el problema pero
  NO lo eliminó — seguía recurriendo (7 veces en 8 días, siempre "CRONICO"). Causa real:
  `scrape_maxicarrefour.py` arma el `env` para los subprocesos ANTES de renovar (`pipeline_local.py`
  ya había cargado el `.env` viejo al arrancar), así que ese dict trae el PHPSESSID muerto de
  ayer. La revalidación post-renovación SÍ usa `load_dotenv(override=True)` y pasa OK — pero
  el dict `env` ya estaba copiado antes de esa actualización. `scraper_pro.py` hacía
  `load_dotenv()` SIN `override=True`: como la variable ya "existía" (vieja), no la pisaba con
  la fresca del archivo, y el scraper completo corría con la cookie muerta (0/N precios en
  TODOS los sectores). Fix: `scraper_pro.py:20` ahora usa `load_dotenv(override=True)`. Detalle
  completo en `data/quality/ALERTA.md` (sección Resueltas, 24/07).
- **Form de login MAXI PEDIDO (diagnosticado y arreglado 15/07/2026)** — causa de ~12
  corridas de las 10am fallidas (03-15/07): el sitio rediseñado (a) agrega un paso previo
  de modalidad de entrega (`#checkbox_retiro`) sin el cual `#region`/`#seller` no se montan,
  y (b) sus selects/inputs tienen bounding box 0x0 (widget custom del CSS) — Playwright los
  considera invisibles y `select_option()`/`fill()` mueren SIEMPRE por timeout aunque el form
  se vea perfecto en pantalla. Fix en `_rellenar_form()`: click a la modalidad + `force=True`
  en cada interacción. NUNCA reemplazar por `dispatchEvent` de JS puro: genera eventos con
  `isTrusted=false` y el reCAPTCHA Enterprise bloquea el submit (probado ese mismo día).
  Si el form vuelve a fallar tras otro rediseño: inspeccionar el DOM real (selects, ids,
  visibilidad y computed styles) ANTES de tocar el flujo — dos veces ya fue la estructura.
- La tarea nocturna `renovar_cookies_diario.bat` (20hs) es desde el 15/07/2026 un RESCATE
  real: corre `scrape_maxicarrefour.py --solo-si-falta-hoy` (si la mañana ya trajo output
  MCF sano no hace nada; si falló, renueva+scrapea con Facu en casa para el click de
  respaldo). El chequeo viejo por edad (25 días) era teatro — la sesión muere en horas.
  Además `scrape_maxicarrefour.py` reintenta la renovación una 2da vez (espera 60s) antes
  de abortar: el 2do intento suele prender (patrón documentado el 12/07).
- **Navegación con reintentos (fix 10/07/2026):** `_goto_con_reintentos()` — 3 intentos de
  60s con espera incremental (10s/30s). Antes un único `page.goto` de 30s que fallaba por
  un timeout transitorio de Cloudflare mataba el scrape del día entero (pasó 7 de 8 días,
  02-09/07). Si el goto falla los 3 intentos DOS días seguidos → el perfil de Chrome
  (`data/carrefour_profile`) puede estar quemado por Cloudflare: borrarlo y hacer un
  login manual una vez para regenerarlo.
- **Login en falso = sesión "semi-autenticada" (incidente 10/07/2026):** el auto-click
  reportó "EXITOSO" con el botón aún `btn-disabled-outlined`; la sesión resultante listaba
  productos PERO con `data-price="private"` en el 100%. Tres defensas agregadas ese día:
  (1) `_cookies_vigentes()` exige señal POSITIVA (`data-price="<dígito>` via regex) — solo
  descartar señales negativas dejaba pasar cualquier body raro como vigente;
  (2) `scraper_pro.py` MCF aborta con exit 1 si <50% de los productos tienen precio > 0
  (contar productos no alcanza — el 10/07 guardó 3.948 productos con CERO precios);
  (3) `sanidad_outputs()` del pipeline alerta si un output tiene <50% de precios > 0.
  Si la renovación automática produce sesiones sin precios repetidamente → click manual
  (beep + 90s) o activar CapSolver.
- **Sitio rediseñado "MAXI PEDIDO" (10-12/07/2026) — mismo síntoma, causa distinta:** tras un
  cambio de UI del sitio, el formulario completaba bien Provincia/Sucursal pero el click en
  "Siguiente" (`#btn_step2`) tiraba timeout (botón seguía `btn-disabled-outlined`) y el código
  igual reportaba "EXITOSO". **No se encontró bug de código reproducible** — reintentar
  `renovar_cookies_carrefour.py --force` una segunda vez el mismo día resolvió el login
  (4.614 prods, 100% con precio). Ante este patrón: reintentar `--force` antes de asumir que
  hay que tocar el flujo de `_rellenar_form()`.
- **Renovar cookies YA dispara el scraper solo (fix 10/07/2026):** `renovar_cookies_carrefour.py`,
  al lograr login (CapSolver o Chrome), llama automáticamente a `scrape_maxicarrefour.py` salvo
  que lo hayan invocado con `--no-auto-scrape` (así se llama a sí mismo internamente, para no
  scrapear 2 veces). Motivo: el 09/07/2026 el pipeline automático de la mañana falló en renovar
  (nadie hizo el click en 90s), Facu logueó a mano por la tarde corriendo el renovador SOLO, pero
  como nada volvió a llamar al scraper, la sesión murió por inactividad (mueren en horas, no en
  días) antes de que el verificador de precios la usara esa noche — el login manual se
  desperdició y el catálogo publicó con MCF de 2 días de atraso. Con el fix, correr
  `python scripts/renovar_cookies_carrefour.py --force` a mano alcanza: renueva Y scrapea en el
  mismo paso, no hace falta acordarse de un segundo comando.
- Consecuencia para verificación de precios MCF: solo funciona con sesión caliente —
  `verificar_precios_real.py` debe correr PEGADO al scrape (por eso vive en `pipeline_local.py`).

## Pipeline de ejecución
Orquestador real: **`pipeline_local.py`** — corre las 8 fuentes + `actualizar_catalogo.py`
+ gates de sanidad (`sanidad_outputs()`, verificación en vivo) en una sola corrida.
Wrappers individuales, para correr una sola fuente suelta:
```
python scrape_yaguar.py         → scraper + actualizar_catalogo.py
python scrape_maxicarrefour.py  → scraper + actualizar_catalogo.py
python scrape_maxiconsumo.py    → scraper + enriquecer_precios.py + actualizar_catalogo.py
python scrape_nini.py           → scraper + actualizar_catalogo.py
python scrape_coto.py           → scraper + actualizar_catalogo.py
python scrape_carrefour.py      → scraper + actualizar_catalogo.py
python scrape_dia.py            → scraper + actualizar_catalogo.py
python scrape_masonline.py      → scraper + actualizar_catalogo.py
python scrape_jumbo.py          → scraper + actualizar_catalogo.py
```

## Coto (cadena minorista — API Constructor.io, documentado 05/07/2026)
- **Sin credenciales:** API JSON pública `ac.cnstrc.com/browse/group_id/{catv}` con key
  pública embebida en el JS del sitio. Sin cookies, sin WAF, sin login. La fuente más
  fácil del proyecto. 6 categorías "súper", EAN 100% (`product_main_ean`).
- **PRECIO = `price[].listPrice` (mediana entre sucursales), NUNCA `formatPrice`.**
  `formatPrice` es el precio POR UNIDAD DE MEDIDA (litro/kg): Glade 360ml tenía
  formatPrice 527.75 × 0.36 = listPrice 189.99. Confundirlos infla los precios hasta 16x
  (pomada 60cc: $124.999 "por litro" vs $7.499 real). Verificado contra la web renderizada.
- **Saltear productos sin `store_availability`:** la web los muestra "no disponible" sin
  precio, y su listPrice en Constructor puede tener AÑOS de antigüedad (misma trampa que
  la regla 08 de Maxiconsumo). Con el filtro quedan ~15k de ~31k del índice.
- **Cap de la API: 10.000 resultados navegables por group_id** (pág 51 devuelve vacío
  aunque `total_num_results` sea mayor). Almacén (11.4k) lo supera → el scraper barre
  también los subgrupos (`response.groups[0].children`) y dedupea por EAN.
- **Coto NO es mayorista:** entra al catálogo como `tipoFuente: 'cadena'` (referencia
  góndola). Excluido de bombas, outliers, validación cruzada, listas de compra y del
  gate de verificación en vivo. El merge se hace en `main()` DESPUÉS de
  `construir_catalogo()` a propósito — nunca moverlo adentro del constructor.
- **Ofertas: ~55% de la góndola tiene descuento activo (medido 05/07/2026)** —
  `discounts[].discountPrice` ("$8056.30") + `discountText` ("30%Dto"). El output
  guarda `precio` = EFECTIVO (oferta si existe, sino regular), `precio_regular` y
  `oferta`. Mostrar solo el regular infla la góndola a la mitad del catálogo
  (caso Fernet Buhero: regular $11.509 vs oferta $8.056 — lo atrapó Facu a ojo).
- Verificar un precio Coto a mano: abrir el `link` del catálogo (SPA) y comparar contra
  "Precio regular" de la ficha renderizada — el HTML estático no trae el precio.

## Carrefour retail (cadena minorista — API VTEX, documentado 05/07/2026)
- **NO confundir con MaxiCarrefour** (mayorista B2B, PHP + cookies). Este es carrefour.com.ar
  (B2C) sobre VTEX: API Intelligent Search pública, sin auth, sin cookies (hay Cloudflare
  pero no bloquea `/api/` — hasta requests plano pasa). EAN 100% (`items[].ean`).
- **Endpoint:** `/api/io/_v/api/intelligent-search/product_search/category-1/{slug}?page=N&count=100&hideUnavailableItems=true`.
  Caps medidos: `count≤100`, `page≤50` (techo 5.000/ruta; alerta en scraper si una categoría
  pasa de 4.500 → bajar a `category-2/{slug}`). 9 categorías de súper, ~11.3k productos.
- **`hideUnavailableItems=true` es OBLIGATORIO + saltear `AvailableQuantity==0`:** el 69%
  del índice está muerto (39.6k → ~11.5k reales) con Price=0 o precios de años de antigüedad
  (misma trampa que regla 08 / Coto). `IsAvailable` a veces viene null — no confiar solo en él.
- **PRECIO = `Price` (efectivo unitario), `ListPrice` = regular tachado.** Verificado 4/4
  contra la web renderizada. NUNCA usar `pricePerUnit` (por litro/kg — trampa formatPrice).
  Oferta directa = Price < ListPrice (~24% del disponible).
- **Promos "2do al 70%"/3x2 (~22%) NO alteran `Price`:** viven en `teasers[]` con
  `conditions.minimumQuantity>=2`; el % estructurado está en
  `effects.parameters[PercentualDiscount]`. El DOM de la ficha muestra el promedio c/u
  llevando 2 — NO es el precio unitario (al verificar a mano, comparar contra el tachado).
- **TRAMPA: teaser "Tarjeta Carrefour 15%" está en el 100% de los productos** y es promo de
  MEDIO DE PAGO (se identifica por `RestrictionsBins` en conditions) — jamás contarla como
  oferta. El scraper la filtra; si un scrape trae <5% de promos por cantidad, WARN (señal de
  cambio de nomenclatura de teasers).
- **Carrefour NO es mayorista:** `tipoFuente: 'cadena'`, mismas exclusiones que Coto
  (bombas, outliers, validación cruzada, gate en vivo). Merge por EAN post-constructor via
  `cargar_cadena()` + loop de cadenas en `main()`.
- Fallback si IS muere (es app `api/io` versionable): legacy
  `/api/catalog_system/pub/products/search?fq=C:{id}` (cap 2.550/fq, teasers sucios).
  Lookup puntual por EAN para verificador: `?fq=alternateIds_Ean:{ean}` → 1 resultado exacto.
- Plan completo con investigación: `.claude/docs/plan-carrefour.md`.

## Dia Online (cadena minorista — API VTEX legacy, documentado 06/07/2026)
- **NO confundir con MaxiCarrefour ni con Carrefour retail.** diaonline.supermercadosdia.com.ar
  corre sobre VTEX (`accountName=diaio`, header `powered: vtex`) — misma plataforma que
  Carrefour retail, pero **sin Cloudflare ni ningun anti-bot detectado** (requests planos
  pasan con 200, la fuente mas simple de las tres cadenas).
- **Usar el endpoint legacy, NO el Intelligent Search:** `/api/io/_v/api/intelligent-search`
  con el slug simple de categoria NO filtra bien (devuelve `recordsFiltered` identico para
  todas las categorias — parece fallback al catalogo completo). El legacy
  `/api/catalog_system/pub/products/search?fq=C:{id}&_from=X&_to=Y` si filtra correctamente
  y es la fuente usada. IDs de categoria via `/api/catalog_system/pub/category/tree/3`
  (no hay slugs utilizables para el legacy, hace falta el ID numerico).
- **Paginacion por indice, step de 50** (pedir 100 de una vez trunca por debajo de lo
  esperado). Cap clasico VTEX de 2.500 por `fq`: ninguna de las 9 categorias "super" lo
  supera (max medido ~1.100), no hace falta la tecnica de subgrupos de Coto.
- **PRECIO = `items[].sellers[].commertialOffer.Price` (efectivo), `ListPrice` = regular
  tachado.** Trampa de precio por unidad de medida vive en las specifications del producto
  (`PrecioPorUnd`/`UnidaddeMedida`) — mismo patron que `formatPrice` (Coto) y `pricePerUnit`
  (Carrefour), tercera vez que aparece esta trampa. Nunca usar ese campo.
- **Sin `hideUnavailableItems` en el legacy:** el endpoint trae tambien productos sin stock
  con precios de anos de antiguedad (misma trampa que regla 08 / Coto / Carrefour). Filtro
  obligatorio client-side por `AvailableQuantity > 0`.
- **EAN 100%** en `items[].ean`. Ofertas por cantidad ("2do al X%", "NxM") viven en
  `commertialOffer.PromotionTeasers[]`, ya en PascalCase limpio (a diferencia del legacy
  crudo que serializa `<Name>k__BackingField`). **No se detecto teaser de medio de pago**
  (tipo "Tarjeta 15%" de Carrefour) en muestras de Almacen (39 prods) ni Bebidas (50 prods,
  16 con teaser real) — el parser igual filtra por las dudas si aparece `RestrictionsBins`.
- **Volumen:** ~4.760 scrapeados / ~1.832 con match EAN contra el catalogo (medido
  06/07/2026) — la mas chica de las 3 cadenas (Coto ~15k/4.1k, Carrefour ~11.3k/4.7k).
- Categorias "super" incluidas (mismo criterio que Carrefour retail, excluye Electro Hogar/
  Indumentaria/Tecnologia/Colchones/Aire libre/Hogar y Deco): Almacen(1), Desayuno(80),
  Bebidas(164), Frescos(121), Congelados(200), Limpieza(282), Perfumeria(216), Mascotas(71),
  Bebe(53) — IDs numericos de categoria, no slugs.

## Masonline (cadena minorista — API VTEX legacy, documentado 20/07/2026)
- Sitio sobre VTEX (CloudFront, sin Cloudflare, sin auth) — mismo perfil que Coto/
  Carrefour/Dia. Usa el legacy Catalog System igual que Dia (`fq=C:{id}`).
- **El arbol de categorias NO tiene agrupador "super"**: a diferencia de Dia/Jumbo,
  cada nodo del arbol (`/api/catalog_system/pub/category/tree/2`) ya es una categoria
  especifica de grano fino (ids 200xxx, ej "Aceites, Vinagres y Aderezos"). El scraper
  agrupa manualmente varios ids bajo un mismo sector display (Almacen=12 ids, Perfumeria=
  14 ids, etc.) — ver `CATEGORIAS` en `targets/masonline/scraper_pro.py`.
- **ListPrice SI es confiable** (a diferencia de Jumbo, ver abajo): ratios medidos entre
  Price y ListPrice van de 1.18x a 2.5x maximo — ofertas reales, ~8% del catalogo.
- **Volumen:** 7.433 scrapeados / 2.726 con match EAN contra el catalogo (medido
  20/07/2026).
- `MIN_PRODUCTS_EXPECTED` calibrado a 5.500 (el bruto por categoria suma ~29.800, pero
  el filtro de disponibilidad + dedupe por EAN entre categorias solapadas deja ~7.400
  reales — no calibrar este umbral sobre el bruto, calibrar sobre el numero real medido).

## Jumbo (cadena minorista Cencosud — API VTEX Intelligent Search, documentado 20/07/2026)
- Sitio sobre VTEX (CloudFront, sin Cloudflare, sin auth).
- **El legacy Catalog System NO sirve en este sitio**: `fq=C:{id}` con categorias de
  nivel 1 (ej Almacen=1, 29.809 productos) funciona, pero con IDs de subcategoria
  (nivel 2/3) devuelve SIEMPRE 0 — Jumbo solo indexa productos en la categoria raiz
  para el legacy. Se uso Intelligent Search en su lugar.
- **El Intelligent Search con el slug simple en el path NO filtra** (mismo bug ya
  documentado para Dia: `recordsFiltered` identico ~88k para cualquier categoria =
  fallback al catalogo completo). La ruta que SI filtra es con el prefijo
  `category-1/{slug}` (mismo patron que Carrefour retail):
  `/api/io/_v/api/intelligent-search/product_search/category-1/{slug}?page=N&count=100&hideUnavailableItems=true`.
- Caps identicos a Carrefour (count<=100, page<=50, techo ~5.000/ruta) — con
  `hideUnavailableItems=true` ninguna de las 15 categorias "super" supera 3.900
  (Almacen, la mas grande), no hizo falta bajar a category-2.
- **BUG CRITICO DE DATOS — ListPrice viene roto en el 100% del catalogo** (medido
  20/07/2026 sobre 10.450 productos: los ~10.347 que tenian ListPrice>Price daban un
  ratio mediano de 82x, hasta 8.264x — ej Price=$2.799 vs ListPrice=$231.405 en un
  Kitkat de $2.800 real). No es una oferta real, es un campo nunca actualizado en el
  feed de Jumbo. **`precio_regular` se fija SIEMPRE igual a `precio`** en
  `targets/jumbo/scraper_pro.py` — NUNCA revertir esto sin volver a medir el ratio real
  contra la web (umbral razonable: <3x, igual criterio que se uso para descartar el bug).
  Si esto se pasa por alto, la app va a mostrar "99% OFF" falso en casi todo Jumbo.
- **DESCUENTO REAL NO estaba en el listado de categoria — fix 24/07/2026.** El
  listado (`product_search`) no trae ninguna oferta real (los `teasers[]` de
  `commertialOffer` vienen SIEMPRE vacios para Jumbo, verificado sobre 2.000+ SKUs
  con oferta activa — a diferencia de Carrefour, donde si se usan). Comparando la API
  contra la ficha renderizada con JS (Puppeteer) en muestra al azar: 5/6 productos
  tenian 25-40% off invisible para el scraper viejo (Kitkat $2.800 -> $1.680, Milka
  $12.250 -> $7.962,5, etc.) — motor de precios "Jumbo Prime + campañas" que corre
  100% client-side. Fuente real: `POST https://www.jumbo.com.ar/_v/search-promotions`
  (mismo dominio, sin auth ni cookies), body `{"seller": PROMO_SELLER, "skus": [...]}`
  — **limite duro de 20 SKUs por request** (21+ tira 500 "SKU limit exceeded").
  Devuelve 3 grupos (`sgc`/`jumbo_prime`/`generic`); un SKU puede tener promo en mas
  de uno a la vez y la ficha real usa SIEMPRE el de mayor prioridad
  `sgc > jumbo_prime > generic` (logica sacada del bundle JS de la tienda — el
  frontend muestra el precio Jumbo Prime a cualquier visitante, sin login). Formula
  verificada 6/6 contra la ficha real, para los 4 `categoryType` que existen
  (segundo_al, percentual, fixed_price, nxm): `precio = precio_regular *
  (1 - float(promo["effectiveDiscount"]))`. `seller` NO es el `sellerId: "1"` del
  listado — es el `defaultSeller` hardcodeado en el bundle JS para la cuenta VTEX
  `jumboargentinaio` (`jumboargentinaj5202martinez`); con `seller: "1"` el endpoint
  responde "item no encontrado" para el 100% de los SKUs. Implementado en
  `fetch_promociones()`/`descuentos_del_lote()` de `targets/jumbo/scraper_pro.py`,
  corre como pasada final sobre los SKUs unicos ya deduplicados (no por categoria).
  Si el endpoint cambia de forma: capturar `performance.getEntriesByType('resource')`
  en una ficha de producto con Puppeteer filtrando "search-promotions", bajar los
  bundles JS listados y grep `defaultSeller`.
- **Verificado end-to-end 24/07/2026:** corrida completa 10.546 productos, 3.979
  (37%) con precio real con descuento, en 7m18s (22:00:48 a 22:08:06) — dentro del
  presupuesto del pipeline diario. Muestra de 8 productos al azar (4 con oferta, 4
  sin) contra la ficha real con Puppeteer: 7/8 exactos, 1/8 (Pepsi Black "6x4") con
  diferencia de $8 sobre $1.607 (0.5%) — causa: `effectiveDiscount` viene redondeado
  a 2 decimales en el feed de Jumbo (1/3 exacto = 0.3333... se guarda como "0.33"),
  la ficha real usa la fraccion exacta del NxM. Limitacion conocida y aceptada: solo
  afecta promos "NxM" cuya fraccion no es exacta a 2 decimales (6x4, no 4x2/3x2/2x1),
  desvio tipico <1%, no vale la complejidad de parsear el código para recalcular.
- **Volumen:** 10.546 scrapeados (medido 24/07/2026, tras el fix de precio real) /
  3.381 con match EAN contra el catalogo (medido 20/07/2026, previo al fix — no
  cambia con este fix, que solo toca `precio`/`oferta`, no el EAN).
- Categorias "super" (15, ids/slugs en `CATEGORIAS` de `targets/jumbo/scraper_pro.py`):
  Almacen, Bebidas, Frutas y Verduras, Carnes, Pescados y Mariscos, Quesos y Fiambres,
  Lacteos, Congelados, Panaderia y Pasteleria, Rotiseria, Perfumeria, Limpieza, Mascotas,
  Mundo Bebe, Pastas Frescas — excluye Electro(15), Hogar y textil(16), Tiempo Libre(465,
  deportes/jugueteria), Sin Categoria(9999), Felices Fiestas(10038, estacional).

## Nini Mayorista (API RPC interna vía sesion Playwright, documentado 29/07/2026)
- **CUENTA PRESTADA POR UN TERCERO — NUNCA usarla para comprar.** El usuario 38620
  no es de Facu; alguien se la prestó únicamente para consultar precios. El scraper
  es SOLO LECTURA por diseño (`targets/nini/scraper_pro.py`): whitelist duro
  (`_METODOS_PERMITIDOS`) de qué combinaciones `daoName/method` puede llamar —
  cualquier otra levanta excepción antes de armar el request. JAMÁS agregar
  `onlineOrderDao` (tiene `Confirm`/`Reserve`/`destroy`) ni tocar cantidad de
  producto, "Confirmar Pedido", "Anular Pedido" ni "Guardar en Borrador" — esos
  botones existen a un click de donde navega el scraper porque la cuenta tiene
  un pedido real en curso de su dueño.
- **La URL de listado no sirve como acceso directo** (`?nini.controllers.listadoDeProductos`
  redirige al login si se navega sin pasar por el flujo) — el sitio guarda el
  estado ("pedido en curso") en la sesión del servidor, igual que el form MAXI
  PEDIDO de MaxiCarrefour. El scraper replica el flujo exacto de un humano:
  login → Creación de pedido → Continuar → Seguir comprando.
- **Detrás de la SPA hay una API JSON real** (backend Node.js, `POST /nodejs/{daoName}/{method}`,
  body urlencoded estilo PHP): `onlineDeparmentDao/findFacets` (8 departamentos),
  `onlineSectorDao/findAll` (135 sectores en una sola llamada, id con prefijo de
  departamento: `210040` = depto `210` + sector), `onlineProductDao/findAllWithOrder`
  (productos con precio, paginado `offsetProducts`/`limit=50`, ya filtrado a
  `withStock=true` por el propio sitio — no hace falta filtrar sin-stock como en
  Maxiconsumo).
- **El id del "pedido en curso" (`currentOrder.id`) es obligatorio para pedir
  precios pero no vive en ningún global de JS accesible.** Se captura
  interceptando el primer request real que dispara el propio sitio al llegar al
  listado (`page.on("request")` de Playwright, sin JS inyectado) — nunca se
  hardcodea, porque si el dueño real de la cuenta confirma/anula su pedido ese
  id puede cambiar de un día para el otro.
- **Bug de encoding real (no cosmético) — el backend responde en ISO-8859-1
  sin declararlo:** `fetch().text()` asume UTF-8 y corrompía "CAÑUELAS" en
  "CA�UELAS" (nombres/marcas con ñ/é quedaban con caracteres de reemplazo en
  el JSON final, no solo en la consola). Fix en `_fetch_dao()`: leer
  `arrayBuffer()` y decodificar con el charset real del header (`iso-8859-1`
  si no viene declarado).
- **Nini NO tiene EAN accesible, y no es por falta de investigar.** La API
  cliente (`onlineProductDao`) no lo expone en ningún campo. Existe un concepto
  interno (`Nini.Models.Barcode`, `Product.findByBarcode` → `productDao`, no
  `onlineProductDao`) pero devolvió 500 al probarlo — es un DAO fuera del rol
  "cliente" de esta cuenta. Se decidió NO insistir: forzar variantes de un
  endpoint admin que ya rechazó el acceso, usando una cuenta prestada, cruza la
  línea de "scrapear como cliente" a "forzar accesos internos ajenos". Matchea
  por nombre exactamente igual que Yaguar/Maxiconsumo (fuzzy contra el Maestro +
  aprendizaje contra cadenas vía `expandir_mapeo_con_cadenas`, persistido en
  `mapeo_brujula.json["por_sku_nini"]`) — sin hoja propia en CODIGOS.xlsx.
- **Integración completa en `actualizar_catalogo.py` verificada en vivo
  (29/07/2026):** primera corrida real, sin arranque en frío — 7.239 productos
  válidos scrapeados, 7.148 entraron al catálogo, 402 matcheados contra
  MaxiCarrefour vía aprendizaje + 343 vía Maestro en la misma corrida. La API de
  Nini ya filtra `withStock=true`, así que no aplica la trampa de precios-sin-stock
  de la regla 08.
- La API no trae imagen ni link de producto usable — esos campos quedan vacíos
  en `fuentes.nini` (a diferencia de Yaguar/MaxiCarrefour/Maxiconsumo).
- **NO se agregó Nini al gate de verificación en vivo** (`scripts/verificar_precios_real.py`).
  A diferencia de Yaguar (ficha pública) o MaxiCarrefour (sesión ya cacheada), Nini no
  tiene una vía de verificación liviana sin repetir todo el login — y repetirlo
  solo para verificar sumaría accesos automáticos innecesarios a una cuenta
  prestada. Decisión deliberada, no un olvido.
- `MIN_PRODUCTS_EXPECTED = 3500` calibrado sobre la primera corrida real (7.248
  scrapeados). El pipeline NO tiene un mínimo de matches en `pipeline_local.py`
  todavía (`minimos_fuente`) — a propósito: sin EAN propio, el número de matches
  crece con cada corrida (aprendizaje), fijar un piso ahora bloquearía
  publicaciones válidas mientras converge.

## Cada scraper debe
- Guardar output con timestamp: `output_{mayorista}_{YYYYMMDD_HHMMSS}.json`
- Loguear errores por sector sin detener los demás
- Retornar exit code 0 solo si produjo datos válidos
- **Output SIN registros duplicados** (`len(registros) == len(claves unicas)`): el pipeline
  lo verifica en `sanidad_outputs()` y alerta si hay >5% de duplicados. Un scraper que
  repite registros = paginación rota (bug Yaguar 25/06-10/07: 34.886 registros / 5.137
  únicos, invisible 2 semanas porque el conteo bruto parecía sano).
- **Los wrappers corren los scrapers con `PYTHONUNBUFFERED=1`** (fix 10/07/2026): sin eso,
  un crash duro del scraper (curl_cffi es extensión C) pierde el buffer entero de la pipe
  y el log queda sin NINGUNA línea de causa — 8 días de "ERROR EN SCRAPER MAXICONSUMO"
  sin diagnóstico posible.

## Yaguar — WooCommerce Store API (reescrito 10/07/2026)
- **El sitio eliminó la navegación HTML el ~10/07/2026:** `/categoria-producto/{slug}/`,
  `/tienda/page/N/` y las fichas `/producto/{slug}/` redirigen TODOS a `/tienda/` (una
  página fija con 16 productos). Cualquier scraper HTML está muerto. El síntoma previo
  (rate-limit con páginas repetidas en vez de vacías) generó duplicados masivos y truncó
  el catálogo al ~70% durante 2 semanas sin que nadie lo viera.
- **Vía actual: Store API pública de WooCommerce** `/wp-json/wc/store/v1/products`
  (`per_page=100`, header `x-wp-total` = total real del catálogo: 7.384 medido 10/07).
  Categorías top-level dinámicas via `/products/categories` (parent=0) + barrido general
  `orderby=id` para atrapar productos sin categoría. Cobertura 100% verificada contra
  `x-wp-total` en cada corrida. El scrape completo tarda ~4 minutos (antes: 8 horas).
- **Precio = `prices.price` / 10^`currency_minor_unit`**. Verificado idéntico al HTML
  logueado del 09/07 (SKUs 90050, 87568 exactos) y `cf-cache-status: BYPASS` (no es el
  cache viejo de Cloudflare de la regla 09). Anónimo == logueado hoy; el login se mantiene
  por si activan precios B2B diferenciados (costo cero).
- **Los SKUs de la Store API son los mismos** que los "Cod." del HTML viejo → CODIGOS.xlsx
  y todo el matching a EAN siguen funcionando sin cambios.
- **Los links `/producto/{slug}/` hoy redirigen a `/tienda/`** — el campo `link` del output
  queda apuntando ahí igual (si Yaguar restaura las fichas, vuelven a andar solos). Tener
  en cuenta al verificar precios a mano: la ficha web NO carga, usar la Store API.
- **Caida real del catalogo del 36% el 19/07/2026 (7.456 -> ~4.748), NO es bug** — bajo
  parejo en casi todas las categorias (Frescos -55%, Almacen -47%, Bebidas -52%, etc.),
  confirmado con una consulta directa a la API en vivo (anonima, `cf-cache-status: DYNAMIC`
  = no es cache) que devolvio el mismo 4.748 dos dias seguidos, y `stock_status=outofstock`
  devuelve 0 — Yaguar dejo de listar productos sin stock (la API ya no los expone ni
  filtrando explicito). El `MIN_PRODUCTS_EXPECTED` viejo (5.000, calibrado el 10/07 sobre
  el catalogo grande) generaba "ERROR" y frenaba la publicacion sobre datos en realidad
  sanos — bajado a 3.500 (26% de margen bajo el piso real actual, mismo criterio de las
  demas fuentes). Si el total vuelve a subir cerca de 7k, es Yaguar reponiendo stock, no
  hace falta tocar nada.

## Anti-bloqueo — reglas permanentes
- Yaguar (Store API): delay 0.5s de cortesía entre requests; sin throttle detectado en la API
- MaxiCarrefour (Cloudflare): cookies PHPSESSID + cf_clearance — mueren en HORAS por
  inactividad, no en 30 días (ver sección de cookies arriba, la renovación es automática).
  Si devuelve `data-price="private"` → cookies expiradas, no tocar el código
- MaxiCarrefour LINKS: no hay URLs de producto individuales sin login. El buscador `/search/{ean}` da 1 resultado exacto PERO solo para ~48% de los EANs: Carrefour rota EANs y el del catálogo no siempre está indexado (medido 14/06/2026 sobre 50 productos). SOLUCIÓN HÍBRIDA (`_carrefour_links_hibrido` en `actualizar_catalogo.py`): verifica cada EAN contra la API del buscador `…/products?currentUrl=search/{ean}&method=productsList` (si la respuesta tiene `item_card` el EAN existe) → `/search/{ean}` directo; si no → `/search/{nombre_url_encoded}` (muestra resultados relacionados, nunca pantalla vacía). Es ~4853 requests, +~2min al pipeline; robusto: ante error de red conserva `/search/{ean}`. NO usar solo nombre (decenas de resultados) ni solo EAN (54% pantalla vacía). El endpoint `/busca/?q=` da 404 y la VTEX API requiere auth. La ficha `/p/{ean}` existe pero usa el EAN interno del buscador (≠ EAN físico del catálogo), no sirve desde el catálogo.
- Maxiconsumo (Magento): curl_cffi con `impersonate="safari15_3"` — NUNCA usar requests normal, Cloudflare lo bloquea
- Si scraper devuelve 0 productos: primero sospechar bloqueo/cookies, no tocar código

## Cobertura de categorías por sitio (verificado 10/07/2026)
- **Yaguar**: dinámica — el scraper descubre las categorías de la Store API en cada corrida
  y valida el total contra `x-wp-total`. Cobertura 100% garantizada por diseño.
- **MaxiCarrefour**: los 10 sectores hardcodeados son TODOS los que existen en el B2B
  (verificado con `countProducts` contra 18 candidatos extra: kiosco, congelados, bodega,
  electro, etc. — todos devuelven 0). Suman ~3.940 productos.
- **Maxiconsumo**: las 8 categorías hardcodeadas cubren todo el consumo. Existe
  `electro.html` con productos pero queda EXCLUIDO por criterio (igual que Electro Hogar
  en las cadenas — no es surtido de kiosco/almacén). El resto de candidatos: 404.

## Cuellos de botella conocidos
- Yaguar y Maxiconsumo NO tienen EAN → matching via Listado Maestro (fuzzy Jaccard) + CODIGOS.xlsx
- MaxiCarrefour 100% EAN
- Fuzzy threshold Paso 1b: `_FUZZ1B_TH = 0.60` | Fuzzy Paso 6c: `_TH6 = 0.75` (subido de 0.65 el 21/05 para evitar falsos matches tipo Fernet 1882 ↔ Fernet Branca)
- Yaguar: `cargar_yaguar()` combina hasta 12 archivos históricos para maximizar cobertura
- Con Yaguar API completo (10/07): 14.016 productos, 2.011 con 2+ precios, 283 ABC=A con 2+

## Bucle verificador post-scraping
Después de correr cualquier scraper, verificar:
1. ¿Se generó el archivo output con timestamp?
2. ¿Cuántos productos tiene? ¿Es un número razonable?
3. ¿Los precios son > 0 en la mayoría de los productos?
4. ¿actualizar_catalogo.py corrió y actualizó catalogo_unificado.json?
Si algo falla → identificar causa → corregir → volver a correr.
