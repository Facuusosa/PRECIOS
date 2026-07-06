# Estado Vivo — Brújula de Precios
**Última actualización:** 06/07/2026 — CARREFOUR RETAIL EJECUTADO (cadena #2, foco ofertas) + detalle/calculadora rediseñados a pedido de Facu. Falta commit + push de todo junto.

## HECHO 06/07 (ronda 2, feedback de Facu) — Tira unificada + calculadora flexible
- 🔴 **Bug atrapado**: `precioGondola` usaba `.find()` → con 2 cadenas solo mostraba la primera (Coto); Carrefour no aparecía ni en detalle ni en inicio.
- ✅ **Detalle — tira única "Dónde comprarlo"**: mayoristas y cadenas en la misma tira, mismo formato de fila, con **chip MAYORISTA (gris) / CADENA (verde)** bajo cada logo (pedido de Facu). Cadenas muestran OFERTA + tachado solo si el regular es mayor (en "2do al X%" el precio unitario no cambia — tacharlo confundía). Verificado en vivo: Coca Zero 2.25L muestra MaxiCarrefour/Yaguar/Coto/Carrefour con chips y oferta.
- ✅ **Bombas del inicio**: se quitó la línea GÓNDOLA de la tarjeta — las cadenas se ven SOLO en el detalle (decisión de Facu, tarjeta limpia).
- ✅ **Calculadora flexible** (pedido de Facu): (1) selector de pills para elegir el competidor base a libre elección — cualquier mayorista O cadena, default el mayorista más barato; (2) **precio de venta editable** — tipeás el precio exacto y el margen/ganancia se recalculan (margen negativo y ganancia en rojo si vendés bajo el costo). Verificado en vivo: base Carrefour $5.700 + venta $6.000 → margen 5%, ganancia $300. `handleGuardar` guarda la fuente elegida y el margen efectivo.
- Archivos: `components/vista-detalle.tsx` (ChipTipo, preciosGondola array, selector, input venta), `components/bomba-list-item.tsx` (línea GÓNDOLA removida). `tsc` limpio.

## HECHO 06/07 — Carrefour retail integrado de punta a punta (plan `.claude/docs/plan-carrefour.md`)
- ✅ **Investigación**: 2 subagentes en paralelo (API en vivo + estructura/ofertas) + verificación propia. VTEX Intelligent Search pública sin auth; 69% del índice muerto → `hideUnavailableItems=true` obligatorio; Price=efectivo / ListPrice=regular (verificado 4/4 vs web renderizada).
- ✅ **Scraper** `targets/carrefour/scraper_pro.py` + `scrape_carrefour.py`: 11.285 productos (9 categorías súper), 100% EAN/precio/imagen, 3.573 con oferta real (31%). Detecta descuento directo ("25% OFF") Y promos por cantidad ("2do al 50%", NxM) desde teasers; filtra "Tarjeta Carrefour 15%" (medio de pago, viene en el 100% de los productos). WARN si promos cantidad <5% (señal de cambio de nomenclatura).
- ✅ **Catálogo**: `cargar_coto()` generalizado a `cargar_cadena()` + merge de cadenas en loop (menos duplicación). **4.809 productos con precio Carrefour** (supera a Coto: 4.116), 1.624 con oferta activa, 3.146 con doble góndola, 5.779 con mayorista+cadena. Mayoristas intactos (6.591/4.735/4.140). Total: 13.275.
- ✅ **Verificación**: 3/3 precios del catálogo exactos contra la API legacy en vivo (endpoint independiente del scraper, lookup por EAN).
- ✅ **Frontend**: 1 línea en `FUENTES` + `carrefour.jpg` (logo completo que dejó Facu) — badge/toggle/góndola/exclusión de bombas salieron gratis de la arquitectura de Coto. `tsc` limpio.
- ✅ **Pipeline**: `pipeline_local.py` con carrefour en los 5 puntos (mínimo 3.000 matches); gate en vivo lo excluye estructuralmente. Docs: CLAUDE.md, 02-scrapers.md (sección Carrefour), HERRAMIENTAS.md, skill pipeline-datos (no tenía ni a Coto — corregido).
- 🟡 **PENDIENTE**: (a) commit+push de Coto+Carrefour juntos tras OK de Facu; (b) chequeo visual de vistas con datos Carrefour (mismo camino de render que Coto); (c) Fase B encolada: surtido exclusivo de cadenas (~6.5k Carrefour + ~11k Coto) con lazy-load; (d) sección "solo ofertas" en la app — ya hay data: 1.624 ofertas Carrefour + 7.287 Coto en catálogo.

## HECHO 05/07 — Coto integrado de punta a punta (plan `.claude/docs/plan-coto.md`)
- ✅ **Fase 1 — Scraper** `targets/coto/scraper_pro.py` + `scrape_coto.py`: 15.043 productos con stock, 100% EAN, 100% precio>0, 4/4 precios verificados exactos contra la web renderizada (Puppeteer).
- ✅ **Fase 2 — Catálogo**: `cargar_coto()` + merge por EAN en `main()` DESPUÉS de `construir_catalogo()` (así los outliers/validación cruzada nunca ven a Coto — más robusto que parchear 4 validaciones). 4.116 productos con precio góndola; los 3 mayoristas EXACTAMENTE iguales que antes (6.591/4.735/4.140); 0 productos con Coto como única fuente.
- ✅ **Fase 3 — `lib/data.ts`**: `tipoFuente: 'mayorista' | 'cadena'`, constante `FUENTES` (única fuente de verdad: clave+nombre+tipo+logo+url), `calcularBombas()` solo mayoristas.
- ✅ **Fase 4 — UI**: hardcodes reemplazados por `FUENTES` en los 7 componentes + `app/page.tsx`; toggle Todos/Mayoristas/Cadenas en catálogo (Cadenas → 4.116 ✓); Detalle separa "Dónde comprarlo" (mayoristas) del bloque "PRECIO GÓNDOLA · VENTA AL PÚBLICO"; calculadora muestra "igualando la góndola tu margen es N%"; bomba muestra línea GÓNDOLA; Perfil lista las 4 fuentes + preferencia "Uso la app como comerciante/consumidor" (setea el filtro default); Planes menciona Coto gratis. Logo: `public/mayoristas/coto.svg` (oficial, bajado del sitio — SVG, no png). `tsc` limpio. 6 vistas verificadas en vivo.
- ✅ **Fase 5 — Pipeline**: `pipeline_local.py` con Coto en los 4 puntos (conteo, scraper, mínimo 3.000 matches, limpieza). `verificar_precios_real.py`: candidatos ahora exigen 2+ MAYORISTAS (Coto no entra al gate); 258 candidatos disponibles.
- 🔴 **Dos errores del plan corregidos en ejecución** (documentados en `.claude/rules/02-scrapers.md`): (1) el precio es `listPrice`, NO `formatPrice` (que es precio por litro/kg — inflaba hasta 16x); (2) la API capea 10.000 resultados por categoría → Almacén se barre por subgrupos. Además se saltean productos sin `store_availability` (precios con años de antigüedad).
- 🟡 **PENDIENTE**: (a) commit + push del repo principal y del submódulo (deploy Vercel) — esperar OK visual de Facu; (b) `npm run lint` está roto DE ANTES (eslint no está en devDependencies del submódulo — el script existe pero el paquete no); (c) Fase B encolada: ~11k productos exclusivos de Coto con lazy-load.

## HECHO 05/07 (ronda 2, feedback de Facu) — Ofertas de Coto + rediseño del detalle
- 🔴 **Facu atrapó a ojo**: mostrábamos el precio REGULAR de Coto ($11.509 en Fernet Buhero) pero la web lo vende con 30%Dto a $8.056,30. Medido: **~48-55% de la góndola de Coto tiene oferta activa** — no era un caso raro.
- ✅ **Fix**: el scraper ahora captura `discounts[].discountPrice` → `precio` = EFECTIVO (lo que paga el público hoy), `precio_regular` + `oferta` ("30%Dto") como campos extra que viajan hasta el frontend (`Precio.precioRegular` / `Precio.oferta`). Re-scrapeado (15.035 prods, 7.287 con oferta) y verificado: Fernet Buhero da $8.056,30 exacto.
- ✅ **Rediseño "Dónde comprarlo"** (pedido de Facu: "discriminar por competidor pero que se vea ahí mismo todo"): una sola sección con sub-encabezados "MAYORISTAS · PRECIO DE COMPRA" y "SÚPER · VENTA AL PÚBLICO", filas del mismo formato; la fila Coto muestra oferta verde + precio de lista tachado. Chau placa gris separada.
- ✅ **Logo oficial de Coto que dejó Facu** (`Downloads/Logo_Supermercado_Coto.svg.webp`) instalado como `public/mayoristas/coto.webp` (borrados el `coto.svg` del header y el `COTO.jpg` duplicado).
- 🟡 **ENCOLADO (pedido de Facu)**: capturar lista + oferta también para **MaxiCarrefour** — mismo patrón (precio efectivo + precio_regular + oferta en `fuentes.maxicarrefour`).

## Hecho 04/07 — Rediseño categorías deployado y verificado en prod
- ✅ **Tarjeta nueva 170×210**: 2 packshots (hero + escolta) escalados por medida real de píxeles,
  rotación crossfade, badge "hasta -N% hoy" (mismo criterio que calcularBombas). Componentes:
  `categoria-card.tsx`, `h-scroll.tsx` (flechas desktop en los 4 carruseles), `lib/categoria-fotos.ts`.
- ✅ **Fotos de Facu** (5 categorías, locales en `public/categories/productos/`); flujo repetible:
  carpetas MAYÚSCULAS en public/ → `node design-lab/procesar-fotos-categorias.js` (mide bbox con sharp).
- ✅ Deploy verificado en prod con Puppeteer (10 tarjetas, badges reales). Commits: submódulo `f7a60a5`, principal `bb58f74`.
- 🟡 **PENDIENTE**: Facu carga carpetas BAZAR / CONGELADOS / KIOSCO / MASCOTAS / DESAYUNO (4 fotos c/u)
  — esas 5 categorías usan fotos del catálogo como relleno temporal.

## ESTADO ACTUAL — Scrapers y catálogo (01/07/2026)
- ✅ **Yaguar**: 6.587 precios — fresco de hoy, verificado 20/20 contra la web
- ✅ **MaxiCarrefour**: 4.735 precios — **fresco de hoy** (cookies renovadas automáticamente, auto-click OK), verificado 20/20
- ✅ **Maxiconsumo**: 4.052 precios — fresco de hoy, verificado 20/20
- ✅ **Catálogo**: 13.186 con precio, 1.885 con 2+ precios, 303 con 3 precios
- ✅ **Verificación en vivo**: 60/60 (100%) — primera vez con las 3 fuentes verificadas
- ✅ **Push a Vercel**: hecho (commit 9589305 en submódulo)

## INCIDENTE RESUELTO 01/07 — MCF publicó 11 días precios del 20/06
Cadena de 4 agujeros alineados (detalle en `.claude/rules/02-scrapers.md`):
Carrefour cambió la señal de sesión muerta (`item_card_public` → `data-price="private"`)
→ `_cookies_vigentes()` daba falso vigente → scraper fallaba a diario → catálogo reciclaba
output viejo con fecha honesta → anti-reciclaje (cuenta precios, no frescura) publicaba
→ verificador MCF roto (endpoint VTEX muerto) + exit code ignorado = nadie se enteró.

## PIPELINE ENDURECIDO 01/07 — qué cambió
- **`scrape_maxicarrefour.py`**: `_cookies_vigentes()` detecta `data-price="private"` → auto-renovación pre-scrape (sin humano en el caso común)
- **`scripts/verificar_precios_real.py`**: parsers arreglados (MCO: dataLayer GTM; MCF: endpoint buscador + formato inglés de precio), exit codes 0/1/2, desglose de no-verificados
- **`pipeline_local.py`**: gate pre-push (diverge → NO publica), frescura por fuente (>3 días → alerta), `alertar()` → `data/quality/ALERTA.md` + beep
- **`/inicio-sesion`**: paso 0 = leer ALERTA.md
- **Tarea Windows**: WakeToRun activado + wake timers habilitados (AC) — corre 10am aunque la PC duerma
- La verificación ya NO corre dentro de `scrape_maxiconsumo.py` (corría 2 veces, exit ignorado)

## PRÓXIMOS PASOS
1. 🟢 Mañana 10am: primera corrida del pipeline endurecido — revisar `data/quality/pipeline_local.log` y `ALERTA.md`
2. 🟡 Yaguar Bebidas da 404 en pág 9 — URL cambió, revisar en `targets/yaguar/scraper_pro.py` (backlog)

## RETOMAR ACÁ — DISPARADOR: "continuemos con el mensaje para los clientes"
**Sistema de outreach con PANEL de control (ver memoria `project_outreach_primer_pagador` + `.claude/docs/playbook-outreach.md`).**

**PANEL DE OUTREACH v3 (15/06 tarde) — COMPLETO:** `scripts/generar_panel_outreach.py` genera
`data/outreach/panel_outreach.html` (autocontenido, se abre solo, portable al celu). Estética Brújula v2
(Poppins, hairlines, placas, dorado sparse). Por comercio:
- **Foto REAL del local** (scrapeada de Google Maps con Puppeteer MCP, sin API key, bajada a `data/outreach/fotos/`).
- Datos, dirección, **logo Google Maps clickeable**, redes y teléfono.
- **Material con buscador autocompletado** sobre POOL de ~759 productos validados (escribís → saltan opciones).
  Al elegir: mensaje, foto del producto, ahorro y **los 3 links de mayoristas (Yaguar/Maxiconsumo/MaxiCarrefour)
  con precio** se actualizan solos. Cada link verifica el precio en vivo. + chips de atajo por comercio.
- **Botón "Reportar precio incorrecto"** → entra en el Exportar para que Claude lo verifique.
- Mensaje editable + Aprobar / Copiar / **Abrir canal** (wa.me con texto cargado / ig.me / m.me) / Marcar enviado.
- Estado, material, ediciones y reportes sincronizados en **Vercel Blob** (cloud) — accesible desde cualquier dispositivo.
- Fallback a localStorage si hay error de red.
- API route: `BRUJULA-DE-PRECIOS/app/api/outreach/route.ts` (GET/POST, protegida por `OUTREACH_PW` env var).
- **URL en producción:** `https://v0-brujula-de-precios.vercel.app/outreach.html?pw=[clave]`
- Para regenerar el panel (ej: nuevos comercios): `python scripts/generar_panel_outreach.py` → genera en `data/outreach/` Y en `BRUJULA-DE-PRECIOS/public/` → commitear y pushear.
- Rediseño desktop (18/06): 2 columnas, ficha de cliente a la derecha (foto 220px, filas de contacto con íconos, badge principal/celular/fijo), trabajo a la izquierda. Mobile: compacto con foto pequeña.
Verificado con screenshot (Puppeteer): se ve impecable. Las 3 fachadas confirmadas (HLY, San Cayetano, Urquiza).

**AMPLIACIÓN DE COMERCIOS (16-17/06):** barrido masivo con subagentes (Maps + directorios web + redes
sociales) en zona cercana a la casa de Facu (ver memoria PRIVADA `user_direccion_facu`). Resultado
consolidado en `data/outreach/comercios_consolidado.json`: **105 comercios únicos** → **27 contactables
por DM** (WhatsApp/IG/FB), 54 solo fijo, 24 sin contacto.
- `scripts/consolidar_candidatos.py` une las 4 fuentes (zonanorte + candidatos_web1/maps/web2), dedup por
  nombre+zona y por dirección (cazó HLY duplicado), rankea digitales primero. Genera comercios_consolidado.json.
- El panel ahora carga `comercios_consolidado.json` (preferido si existe): **27 digitales** rankeados.
- Fotos del local: subagente sacó 17 `foto_url`; descargadas a `data/outreach/fotos/` y seteado `foto_local`.
  **Panel regenerado y verificado: 27 comercios, 17 con foto del local.** Los 10 sin foto muestran botón a Maps.
  Búsqueda CORTADA por Facu (suficientes para arrancar). Para sumar más: re-correr barrido + `consolidar_candidatos.py`.
- OJO (aviso del agente Maps): de los 14 WhatsApp, solo 2 son celular 100% confirmado; el resto inferido
  por prefijo. VERIFICAR cada número antes de mandar el primer mensaje.

Base anterior: `data/outreach/comercios_zonanorte_20260615.json` (10, los 3 originales con foto ya verificada).

Próximos pasos (en orden):
1. **Facu revisa el panel ampliado** (27 comercios) y **EMPIEZA A MANDAR** (Abrir WhatsApp/DM → enviar → Marcar enviado).
   Verificar el número de WhatsApp antes de cada envío. Follow-up 1 vez a los 3-4 días.
3. Si reporta precios → exportar JSON → Claude verifica y corrige catálogo.
4. Pendiente estratégico (NO ahora): palanca de grupos de comerciantes en FB/WhatsApp + video de ahorro.

(backlog técnico) Sector Bebidas de Yaguar da 404 — cambió la URL; revisar en `targets/yaguar/scraper_pro.py`.

(backlog técnico) Sector Bebidas de Yaguar da 404 — cambió la URL; revisar en `targets/yaguar/scraper_pro.py`.

## Hecho 17/06 — iconos del drawer de catálogo (deployado a prod)
- ✅ **Menú de categorías con iconos de línea uniformes.** `components/category-drawer.tsx`:
   fuera thumbnails PNG + emoji (inconsistentes) → iconos lucide, uno por sector, dentro de chip
   con tinte pastel ATENUADO (B2 atenuado, aprobado por Facu tras comparar 3 variantes en preview HTML).
   Mapa `SECTOR_ICONS` (icono + bg + fg por sector) + fallback neutro `Package`.
- Los PNG de `/categories/` NO se borraron: `vista-inicio.tsx` los sigue usando.
- Verificado: `npx tsc --noEmit` OK + deploy Vercel `dpl_GQKV7R4...` BUILDING→prod con commit `74691fe`.
- Deploy del frontend = push a `main` del SUBMÓDULO `BRUJULA-DE-PRECIOS` (repo propio, Vercel linkeado ahí).

## Hecho 14/06 (TARDE) — deployado y verificado en navegador real
- ✅ **Tarea automática CREADA** en Programador de Windows: "Brujula - Actualizar precios", diaria
   10:00, StartWhenAvailable (corre apenas se prende la PC si se perdió la hora), usuario Facun.
   Facu no tiene que tocar nada. Autonomía total lograda.
- ✅ **Railway BORRADO** (proyecto eliminado, no solo cancelado). Limpieza: borrado
   `scripts/notify_railway.py` (huérfano) + `_sincronizar_railway()` de `renovar_cookies_carrefour.py`.
- ✅ **Indicador de frescura FUNCIONANDO en prod** — estaba muerto porque Railway subía catálogo SIN
   `dias_desde_scraping` (0/18.662 fuentes). El catálogo local sí lo trae → puntito "Hoy" visible.
- ✅ **Título de pestaña** cambiado a "Brújula de Precios" (era "Brújula Mayorista").
- ✅ **Links de los 3 mayoristas arreglados y verificados:**
   - Yaguar: directo a ficha (ya estaba).
   - Maxiconsumo: directo a ficha SIN prefijo `/sucursal_burzaco/` (eso daba Forbidden). Verificado por Facu.
   - MaxiCarrefour: HÍBRIDO. Carrefour rota EANs, su buscador resuelve ~48%. `_carrefour_links_hibrido()`
     verifica cada EAN contra la API del buscador → `/search/{ean}` directo si existe, `/search/{nombre}`
     si no (nunca pantalla vacía). 2.366 directo / 2.487 fallback. Integrado en el pipeline.
- ⚠️ Lección: NO generalizar de 1 caso. Probé el link MC con el Buhero (caso raro de EAN cambiado),
   concluí mal que `/search/{ean}` estaba roto y cambié todo a nombre = regresión. Medir con muestra.

## Hecho 14/06 (mañana, deployado y verificado)
- ✅ **Railway dado de baja** (subscription cancelada, vence 28/06, no se renueva).
- ✅ **Los 3 mayoristas frescos** desde la PC: MaxiCarrefour 100% (14/06), Maxiconsumo 97%,
   Yaguar 90%. Stale total bajó de ~13.900 a ~870. Catálogo: 17.875 productos.
- ✅ **Cookies MaxiCarrefour renovadas** (14/06) — el modo Chrome automático SÍ puede pasar la
   traba solo (hoy salió). Si falla, un click de Facu en la ventana alcanza.
- ✅ **Carteles de frescura DEPLOYADOS** en producción (commit `aeebc67`).
- 🐛 2 bugs cazados y arreglados: (a) crash de encoding cp1252 (emojis) → `set PYTHONUTF8=1` en
   `.bat` y `pipeline_local.py`; (b) `encontrar_mejor()` priorizaba archivo viejo grande sobre
   fresco → cambiado a tolerancia 70% (recencia manda).
- ⚠️ Aprendizaje: NO mergear `catalogo_unificado.json` con git (mezcla 2 versiones). Si el
   remoto avanzó, regenerar con `actualizar_catalogo.py` y pisar, no `git pull -X ours`.

## Trabajo 13/06 — Autonomía y confiabilidad de datos (plan aprobado, 3 fases hechas)

## Trabajo 13/06 — Autonomía y confiabilidad de datos (plan aprobado, 3 fases hechas)

**Causa raíz de "mi app dice X, el link dice Y":** matching de cantidad + datos viejos
mostrados como frescos + scraping no confiable en la nube. Resuelto así:

- ✅ **Fase 1 — Confiabilidad (Python).** `actualizar_catalogo.py`: helper
  `extraer_fecha_de_timestamp()` inyecta fecha del nombre del archivo cuando el producto
  no la trae → fuentes sin fecha de ~1.900 a **0**. Umbral stale 30→**14 días**.
  `dias_desde_scraping` se setea siempre. Exit codes arreglados en `scrape_yaguar.py` y
  `scrape_maxiconsumo.py`. (Paso 6d de cantidad canónica ya estaba del trabajo previo.)
- ✅ **Fase 2 — Frescura visible (React).** `lib/data.ts`: interfaz `Precio` con
  `precioStale`/`diasDesdeScraping` + helper `frescuraDe()`. Componente
  `components/frescura-pill.tsx` (punto verde "Hoy" / gris "Hace N d" / ámbar viejo).
  Integrado en vista-detalle, bomba-list-item (inicio), vista-catalogo, vista-lista.
  `tsc --noEmit` OK. Bombas: no se excluyen por stale (vaciaría la home con datos viejos);
  el badge avisa y el re-scrapeo lo resuelve.
- ✅ **Fase 3 — Autonomía local, sin Railway.** `pipeline_local.py` (raíz): corre los 3
  scrapers (vía wrappers, que manejan cookies y enriquecimiento) → `actualizar_catalogo.py`
  → chequeo anti-reciclaje (aborta si el total cae >15% o una fuente queda en 0) → git push.
  `actualizar_brujula.bat` lo ejecuta (doble-click o Task Scheduler). Railway archivado en
  `archive/` (no borrado).

## Backlog (no urgente)
- ~34 `nombre_display` mal escritos (Quitamanchas "1.5 ml" → "1.5 L"). Cosmético, precio OK.
- Fase 4: nube 24/7 con proxy + CapSolver — solo cuando haya pagadores. Ver `archive/README.md`.

---

## Misión
Primer comerciante pagador. Todo lo que no acerque a eso es ruido.

---

## Estado actual

| Componente | Estado | Detalle |
|---|---|---|
| **Scraper Yaguar** | OK | Última corrida: 27/05/2026 — 12.664 productos |
| **Scraper MaxiCarrefour** | OK | Última corrida: 28/05/2026 — 5.067 productos. Precios verificados API: 5/5 OK |
| **Scraper Maxiconsumo** | OK | Última corrida: 28/05/2026 — 9.775 productos. 9.616 precios re-verificados con selector correcto |
| **Catálogo unificado** | ✅ DEPLOYADO | 18.075 productos, 2.917 con 2+ precios. Fix precios bulto MC aplicado. En producción. |
| **Frontend** | ✅ DISEÑO v2 EN PRODUCCIÓN | Deployado 11/06 (commit `64b336f`, Vercel READY). 6 vistas + mejoras post-aprobación: Inicio desktop calco Trolley (placa 360px medida con getComputedStyle), Top 20 rankeado (clase A × 3 precios × ahorro) con 6 deals + "Ver más", reveal de pills on-scroll 650ms, drawer con thumbnails + drill-down de subcategorías, LogoLoop en todas las resoluciones. Bug fuente Poppins resuelto. Nota: `npm run lint` no funciona — eslint nunca estuvo instalado (preexistente). |
| **Scraping automático** | ✅ LOCAL AUTOMÁTICO | Tarea Windows "Brujula - Actualizar precios" diaria 10:00 (StartWhenAvailable). `pipeline_local.py` + `actualizar_brujula.bat`. Railway BORRADO. |
| **Cookies MaxiCarrefour** | OK | Auto-renovación implementada 27/05/2026 — Chrome real + auto-click |
| **Outreach comerciantes** | 🔴 PENDIENTE | BLOQUEADOR REAL — nunca enviado |

---

## Bloqueador principal
**Outreach a comerciantes.** El código está listo, QA aprobado 6/6. Solo falta hablar con clientes.

---

## Próximos 3 pasos (en orden de impacto a ingresos)

1. **Outreach comerciantes** — `/buscar-comercios` → `/investigar-y-contactar` → `/enviar-outreach`. NUNCA enviado. BLOQUEADOR REAL — la app nueva ya está en producción como carta de presentación.
2. **Sesión de pipeline: nombres + fotos** — (a) script de limpieza de nombres: marca + nombre_limpio para los 18k productos (frontend listo para 2 líneas estilo Trolley); (b) fotos propias: descarga multi-fuente eligiendo mejor resolución → Cloudflare R2 (Facu crea la cuenta gratis, 10 min, guiado). Plan completo en memoria `project_fotos_productos`.
3. **Filtro outlier precios** — En `actualizar_catalogo.py`: si precio MC > 2.5x mediana → descartarlo. Ver `.claude/rules/08-precios-sin-stock.md`.

---

## Ideas en cola — NO tocar todavía

- NINI y VITAL (mayoristas nuevos)
- Mapa de ubicaciones con Google Maps
- Redefinir tiers (Free / Pro / Max)
- Mejoras profundas de diseño y textos
- Modal.com (scraper como URL pública)
- Railway cron automático

---

## Historial de sesiones recientes

| Fecha | Qué se hizo |
|---|---|
| 02-04/07/2026 | **Rediseño "Explorá por categoría" — iterado con Facu y deployado.** Proceso: 3 propuestas en mockup (design-lab) → Facu eligió collage vivo + badge de ahorro → iteración sobre UNA tarjeta (6 variantes → hero+escolta ganadora) → Facu curó sus propias fotos (fondo blanco, carpetas en public/) → medición de bbox por píxeles con sharp para escalado uniforme → implementación real + deploy verificado en prod. Además: flechas desktop en los 4 carruseles (h-scroll.tsx), categorías vacías ocultas, portadas estáticas viejas eliminadas. Skill impeccable actualizada a v3.9.1 (hook de diseño activo en cada write). Pendiente: fotos de Facu para Bazar/Congelados/Kiosco/Mascotas/Desayuno. |
| 19/06/2026 | **Panel outreach v4 — JS bug resuelto, en producción.** Causa raíz: en Python `'''...'''`, `\'` → `'` (backslash consumido), rompiendo todos los `onclick="fn(\'...\')"`. Fix definitivo: JS extraído a `scripts/panel_outreach_app.js` (sin Python de por medio), `rebuild_panel.py` lo lee e inyecta. Fix adicional: `checkPw()` usaba `.value` del input vacío en lugar del URL param → `|| params.get("pw")`. Verificado con Puppeteer: JS OK, 70 comercios, detalle abre, guarda en Vercel Blob. Todo listo para empezar a enviar. |
| 12/06/2026 (madrugada) | **CRISIS DATOS MC RESUELTA + todo deployado.** Facu detectó precios MC incorrectos → investigación: scraper MC fallaba en Railway desde 28/05 y `_fallback_mc_desde_catalogo()` reciclaba precios viejos PISANDO fecha con "hoy" (5.128 precios del 28/05 disfrazados de frescos). Fixes: (1) fallback conserva fecha real, (2) cookies renovadas + sincronizadas a Railway, (3) scraper MC local corrido (5.031 con precio) + parche quirúrgico `scripts/parchear_mc_catalogo.py` (solo MC, sin tocar Yaguar/MCO frescos de Railway) → 4.504 precios MC de hoy en producción (commit `297b692`). Branca confirmado: $15.349→$16.425. Diferencia residual Buhero ($10.015 vs $10.315 del portal de Facu) = percepciones IIBB +3% según CUIT del cliente → nota fiscal agregada al detalle (commit `da77e5a`, verificada en prod). RENOVACIÓN COOKIES GRATIS (Facu no quiere pagar CapSolver): tarea programada Windows diaria 20:00 (`renovar_cookies_diario.bat`) — chequea fecha, renueva solo si >25 días, beep si necesita click. FOTOS SIN CUENTAS: propuesta GitHub repo + jsDelivr CDN (gratis, sin registro nuevo) — pendiente OK de Facu. Verificación previa: 96.4% precios OK vs webs (27/28), trampa Yaguar pack x3 documentada en memoria. |
| 11/06/2026 (noche) | **6 FIXES UX + CALIDAD DE DATOS — commiteados, pendiente push.** Frontend (commit `1718999`): sidebar desktop con categorías desplegables (accordion), favoritos persistentes (localStorage + corazón header + chip Favoritos en catálogo), Mi Lista rehidratada contra catálogo del día (cálculos usaban precios congelados del snapshot), Toaster montado (el "+Lista" del Inicio funcionaba pero sin feedback — sonner nunca estuvo montado), labels del rango de precios anclados (se cortaban en mobile), `calcularBombas()` excluye ahorros >60%. Todo verificado con Chrome headless (`scripts/verificar-ux.mjs`, puppeteer-core nuevo devDep). Pipeline (commit `fca072a`): auditoría con agente auditor-catalogo encontró 23 outliers MC (bulto/sin stock, ej. Tulipán 11.3x) + 58 ahorros imposibles → paso 6f (MC >2.5x mediana → descartar, regla 08) + paso 6g (ahorro >60% → flag `precio_sospechoso`) + umbral 50x→10x commiteado al fin (estaba local desde 28/05 — POR ESO producción mostraba outliers). Reporte: `data/quality/auditoria_catalogo_2026-06-11.md`. Verificado: catálogo regenerado local con 0 ahorros >60% sin flag; catálogo fresco de Railway restaurado después de la prueba. PENDIENTE: push de ambos repos (BRUJULA → deploy Vercel con rebase previo por catálogos Railway; PRECIOS → rebuild imagen Railway para el cron de 6 AM). Facu debe crear cuenta Cloudflare R2 para la tanda fotos+nombres. |
| 11/06/2026 (cierre) | **DISEÑO v2 DEPLOYADO A PRODUCCIÓN.** Post-aprobación de Facu: Inicio desktop rediseñado calco Trolley (proporciones medidas con getComputedStyle en trolley.co.uk: placa 360×418 + gap 40 + info), Top 20 rankeado (clase A × 3 precios × ahorro) con 6 deals + "Ver más", reveal de pills on-scroll (650ms, pedido de Facu: lento), drawer v2 con thumbnails de categorías + drill-down de subcategorías (accordion grid-rows), LogoLoop restaurado en desktop (pedido de Facu), fixes de superposición (categorías flex-column, labels rango con fondo). Deploy: build local OK → commit → rebase sobre 14 días de catálogos Railway (conflicto resuelto a favor de Railway) → push → Vercel READY verificado por API. DESCUBRIMIENTO: el cron Railway corre hace 14 días commiteando catálogo diario (ESTADO decía "sin configurar" — corregido). Memoria actualizada: colaboración (proyecto de ambos), plan fotos R2, regla de rebase pre-push. PRÓXIMA SESIÓN: Facu define rumbo — recomendado outreach > pipeline nombres/fotos. |
| 10-11/06/2026 | **MIGRACIÓN DISEÑO v2 COMPLETA (local).** Bug fuente Poppins arreglado (`poppins.className` directo en body — `--font-sans` computaba vacía por conflicto :root vs @theme de Tailwind v4). Tokens claros (`--ink/--gray/--line/--plate/--gold/--green/--pill` + easings Emil) en `globals.css`, legacy vars eliminadas. Layout global: header nuevo (hamburguesa + logo B + wordmark), bottom-nav blanca con puntito dorado, `category-drawer.tsx` (curva iOS 400ms), `desktop-sidebar.tsx` simplificada. 6 vistas migradas verificando cada una con Puppeteer vs su mockup: Inicio (BombaHero + BombaRow + LogoLoop claro + categorías con foto), Catálogo (grid hairlines 2/4 col, chips dropdown, ClickSpark WAAPI en "+", sin logos en celdas), Detalle (sticky 500px desktop — fix overflow `min-width:0` en grid item, barra rango con anti-colisión de labels, insight auto-generado, calculadora con shuffle de dígitos), Mi Lista (ticket + toggle Productos/Dónde comprar + WhatsApp con plan mixto — fix: mix ahora multiplica por cantidad), Perfil (iOS groups, CountUp, banner upgrade), Planes (nueva vista: hero, toggle Mensual/Anual con shuffle, cards PRO/Gratis, sweep CTA, upgrade por WhatsApp). Limpieza: borrados `vista-ofertas`, `vista-comparativa`, `bomba-card`, `sidebar-nav`, `modal-producto`, `calculadora`, `pricing-section`, `impact-card`, `AnimatedList` (wrapper), `theme-provider`, `motion-variants`. Cero hex legacy en componentes. tsc OK. ESLint no instalado (preexistente). PENDIENTE: OK de Facu en local → deploy. |
| 09-10/06/2026 | **DESIGN LAB COMPLETO Y CERRADO.** Auditoría vs Trolley medida con Puppeteer (`auditoria-diseno-vs-trolley-2026-06-09.md`) → bug fuente producción detectado. Identidad clara estilo Trolley co-creada y aprobada vista por vista: Inicio, Catálogo (deals-style 4 col + drawer), Detalle (sticky + barra rango), Mi Lista (patrón ticket + toggle Productos/Dónde comprar), Perfil (iOS groups liviano), Planes (pantalla propia estilo 21st.dev con toggle Mensual/Anual). Logo: monograma B. Skills instaladas: `emil-design-eng` + `impeccable`. Efectos curados: LogoLoop, ClickSpark, CountUp, Shuffle, sweep CTA (resto descartado como ruido). 3 agentes de investigación usados (inspiración listas, pricing UI, perfil UX). Todo en `design-lab/` (7 archivos). Spec de migración: `.claude/docs/migracion-diseno-v2.md`. |
| 28/05/2026 (tarde) | **Sesión informativa + organización.** Investigación completa de novedades Claude: Opus 4.8 confirmado, Dynamic Workflows lanzados hoy (v2.1.154). WebFetch y WebSearch habilitados en settings.json del proyecto. Memoria actualizada: regla Jarvis automático (nunca esperar keywords), plan fotos Makro (Brújula), plan fotos trabajo día job (proyecto separado cuando Facu avise). Sin cambios al código de Brújula. |
| 28/05/2026 (noche v2) | **Rediseño BombaListItem — INCOMPLETO, continúa mañana.** Card completo clickable (sin botón "Ver producto"). Precios en filas verticales con badge "MEJOR" a la derecha del número en horizontal (dorado). Sección "VALORACIONES" con estrellas placeholder. Botones "+Lista" (conectado a `handleAgregarRapido`) y "Compartir" (Web Share API). Fallback dinámico de imágenes en BombaListItem y VistaDetalle. Open Food Facts como primer fallback en `lib/data.ts` (extrae EAN de URL Carrefour). Screenshot loop con Puppeteer verificó resultado. Referencia: `.claude/docs/seccion_ofertas.png` (Trolley.co.uk). Diseño visual pendiente de ajustes — mañana continuar. |
| 28/05/2026 (noche) | **Calidad de datos + patrón orquestador.** Scraper MC corrido (5.067 prods), precios verificados contra API: 5/5 OK. 3 agentes paralelos lanzados (primera vez patrón orquestador). Fix `encontrar_mejor`: prioriza recencia con 5% tolerancia. Fix precios stale: flag `precio_stale:true` para fuentes >30 días. Fix `cargar_yaguar`: 317 SKUs fantasma descartados — productos que Yaguar ya no tiene. Reglas `08-subagentes-verificacion.md` y `09-calidad-datos-catalogo.md` creadas. |
| 28/05/2026 (tarde) | **Verificación precios Yaguar completada.** Agente QA corrió scraper + verificó top 5 bombas con Puppeteer: 4/5 OK (diferencia $0), 1 URL rota (Salsa Pizza CICA discontinuada). Catálogo corregido: precio Yaguar → 0, fuente removida. Reporte en `data/quality/verificacion_yaguar_2026-05-28.md`. |
| 28/05/2026 | **Auto-renovación cookies MaxiCarrefour completada.** Chrome real + perfil persistente + auto-click pasa reCAPTCHA Enterprise 2/2. `_cookies_vigentes()` fix (fingerprint mismatch safari→chrome131). Los 3 scrapers corridos: 12.664+5.069+9.775 productos. Catálogo: 18.087 productos, 3.053 comparables. QA 6/6 VERDE. Fix doble buscador header. |
| 27/05/2026 | **Sistema Jarvis implementado.** ESTADO.md creado. `/inicio-sesion` skill creada. `06-jarvis-razonamiento.md` creado. CLAUDE.md actualizado con protocolo Jarvis + matriz de orquestación + lista completa de 7 agentes. `settings.json` global: beeps reales (800Hz/440Hz) + Agent Teams habilitado. `CLAUDE_CODE.MD` movida a `.claude/docs/raw/`. |
| 23/05/2026 | Scrapers corridos. Catálogo actualizado. |
