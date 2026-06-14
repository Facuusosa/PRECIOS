# Estado Vivo — Brújula de Precios
**Última actualización:** 14/06/2026 (DEPLOYADO: 3 mayoristas frescos + frescura visible en producción; Railway dado de baja)

## RETOMAR ACÁ (próxima sesión) — 2 pendientes + 1 backlog
1. **Tarea automática de la mañana (Programador de Windows)** — lo único que falta para autonomía
   total. Crear tarea que corra `actualizar_brujula.bat` ~7-9 AM con "ejecutar lo antes posible
   si se perdió el inicio". El .bat ya está probado y funciona.
2. **Link "Ver" de Maxiconsumo da "Forbidden"** al usuario (afecta ~9.500 productos). A mí desde
   afuera me carga; a Facu no → Maxiconsumo bloquea el deep-link sin sesión de sucursal. Para
   arreglar: que Facu pruebe la home `https://maxiconsumo.com/` y vea si pide elegir sucursal,
   y según eso cambiar el formato del link en `actualizar_catalogo.py`.
3. (backlog) **Sector Bebidas de Yaguar da 404** — cambió la URL; el scraper recicla los viejos.
   Revisar la URL del sector Bebidas en `targets/yaguar/scraper_pro.py`.

## Hecho 14/06 (deployado y verificado)
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
| **Scraping automático** | 🟡 LOCAL (pendiente Task Scheduler) | `pipeline_local.py` + `actualizar_brujula.bat`. Railway dado de baja (archivado en `archive/`) — fallaba en la nube. Falta crear la tarea en Programador de Windows. |
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
