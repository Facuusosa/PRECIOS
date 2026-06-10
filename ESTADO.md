# Estado Vivo — Brújula de Precios
**Última actualización:** 09/06/2026 (sesión rediseño identidad — mockup aprobado + logo elegido)

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
| **Frontend** | 🎨 DESIGN LAB COMPLETO | Las 5 vistas aprobadas por Facu en `design-lab/`: Inicio (`propuesta-inicio-trolley.html`), Catálogo (4 col deals-style + drawer categorías), Detalle (sticky foto + barra rango + calculadora), Mi Lista (ticket + toggle "Dónde comprar"), Perfil (iOS groups + planes FREE/PRO con reglas de paywall-upgrade-cro). Logo: monograma B (`logo-brujula.svg`). PENDIENTE MIGRAR A LA APP. BUG CRÍTICO: fuente custom no se aplica en producción (`--font-sans` vacía). Auditoría: `.claude/docs/auditoria-diseno-vs-trolley-2026-06-09.md` |
| **Railway scrapers automáticos** | ❌ SIN CONFIGURAR | Hobby $5/mes pagado, sin cron activo |
| **Cookies MaxiCarrefour** | OK | Auto-renovación implementada 27/05/2026 — Chrome real + auto-click |
| **Outreach comerciantes** | 🔴 PENDIENTE | BLOQUEADOR REAL — nunca enviado |

---

## Bloqueador principal
**Outreach a comerciantes.** El código está listo, QA aprobado 6/6. Solo falta hablar con clientes.

---

## Próximos 3 pasos (en orden de impacto a ingresos)

1. **MIGRAR DISEÑO v2 A LA APP** — sesión completa dedicada. Spec lista en `.claude/docs/migracion-diseno-v2.md` (los mockups de `design-lab/` son la fuente de verdad). Arranca por el bug de la fuente. Al terminar: probar en localhost → deploy.
2. **Outreach comerciantes** — `/buscar-comercios` → `/investigar-y-contactar` → `/enviar-outreach`. NUNCA enviado. BLOQUEADOR REAL (con el diseño nuevo, mejor primera impresión).
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
| 09-10/06/2026 | **DESIGN LAB COMPLETO Y CERRADO.** Auditoría vs Trolley medida con Puppeteer (`auditoria-diseno-vs-trolley-2026-06-09.md`) → bug fuente producción detectado. Identidad clara estilo Trolley co-creada y aprobada vista por vista: Inicio, Catálogo (deals-style 4 col + drawer), Detalle (sticky + barra rango), Mi Lista (patrón ticket + toggle Productos/Dónde comprar), Perfil (iOS groups liviano), Planes (pantalla propia estilo 21st.dev con toggle Mensual/Anual). Logo: monograma B. Skills instaladas: `emil-design-eng` + `impeccable`. Efectos curados: LogoLoop, ClickSpark, CountUp, Shuffle, sweep CTA (resto descartado como ruido). 3 agentes de investigación usados (inspiración listas, pricing UI, perfil UX). Todo en `design-lab/` (7 archivos). Spec de migración: `.claude/docs/migracion-diseno-v2.md`. |
| 28/05/2026 (tarde) | **Sesión informativa + organización.** Investigación completa de novedades Claude: Opus 4.8 confirmado, Dynamic Workflows lanzados hoy (v2.1.154). WebFetch y WebSearch habilitados en settings.json del proyecto. Memoria actualizada: regla Jarvis automático (nunca esperar keywords), plan fotos Makro (Brújula), plan fotos trabajo día job (proyecto separado cuando Facu avise). Sin cambios al código de Brújula. |
| 28/05/2026 (noche v2) | **Rediseño BombaListItem — INCOMPLETO, continúa mañana.** Card completo clickable (sin botón "Ver producto"). Precios en filas verticales con badge "MEJOR" a la derecha del número en horizontal (dorado). Sección "VALORACIONES" con estrellas placeholder. Botones "+Lista" (conectado a `handleAgregarRapido`) y "Compartir" (Web Share API). Fallback dinámico de imágenes en BombaListItem y VistaDetalle. Open Food Facts como primer fallback en `lib/data.ts` (extrae EAN de URL Carrefour). Screenshot loop con Puppeteer verificó resultado. Referencia: `.claude/docs/seccion_ofertas.png` (Trolley.co.uk). Diseño visual pendiente de ajustes — mañana continuar. |
| 28/05/2026 (noche) | **Calidad de datos + patrón orquestador.** Scraper MC corrido (5.067 prods), precios verificados contra API: 5/5 OK. 3 agentes paralelos lanzados (primera vez patrón orquestador). Fix `encontrar_mejor`: prioriza recencia con 5% tolerancia. Fix precios stale: flag `precio_stale:true` para fuentes >30 días. Fix `cargar_yaguar`: 317 SKUs fantasma descartados — productos que Yaguar ya no tiene. Reglas `08-subagentes-verificacion.md` y `09-calidad-datos-catalogo.md` creadas. |
| 28/05/2026 (tarde) | **Verificación precios Yaguar completada.** Agente QA corrió scraper + verificó top 5 bombas con Puppeteer: 4/5 OK (diferencia $0), 1 URL rota (Salsa Pizza CICA discontinuada). Catálogo corregido: precio Yaguar → 0, fuente removida. Reporte en `data/quality/verificacion_yaguar_2026-05-28.md`. |
| 28/05/2026 | **Auto-renovación cookies MaxiCarrefour completada.** Chrome real + perfil persistente + auto-click pasa reCAPTCHA Enterprise 2/2. `_cookies_vigentes()` fix (fingerprint mismatch safari→chrome131). Los 3 scrapers corridos: 12.664+5.069+9.775 productos. Catálogo: 18.087 productos, 3.053 comparables. QA 6/6 VERDE. Fix doble buscador header. |
| 27/05/2026 | **Sistema Jarvis implementado.** ESTADO.md creado. `/inicio-sesion` skill creada. `06-jarvis-razonamiento.md` creado. CLAUDE.md actualizado con protocolo Jarvis + matriz de orquestación + lista completa de 7 agentes. `settings.json` global: beeps reales (800Hz/440Hz) + Agent Teams habilitado. `CLAUDE_CODE.MD` movida a `.claude/docs/raw/`. |
| 23/05/2026 | Scrapers corridos. Catálogo actualizado. |
