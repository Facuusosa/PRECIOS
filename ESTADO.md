# Estado Vivo — Brújula de Precios
**Última actualización:** 28/05/2026 (madrugada — cierre sesión calidad datos Maxiconsumo)

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
| **Frontend** | OK — EN MEJORA | BombaListItem rediseñado (28/05 noche) — continúa mañana |
| **Railway scrapers automáticos** | ❌ SIN CONFIGURAR | Hobby $5/mes pagado, sin cron activo |
| **Cookies MaxiCarrefour** | OK | Auto-renovación implementada 27/05/2026 — Chrome real + auto-click |
| **Outreach comerciantes** | 🔴 PENDIENTE | BLOQUEADOR REAL — nunca enviado |

---

## Bloqueador principal
**Outreach a comerciantes.** El código está listo, QA aprobado 6/6. Solo falta hablar con clientes.

---

## Próximos 3 pasos (en orden de impacto a ingresos)

1. **Outreach comerciantes** — `/buscar-comercios` → `/investigar-y-contactar` → `/enviar-outreach`. NUNCA enviado. BLOQUEADOR REAL.
2. **Filtro outlier precios** — En `actualizar_catalogo.py`: si precio MC > 2.5x mediana de otras fuentes → descartarlo. Ver `.claude/rules/08-precios-sin-stock.md`.
3. **Railway cron** — Scrapers automáticos en la nube. Hobby $5/mes pagado, sin configurar.

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
| 28/05/2026 (noche v2) | **Rediseño BombaListItem — INCOMPLETO, continúa mañana.** Card completo clickable (sin botón "Ver producto"). Precios en filas verticales con badge "MEJOR" a la derecha del número en horizontal (dorado). Sección "VALORACIONES" con estrellas placeholder. Botones "+Lista" (conectado a `handleAgregarRapido`) y "Compartir" (Web Share API). Fallback dinámico de imágenes en BombaListItem y VistaDetalle. Open Food Facts como primer fallback en `lib/data.ts` (extrae EAN de URL Carrefour). Screenshot loop con Puppeteer verificó resultado. Referencia: `.claude/docs/seccion_ofertas.png` (Trolley.co.uk). Diseño visual pendiente de ajustes — mañana continuar. |
| 28/05/2026 (noche) | **Calidad de datos + patrón orquestador.** Scraper MC corrido (5.067 prods), precios verificados contra API: 5/5 OK. 3 agentes paralelos lanzados (primera vez patrón orquestador). Fix `encontrar_mejor`: prioriza recencia con 5% tolerancia. Fix precios stale: flag `precio_stale:true` para fuentes >30 días. Fix `cargar_yaguar`: 317 SKUs fantasma descartados — productos que Yaguar ya no tiene. Reglas `08-subagentes-verificacion.md` y `09-calidad-datos-catalogo.md` creadas. |
| 28/05/2026 (tarde) | **Verificación precios Yaguar completada.** Agente QA corrió scraper + verificó top 5 bombas con Puppeteer: 4/5 OK (diferencia $0), 1 URL rota (Salsa Pizza CICA discontinuada). Catálogo corregido: precio Yaguar → 0, fuente removida. Reporte en `data/quality/verificacion_yaguar_2026-05-28.md`. |
| 28/05/2026 | **Auto-renovación cookies MaxiCarrefour completada.** Chrome real + perfil persistente + auto-click pasa reCAPTCHA Enterprise 2/2. `_cookies_vigentes()` fix (fingerprint mismatch safari→chrome131). Los 3 scrapers corridos: 12.664+5.069+9.775 productos. Catálogo: 18.087 productos, 3.053 comparables. QA 6/6 VERDE. Fix doble buscador header. |
| 27/05/2026 | **Sistema Jarvis implementado.** ESTADO.md creado. `/inicio-sesion` skill creada. `06-jarvis-razonamiento.md` creado. CLAUDE.md actualizado con protocolo Jarvis + matriz de orquestación + lista completa de 7 agentes. `settings.json` global: beeps reales (800Hz/440Hz) + Agent Teams habilitado. `CLAUDE_CODE.MD` movida a `.claude/docs/raw/`. |
| 23/05/2026 | Scrapers corridos. Catálogo actualizado. |
