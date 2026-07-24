# ALERTAS del pipeline automático

Las escribe `pipeline_local.py` (función `alertar()`) cuando algo falla o queda raro.
Claude las lee al inicio de cada sesión (`/inicio-sesion`, paso 0) y las reporta.
Una vez resueltas, se mueven a la sección de abajo.

<!-- Las alertas nuevas se insertan acá abajo automáticamente (antes de Resueltas) -->

## 17/07/2026 11:10 — Scraper maxiconsumo FALLO hoy
Accion sugerida: revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force

## 17/07/2026 11:18 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 19/07/2026 06:16 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 19/07/2026 15:20 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 20/07/2026 12:19 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 21/07/2026 03:10 — Scraper yaguar FALLO -- 4 corridas seguidas (CRONICO)
Accion sugerida: no es un fallo puntual: revisar el patron en data/quality/historial_corridas.csv y pipeline_local.log

## 21/07/2026 03:16 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 21/07/2026 11:42 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 22/07/2026 14:14 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## 23/07/2026 11:16 — Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual
Accion sugerida: ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json

## Resueltas

- 24/07/2026 — "Scraper maxiconsumo FALLO" (21/07 11:31 y 23/07 11:05 CRONICO, 3 corridas
  seguidas). Los fixes de causa raiz (guardian de timeout + reintento con backoff + corte
  por estancamiento, ver entrada 22/07 mas abajo) YA estaban aplicados en el codigo desde
  el 22/07 -- pero la corrida automatica del 23/07 10:08am volvio a fallar igual, y esta vez
  DISTINTO: las 8 categorias tiraron timeout real (`curl error 28`, no conexion colgada sin
  excepcion) en la pagina 1, incluso tras 3 intentos con backoff 10s/30s -- un bloqueo asi
  de parejo no lo resuelve ningun reintento razonable. Confirmado 24/07: el pipeline de las
  10am corrio solo MaxiCarrefour (OK, 4.898 precios) sin reintentar Maxiconsumo; relanzado
  a mano mas tarde (15:59) completo sin problema, 4.055 productos / 4.054 con precio.
  **HIPOTESIS SIN CONFIRMAR, vigilar:** Cloudflare puede estar bloqueando mas agresivo en
  la franja de las 10am que en la tarde -- necesita mas corridas en distintos horarios para
  confirmar antes de tocar el codigo. Catalogo reconstruido 24/07 con este output
  (`actualizar_catalogo.py` corrido manualmente, 14.278 productos totales).

- 24/07/2026 — "Scraper maxicarrefour FALLO -- N corridas seguidas (CRONICO)" (7 apariciones
  entre 16/07 y 23/07, incl. el intento de fix del 16/07 commit 9cc8556 que solo lo mitigó
  a medias). CAUSA RAIZ REAL encontrada: `scrape_maxicarrefour.py` arma el dict `env` para
  los subprocesos ANTES de renovar cookies (linea ~99); `pipeline_local.py` ya habia cargado
  el `.env` viejo al arrancar (linea 42-43), asi que ese dict trae el PHPSESSID muerto de
  ayer. Cuando la renovacion escribe cookies frescas al archivo `.env`, `_cookies_vigentes()`
  SI las relee bien (usa `load_dotenv(override=True)`) y la validacion pasa — pero el dict
  `env` ya estaba copiado antes, con el valor viejo adentro. `targets/maxicarrefour/scraper_pro.py`
  hacia `load_dotenv()` SIN `override=True` en su import: como la variable ya "existia" (aunque
  vieja), python-dotenv no la pisaba con la fresca del archivo — el scraper completo corria con
  la cookie muerta y sacaba 0/N precios en TODOS los sectores desde el producto 1. Explica por
  que las corridas manuales aisladas (rescate de las 20hs) siempre andaban bien: sin un proceso
  padre que precargara el `.env` viejo, no habia nada que pisar.
  **FIX:** `targets/maxicarrefour/scraper_pro.py:20` ahora hace `load_dotenv(override=True)`.
  **Verificado 24/07** reproduciendo el escenario exacto (variable de entorno vieja inyectada
  a proposito antes de correr `scrape_maxicarrefour.py`): scrape completo, 4.840 productos con
  precio real, cero apariciones de "sesion sin acceso a precios". Si el patron CRONICO
  reaparece, sospechar de una causa nueva — esta especifica ya esta cerrada.

- 22/07/2026 14:08 — "Scraper maxicarrefour FALLO -- 4 corridas seguidas (CRONICO)". Se
  auto-resolvió: el rescate nocturno `renovar_cookies_diario.bat` (20hs) corrió solo, renovó
  cookies (2do intento del form tras detectar estado semi-autenticado en el 1ro) y scrapeó
  4.716 productos a las 20:13. Catálogo unificado ya actualizado con ese output
  (`output_maxicarrefour_20260722_201310.json`, 4.706 con precio). No fue necesaria
  intervención manual.

- 22/07/2026 20:09-23:39 — Maxiconsumo: 4 intentos fallidos + 1 exitoso, 2 bugs reales de
  código encontrados y arreglados (no era solo bloqueo de Cloudflare). Secuencia completa:
  - Intentos 1-2 (20:09 automático, 20:57 manual): 2.504 y 2.422 productos, insuficiente
    (<3.500). Patrón de timeouts intermitentes (curl error 28) que cortaban categorías
    enteras por UN solo blip — `scrape_categoria()` en `targets/maxiconsumo/scraper_pro.py`
    no reintentaba, solo cortaba. **Fix 1:** reintento con backoff (10s/30s) antes de
    abandonar una página.
  - Intento 3 (22:19): quedó COLGADO 30+ min en una sola página sin ninguna excepción — el
    timeout=25 de curl_cffi no se disparó ante una conexión que Cloudflare deja abierta sin
    responder ni cerrar. **Fix 2:** `_get_con_guardian()`, wrapper con thread daemon +
    `join(timeout)` que corta la espera pase lo que pase, sin depender del timeout interno
    de la librería.
  - Intento 4 (22:51): con los 2 fixes, Almacen pasó de su fin real (~pág 130) hasta la
    página 300 (tope duro) sin agregar productos nuevos — el chequeo de "página repetida"
    no detectaba que el sitio reordena/repite cerca del límite sin devolver una página
    IDÉNTICA. 170 requests inútiles por categoría. **Fix 3:** corte por estancamiento (3
    páginas seguidas sin producto nuevo = fin real).
  - Intento 5 (22:51, con los 3 fixes): scraper completo, **4.034 productos únicos**
    (`output_maxiconsumo_raw_20260722_232007.json`). El paso siguiente (`enriquecer_precios.py`,
    visita 4.034 fichas de detalle buscando EAN) se colgó de nuevo a los 2.000/4.034 por el
    MISMO bug del intento 3 (timeout que no se dispara) — pero como ese script guarda
    checkpoint cada 200 productos, el archivo `output_maxiconsumo_20260722_232008.json` ya
    tenía los 4.034 productos completos (4.033 con precio, 0 con EAN — esperado, Maxiconsumo
    no expone EAN, matching es por Jaccard). Se mató el proceso colgado y se corrió
    `actualizar_catalogo.py` manualmente contra ese archivo en vez de esperar el cierre del
    `ThreadPoolExecutor` (bloqueado indefinidamente por la tarea colgada). **Fix 2 aplicado
    también en `enriquecer_precios.py`** para que no vuelva a pasar en la corrida automática.
  - Resultado final: catálogo actualizado, Maxiconsumo 4.067 con precio (vs. 4.043 de ayer).
  - Ningún fix toca nada de anti-bot/evasión — todos atacan resiliencia ante timeouts reales
    de la librería/sitio, consistente con el resto de `.claude/rules/02-scrapers.md`.

- 19/07 06:11 y 20/07 12:13 — "Scraper yaguar FALLO" (incl. CRONICO 3 corridas). Causa
  RAIZ (no bug de scraping): el catalogo real de Yaguar cayo ~36% el 19/07 (7.456 -> 4.748
  productos), parejo en casi todas las categorias (Frescos -55%, Almacen -47%, Bebidas
  -52%) — Yaguar dejo de listar productos sin stock (confirmado: `stock_status=outofstock`
  en su API publica devuelve 0). Verificado en vivo el 21/07 contra la API anonima
  (`cf-cache-status: DYNAMIC`, no cache) con el mismo 4.748 dos dias seguidos. El scraper
  funcionaba bien; el que estaba mal era `MIN_PRODUCTS_EXPECTED = 5000` (calibrado 10/07
  sobre el catalogo grande) — bajado a 3.500 en `targets/yaguar/scraper_pro.py` (detalle en
  `.claude/rules/02-scrapers.md`). La alerta de las 15:16 del 19/07 fue una causa DISTINTA
  y ya transitoria: timeout de red en el login (curl error 28) a las 14:02, no relacionada
  al tamaño del catalogo.
- 13/07 a 15/07 — "Scraper maxicarrefour FALLO hoy" (4 alertas) + fallo 16/07 01:30. CAUSA RAÍZ
  del patrón crónico (~12 corridas de las 10am, 03-15/07) encontrada el 15/07 y RESUELTA:
  el form rediseñado MAXI PEDIDO tiene (a) paso previo de modalidad de entrega
  (#checkbox_retiro) sin el cual #region/#seller no se montan, y (b) selects/inputs con
  bounding box 0x0 que Playwright consideraba invisibles → `_rellenar_form()` moría SIEMPRE
  por timeout. Fix (commit 0af21b7): click a la modalidad + force=True (nunca dispatchEvent
  JS: el reCAPTCHA bloquea isTrusted=false). CONFIRMADO 16/07: dos renovaciones desatendidas
  seguidas (12:35 y 14:01) con "Formulario completo" + "Click automatico EXITOSO" sin humano.
  Detalle permanente en .claude/rules/02-scrapers.md.
- 15/07 21:17 y 16/07 01:36 — "Verificacion en vivo INCONCLUSA": era el gate por fuente NUEVO
  haciendo su trabajo — MCF quedó sin verificar porque su sesión PHP ya estaba fría (corridas
  partidas por suspensión de la PC; el verificador corrió horas después del scrape MCF). En la
  corrida normal de las 10am el verificador corre pegado al scrape. No es un bug.
- 12/07/2026 18:48-18:50 — Scraper maxiconsumo FALLO (corrida de la tarde). Timeout transitorio
  de red (mismo patrón del 11/07). MCO anduvo OK en todas las corridas siguientes (13 a 16/07)
  sin tocar nada — se confirma transitorio.
- 10/07 a 12/07 — MCF: sitio B2B REDISEÑADO (MAXI PEDIDO) — renovacion producia sesion sin
  precios (logueaba en sucursal WARNES en vez de AVELLANEDA, data-price=private). Diagnostico
  interactivo con Facu 12/07: `_rellenar_form()` SI completaba bien el formulario (matcheaba
  "AVELLANEDA" correctamente), pero el intento de click automatico en "#btn_step2" tiraba
  timeout (boton seguia `btn-disabled-outlined`) y el codigo igual reportaba "EXITOSO" en base
  a `_esta_autenticado()` — mismo patron que el incidente del 10/07 documentado en
  02-scrapers.md. Al re-ejecutar `renovar_cookies_carrefour.py --force` una segunda vez el
  mismo dia, el login SI prendio bien: scraper trajo 4.614 productos, 100% con precio real
  (verificado contra la web en vivo, 59/59 correctos).
  ACTUALIZACION 15/07: causa raiz SI encontrada (ver arriba) — era el form rediseñado con
  elementos 0x0 + estado semi-autenticado del perfil, no inestabilidad del reCAPTCHA.
- 02/07 a 09/07 — TODAS las alertas "Scraper maxicarrefour/maxiconsumo FALLO hoy" +
  "FUENTE CONGELADA maxicarrefour" (13 alertas acumuladas). Causa raíz diagnosticada y
  arreglada el 10/07: (a) MCF: un único page.goto de 30s sin reintento moría por timeout
  transitorio de Cloudflare → ahora `_goto_con_reintentos()` 3x60s, cookies renovadas y
  scrape OK (3.948 prods); (b) MCO: crash intermitente cuya causa era invisible porque el
  buffer de la pipe se perdía → wrappers ahora con PYTHONUNBUFFERED=1 + skip por categoría;
  scrape OK (4.090 prods). Además Yaguar venía TRUNCADO desde ~25/06 (sitio cambió, páginas
  repetidas) → scraper reescrito sobre la WooCommerce Store API, 7.384/7.384 (100%).
- 01/07 23:04 — Scrapers maxicarrefour y maxiconsumo FALLARON en la corrida de las 21:15.
  Causa: segunda corrida del mismo día (renovación de cookies desconfió + rate-limit MCO).
  El pipeline usó los outputs frescos de la tarde, verificó 39/39 y publicó OK. No aplica
  a la corrida diaria normal de las 10am. Visto con Facu 01/07.
