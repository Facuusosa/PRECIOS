# Reglas: Scrapers

## Estándar de output (OBLIGATORIO en los 3 scrapers)
- Nunca usar `capture_output=True` en wrappers — output siempre en tiempo real
- Formato por sector: `[X/N] Sector: {nombre}`
- Progreso cada 5 páginas: `Pag 5/36: 120 unicos acumulados`
- Al terminar sector: `{nombre}: {total} productos totales`

## Credenciales
- Todas en `.env` — nunca hardcodeadas en el código
- Yaguar: `YAGUAR_USERNAME`, `YAGUAR_PASSWORD`
- Carrefour: `CARREFOUR_PHPSESSID`, `CARREFOUR_CF_CLEARANCE`

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
- La tarea nocturna `renovar_cookies_diario.bat` (20hs, umbral 25 días) queda como respaldo;
  el control real es el pre-scrape.
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
```
python scrape_yaguar.py         → scraper + actualizar_catalogo.py
python scrape_maxicarrefour.py  → scraper + actualizar_catalogo.py
python scrape_maxiconsumo.py    → scraper + enriquecer_precios.py + actualizar_catalogo.py
python scrape_coto.py           → scraper + actualizar_catalogo.py
python scrape_carrefour.py      → scraper + actualizar_catalogo.py
python scrape_dia.py            → scraper + actualizar_catalogo.py
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

## Anti-bloqueo — reglas permanentes
- Yaguar (Store API): delay 0.5s de cortesía entre requests; sin throttle detectado en la API
- MaxiCarrefour (Cloudflare): cookies PHPSESSID + cf_clearance, renovar cada ~30 días. Si devuelve `data-price="private"` → cookies expiradas, no tocar el código
- MaxiCarrefour (Cloudflare): cookies PHPSESSID + cf_clearance, renovar cada ~30 días. Si devuelve `data-price="private"` → cookies expiradas, no tocar el código
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
