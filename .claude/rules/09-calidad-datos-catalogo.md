# Regla: Calidad de datos del catálogo

## Los 3 loaders que COMBINAN históricos deben quedarse con el scrape MÁS FRESCO (07/10/2026 — caso Branca)

`cargar_yaguar()`, `cargar_maxiconsumo()` y `cargar_nini()` combinan hasta 12 archivos
históricos por SKU para maximizar cobertura (un SKU que no aparece hoy conserva su último
precio conocido con su fecha real). Al desempatar un SKU presente en varios archivos, SIEMPRE
gana el del scrape más reciente (los archivos se iteran ordenados por mtime descendente, así
que la PRIMERA aparición del SKU es la más fresca). Dos bugs reales por no respetar esto:

- **Nini se quedaba con el precio MÁS ALTO, no el más fresco** (`cargar_nini`, fix 07/10/2026):
  cualquier producto que entrara en oferta o bajara de precio quedaba pisado por el valor viejo
  más caro. Caso: Fernet Branca 750 publicado a $15.943 del 05/10 y marcado "MÁS BARATO" cuando
  el scrape de hoy lo tenía en oferta a $15.299 — invisible hasta que Facu lo vio a ojo. Fix:
  `if sku not in sku_to_mejor` (freshest-wins), igual que las otras dos.
- **Yaguar prefería un precio viejo ≥$200 sobre uno fresco de $100-200** (`cargar_yaguar`, fix
  07/10/2026): el guard anti-escala usaba umbral `<200`, pero desde que Yaguar usa la Store API
  (10/07/2026, precios exactos) un precio de $100-200 es real (sachets, golosinas), no un glitch
  de escala. Bajado a `<100` (solo precios realmente rotos por la pasada x100/x1000).

**Guardrail automático que lo detecta solo — `auditar_frescura_combinados()`** (agregado
07/10/2026): tras cada rebuild compara el catálogo contra el output más fresco de cada una de
las 3 fuentes; si un SKU que SÍ está en el scrape de hoy quedó en el catálogo con otro precio
(>1% de diferencia), escribe la divergencia en `data/quality/consistencia_fuentes.json` y
`pipeline_local.py` la eleva a ALERTA en el veredicto diario. Costo cero (no toca la web, solo
compara archivos ya scrapeados). Habría cazado Branca al instante. Si vuelve a aparecer una
divergencia aquí, el culpable es un `cargar_X()` que dejó de tomar el más reciente — no tocar
el detector, arreglar el loader. (Las cadenas y MaxiCarrefour usan `encontrar_mejor()` = un solo
archivo fresco, no pueden tener este bug; por eso el detector solo cubre las 3 que combinan.)

## Fusiones fuzzy: dos EANs reales distintos NUNCA se fusionan (14/07/2026 — caso Playadito)

El Paso 6c de `actualizar_catalogo.py` fusionaba variantes DISTINTAS de una misma marca
con igual cantidad (Playadito común vs LATA vs DESPALADA dan Jaccard justo 0.75 = `_TH6`)
y descartaba EN SILENCIO la fuente del absorbido si la base ya la tenía. Efecto medido:
~520 productos desaparecidos del catálogo y ~250 comparaciones falsas visibles (precio de
variante A junto a variante B). La Yerba Playadito 500g (EAN ...911), presente en 5 fuentes,
no existía en el catálogo.

Reglas permanentes derivadas (guards agregados ese día — no quitarlos):
- **Dos productos con EAN real distinto jamás se fusionan**, sin importar el score fuzzy
  (el 6b ya lo hacía; el 6c no — era una inconsistencia interna).
- **Una fusión "complementaria" nunca puede descartar datos**: si ambos productos tienen
  precio en la misma fuente, no son complementarios → no fusionar. Descartar un registro
  en silencio está prohibido en cualquier paso nuevo.
- Cada corrida escribe auditoría en `data/quality/fusiones_6c.json` (aplicadas + descartadas).
- Señal de recaída: si "fusiones fuzzy complementarias" del log vuelve a saltar de ~130 a
  600+, algo quitó los guards.

## Expansión autónoma de mapeo SKU→EAN vía cadenas (14/07/2026)

`expandir_mapeo_con_cadenas()` corre en cada `actualizar_catalogo.py` ANTES del constructor:
usa los ~22k pares EAN+nombre de Coto/Carrefour/Día/MCF como diccionario para resolver EANs
de Yaguar/Maxiconsumo. Similitud ≥0.85 (con marca igual + cantidad canónica ±10%) se aprende
solo y persiste en `mapeo_brujula.json`; 0.75–0.85 va a `data/quality/matches_pendientes.json`
(revisión manual; los rechazados se anotan ahí y no se vuelven a proponer); los mapeos
aprendidos con cantidad divergente vs góndola caen en `data/quality/mapeos_sospechosos.json`.
OJO: hay DOS mecanismos que escriben `mapeo_brujula.json` (este y el auto-aprendizaje viejo
al final de `main()`) — ambos solo agregan, nunca pisan, y usan indent=2. Mantener así.

Memorias persistentes del flujo de revisión (15/07/2026 — no romper):
- `matches_pendientes.json` → lista `rechazados` ("fuente:sku:ean"): bloquea re-aprendizaje
  en LOS DOS mecanismos (expansión y fuzzy 1b de main). Sin eso, un rechazo manual volvía
  a entrar solo en la corrida siguiente.
- `mapeos_sospechosos.json` → lista `aceptados`: sospechosos que Facu revisó y mantuvo
  (packs multiplicados, rediseños) — no se re-proponen.
- **Pase TF-IDF de trigramas (3b)**: encuentra typos ("250GGR") y abreviaturas crudas
  ("C/sem") que el Jaccard de palabras no ve. Está en MODO CALIBRACIÓN: `via: "tfidf"`
  solo va a pendientes, jamás auto-aprende, hasta calibrar umbral con feedback real de
  Facu (primera tanda de 300 en el artifact con checkboxes, esperando revisión).
- Restricción de presupuesto (permanente): mejoras de matching solo gratuitas/locales —
  nada de APIs pagas (decisión Facu 15/07).

## Barrido ampliado de fragmentación EAN-EAN vía agente `auditor-catalogo` (17/07/2026)

Más allá de `matches_pendientes.json` (SKU sin EAN → EAN), existe otro tipo de fragmentación:
dos productos que YA tienen EAN real cada uno, pero DISTINTO (mismo producto físico, código
de barras diferente por fabricante/importador/rediseño — caso semilla: Fernet Branca 750,
ver `alias_ean.json`). El agente `auditor-catalogo` puede barrer esto comparando productos
EXCLUSIVOS de una sola fuente entre sí (script ad-hoc, no versionado en el repo — vive en el
scratchpad de la sesión que lo corrió). Hallazgos operativos:

- **Coto/Carrefour/Día no tienen productos exclusivos**: cualquier producto de esas 3 cadenas
  que no tenga mayorista fusionado, casi siempre tiene TAMBIÉN MaxiCarrefour con el mismo EAN
  (ya integradas). El barrido cruzado real termina siendo 100% Yaguar/Maxiconsumo vs
  MaxiCarrefour — no es un bug del método, es la composición real de los datos.
- **Forzar cruces con pool chico de candidatos genera falsos positivos**: al cruzar TODOS los
  pares de fuentes (no solo el emparejamiento principal), con un pool de ~276 productos
  exclusivos de MaxiCarrefour el algoritmo "fuerza" el mejor match disponible aunque sea malo
  (6 de 7 candidatos "alta confianza" de esa ronda eran variante de vino/línea de producto
  distinta del mismo fabricante — Malbec vs Pinot Noir, Champagne vs Vino Tinto, Aclarante vs
  Engrosador). Con pool grande (4600+ vs 2000+) la tasa de falsos positivos es mucho menor.
  Regla: desconfiar de "alta confianza" cuando el grupo candidato del lado B es chico (<500).
- **Productos de Yaguar/Maxiconsumo sin EAN propio** (`ean_a == ""`, tienen `sku_a` igual):
  NO van a `alias_ean.json` (que es EAN→EAN) — van a `mapeo_brujula.json` como
  `por_sku_{fuente}[sku] = ean_canonico`, igual que un match normal.
- **EAN con formato roto** (14 dígitos con un caracter de más, o 12 con uno de menos) se
  aplican TAL CUAL están guardados en el catálogo — nunca "corregir" el dígito a ojo. El
  alias apunta desde el valor exacto que trae la fuente, para que `_ean_canonico()` lo
  resuelva sin importar que el dato de origen tenga un error de tipeo.
- Mecanismo de revisión usado: 2 Artifacts (páginas HTML con checkboxes ✓/✕, ver historial
  de esta sesión) — **las descargas de archivo a disco NO funcionan desde un Artifact**
  (sandboxing de seguridad de la plataforma, confirmado con Facu abriendo en Chrome real, no
  solo en el visor embebido de VSCode). El flujo que sí funciona: Facu copia/pega una lista
  corta de IDs (`fuente:sku` o `ean_a:ean_b`), Claude la cruza contra los archivos reales del
  proyecto para reconstruir y aplicar. Cada tanda aplicada se registra explícitamente en
  `fragmentacion_ampliada.json` (`aprobados`/`rechazados`, listas de `ean_a:ean_b`) para que
  el Artifact se pueda regenerar mostrando SOLO lo pendiente real.

Lecciones del caso leche sachet (15/07/2026 — EAN 7790742348005), no regresionar:
- **Los dígitos sueltos ("1"/"2"/"3") se conservan en `_exp_tokens`**: son el % de grasa
  u otra variante. Filtrarlos hizo que la leche 2% se llevara el EAN de la 1%.
- **El guard de marca acepta la marca en cualquier posición del nombre** (Yaguar suele
  arrancar con el descriptor: "PARCIALMENTE DESCREMADA LA SERENISIMA..."). Solo rechaza
  si la marca detectada de un lado no aparece como token en el otro.
- `_fusionar_grupo` (6a/6b): base = EAN con respaldo en Maestro > EAN sin respaldo > sin
  EAN; colisión de fuente la gana el registro con `fecha_scraping` más fresco. Antes un
  SKU discontinuado con EAN muerto de CODIGOS.xlsx pisaba al SKU vigente y publicaba un
  precio viejo 26% más caro.
- Scraper Maxiconsumo: una página entera "disponibilidad crítica" NO corta la categoría
  (frescos declara ~977 pero solo ~120 tienen stock; el sitio ordena por disponibilidad).
  Fin de paginación = página sin items o página repetida (Magento repite al pasarse).

## Cache público de Yaguar ≠ precio real (01/07/2026 — caso Fernet Branca 750)

Síntoma: Facu (anónimo, browser real) veía $17.772 en la ficha de Yaguar; el catálogo
decía $15.131. Medido con test A/B: la vista anónima venía de Cloudflare con
`cf-cache-status: HIT, age=217.422s` (2.5 días) — precio VIEJO cacheado. El server real
(`BYPASS`, y también la vista logueada — confirmado por Facu logueándose) da $15.131.

- **El precio real de Yaguar es el del server/logueado, NO el de la vista pública anónima**
  (que puede estar cacheada días). El scraper entra logueado → captura el real. Correcto.
- Si un usuario reporta "Yaguar muestra otro precio": preguntar si está logueado ANTES de
  tocar nada. Anónimo + precio distinto = casi seguro cache viejo de Cloudflare.
- Test rápido para confirmar: request con cookie `wordpress_logged_in_test=test` (bypasea
  cache) vs request anónimo puro; mirar `cf-cache-status` y `age` en los headers.
- Mejora pendiente (encolada, no urgente): "modo percepción" en el verificador — leer
  también la vista anónima cacheada y reportar productos donde cache ≠ server, para saber
  qué precios van a confundir a comerciantes que navegan sin loguearse.

## Matching de cantidad: comparar SIEMPRE en cantidad canónica (13/06/2026)

Síntoma reportado por Facu: "mi página muestra una cosa y el link del mayorista muestra
otra". Causa raíz verificada (caso Agua Glaciar): la app mostraba 1.5L a $1.700 pero el
link de Maxiconsumo iba a Glaciar **2L** a $1.405 — fuente mal matcheada a otro tamaño.

El `Paso 6d` de `actualizar_catalogo.py` dejaba pasar 75 casos así (Yaguar 35, MaxiCarrefour
24, Maxiconsumo 16) por dos fallas: (1) umbral `ratio >= 2.0` — Glaciar 1.5↔2L es 1.33x y no
se detectaba; (2) extracción de números con `_QTY_RE` sobre `clave_nombre`, que no entiende
`L`/`LT` ni decimales.

**Fix aplicado:** `_cantidad_canonica()` extrae del nombre CRUDO (no `clave_nombre`) y
normaliza volumen->ml y peso->g. El 6d ahora elimina la fuente si difiere >10% del ancla en
la misma dimensión. El 10% tolera ruido de parsing (950↔930ml = 2%) sin dejar pasar tamaños
distintos. Resultado: 103 fuentes incompatibles eliminadas, casos fuente-vs-fuente a 0.

- Para comparar tamaños SIEMPRE normalizar a unidad canónica; nunca comparar "números
  compartidos" en el string (2L y 2u comparten el 2 y no son lo mismo).
- Quedan ~34 casos display-vs-fuente: el PRECIO es correcto (las fuentes coinciden entre sí)
  pero el `nombre_display` está mal escrito (ej. Quitamanchas "1.5 ml" debió ser "1.5 L") o
  expresa la cantidad distinto (Bon o Bon "18u x 15g" = 270g). Es cosmético, no de precio.

## Gap NO cubierto por cantidad canónica: pack de N unidades con el MISMO EAN que la unidad (auditoría 31/07/2026)

`_cantidad_canonica()` normaliza volumen/peso (ml, g) pero **no detecta multiplicadores de
pack** ("X6", "6 Unidades", "Pack X4", "CAJON"). Cuando el fabricante (o el catálogo interno de
una cadena) reutiliza el MISMO EAN para el pack completo y para la unidad suelta, el match por
EAN se trata como verdad absoluta y nunca pasa por el filtro del 6d — quedan publicadas
comparaciones de precio incorrectas (pack vs unidad, mismo EAN, mismo producto en el catálogo).

Casos confirmados en producción (auditoría 31/07/2026, `data/quality/auditoria_catalogo_20260731.md`):
Cerveza Budweiser/Brahma lata 473-710ml (coto "Pack Latas 6 Unidades" / jumbo "X 6 Un" con el
mismo EAN que la lata suelta de maxiconsumo/nini/dia, ratio 5.5x-9.1x), Chicle Beldent 20u
(maxiconsumo caja completa vs masonline una unidad, 11.1x), Dulce Arcor/Esnaola "CAJON 5 KG"
(maxiconsumo caja sin dividir vs coto precio por 1kg, 3.3x-3.8x).

**Pendiente de implementar:** extender `_cantidad_canonica()` (o agregar un filtro nuevo en el
Paso 6d) para detectar `\bX?\d+\s*(UN|UNI|UNIDADES)\b` / `\bPACK\b` / `\bCAJON\b` en el nombre
crudo de cada fuente y multiplicar la cantidad base por ese factor antes de comparar. Si el
factor detectado difiere entre fuentes que comparten EAN, descartar la comparación con el mismo
criterio que ya usa el 6d para tamaños físicos distintos (>10% de diferencia en la misma
dimensión) — en vez de mostrarla como si fuera una oferta real.

## Regla de oro (12/06/2026): ningún fallback puede alterar metadata de frescura

`_fallback_mc_desde_catalogo()` pisaba `fecha_scraping` con la fecha de hoy "para que el
stale-detection no los marque". Resultado: el scraper MC falló 14 días seguidos en Railway
y 5.128 precios del 28/05 circularon como frescos hasta que Facu los detectó a ojo.

- Un fallback SIEMPRE conserva la fecha real del dato que recicla.
- Si un dato parece fresco, verificar contra la FUENTE (web del mayorista), no contra
  su propia metadata — la fecha del catálogo puede mentir si algún paso la reescribe.
- Señal de reciclaje: precios de una fuente 100% idénticos entre dos corridas separadas
  por días (con inflación, imposible). Test: comparar output viejo vs catálogo actual.
- Diferencia sistemática de ~3% exacta entre nuestra app y el portal logueado del
  comerciante = percepciones IIBB según CUIT del cliente, NO error de scraping.

## Errores documentados (28/05/2026)

### Error 1 — encontrar_mejor priorizaba cantidad sobre recencia
`actualizar_catalogo.py` elegía el archivo con más productos válidos, ignorando la fecha.
Resultado: si el scraper de ayer tenía 2 productos más que el de hoy, se usaba el de ayer.
**Fix aplicado:** nuevo criterio de 5% de tolerancia — si el archivo más reciente está dentro
del 5% del score máximo, gana el más reciente.

### Error 2 — Precios stale en catálogo sin indicador
Productos con precio de hace >30 días aparecían como información vigente en el frontend.
Ejemplo: Cerveza Quilmes Yaguar $1.410 del 20/04 (38 días viejo) mostrada como precio actual.
**Fix aplicado:** `actualizar_catalogo.py` ahora agrega `precio_stale: true` y
`dias_desde_scraping: N` en la fuente del producto. **Actualizado 16/07/2026: el umbral real
en código es `STALE_DIAS = 14`** (`actualizar_catalogo.py:2569`, verificado 29/07/2026 — el
número de línea se corre con cada refactor del archivo), no 30. Verificar el valor en código
ante cualquier duda, no confiar en este número.

## Cómo se usa precio_stale/dias_desde_scraping en el frontend (verificado 16/07/2026)

Ya está IMPLEMENTADO, no es solo un flag sin consumir. `lib/data.ts` expone `frescuraDe()`
con 3 niveles (no solo el booleano `precio_stale`): fresco ≤3 días (verde), reciente 4-14
días (dorado), viejo >14 días (rojo) — con label exacto "Hoy"/"Ayer"/"N días". El componente
`components/frescura-pill.tsx` lo renderiza (punto de color + texto, title con fecha exacta
al hover) y se consume en `bomba-list-item.tsx`, `vista-lista.tsx`, `vista-detalle.tsx` y
`vista-catalogo.tsx`. Un precio de 3-4 días SÍ se distingue visualmente de uno de hoy.

## Bombas de Inicio: filtro de frescura para no contaminar "Bombas de hoy" (05/08/2026)

El título de Inicio (`"Bombas de hoy"` / `"Bombas actualizadas hace N días"`, en
`vista-inicio.tsx`) toma el PEOR caso (mayor antigüedad) entre TODOS los precios mayoristas
de las bombas visibles, no un promedio — un solo producto viejo en el pool contaminaba el
título entero aunque el resto fuera de hoy. Causa de que hubiera productos viejos pese a
scrapers OK: el catálogo combina hasta 12 archivos históricos de Yaguar para maximizar
cobertura (`02-scrapers.md`); un producto que no aparece en el scrape de HOY conserva su
último precio conocido con fecha REAL (no falseada) — comportamiento correcto, no bug.

**Fix:** `calcularBombas()` en `lib/data.ts` excluye del pool cualquier producto donde algún
precio mayorista supere `BOMBA_DIAS_MAX = 3` días de antigüedad — filtrado en el origen
(la función que arma TODAS las bombas), no solo en el texto del título, así tampoco se puede
mostrar una bomba individual con datos viejos. Umbral elegido con datos reales del catálogo:
deja 273/314 candidatos ABC=A (87%), pool sigue grande para el shuffle de rotación (ver
[[project_bombas_rotacion]] en memoria). Si el título vuelve a mostrar "hace N días" con
N>3 de forma consistente (no solo una visita aislada), sospechar que el umbral quedó
desactualizado o que una fuente mayorista viene degradando su frescura real.

## Señales de alerta para detectar precios incorrectos

- Ahorro cross-mayorista >60%: investigar antes de mostrar como bomba real
- `fecha_scraping` de hace >14 días: el precio puede no reflejar la realidad (umbral real,
  ver arriba)
- Productos donde nombre_yaguar o nombre_maxiconsumo están vacíos pero hay precio de ese
  mayorista: el match fue fuzzy no confirmado — riesgo de falso positivo

## Frecuencia recomendada de scraping

- MaxiCarrefour: cookies duran ~30 días → scraper cada 7 días ideal
- Yaguar: scraper cada 7 días (libre, sin auth)
- Maxiconsumo: scraper cada 7 días (libre con curl_cffi)
