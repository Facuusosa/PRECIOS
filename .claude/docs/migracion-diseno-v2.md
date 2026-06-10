# Migración Diseño v2 — Design Lab → App Real

**Estado:** LISTO PARA EJECUTAR. Diseño aprobado por Facu el 09-10/06/2026.
**Objetivo:** que `localhost:3000` se vea EXACTAMENTE como los mockups de `design-lab/`.
**Los mockups son la spec.** Ante cualquier duda visual, abrir el mockup en el navegador y copiar valores exactos de su CSS.

---

## Fuente de verdad (design-lab/)

| Mockup | Vista de la app | Componente destino |
|---|---|---|
| `propuesta-inicio-trolley.html` | Inicio / Para Ti | `components/vista-inicio.tsx` + `bomba-list-item.tsx` |
| `propuesta-catalogo.html` | Catálogo | `components/vista-catalogo.tsx` (+ drawer nuevo) |
| `propuesta-detalle.html` | Detalle producto | `components/vista-detalle.tsx` |
| `propuesta-lista.html` | Mi Lista | `components/vista-lista.tsx` |
| `propuesta-perfil.html` | Perfil | `components/vista-cuenta.tsx` |
| `propuesta-planes.html` | Planes (PANTALLA NUEVA) | crear `components/vista-planes.tsx` |
| `logo-brujula.svg` | Logo monograma B | `public/icon.svg` + favicon + header |

## Tokens nuevos (reemplazan los oscuros en `app/globals.css`)

```css
--ink: #1a1a1a;        /* texto principal */
--gray: #808080;       /* texto secundario (ÚNICO gris de texto) */
--line: #ececec;       /* hairlines, borders */
--plate: #f6f5f3;      /* placas de imagen de producto */
--gold: #c89055;       /* acento único (saturado para fondo claro; reemplaza #d4a574) */
--gold-deep: #b07a3f;  /* gradiente de CTA dorado */
--green: #15803d;      /* SOLO ahorro/éxito */
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);  /* easing global (Emil) */
/* Fondo de la app: #ffffff. Pills negras: #111. */
```

Tipografía: Poppins única familia (Trolley usa Poppins — Barlow Condensed queda OBSOLETA, remover de layout.tsx).
Escala medida de Trolley (ya existe en globals.css): h1 25.7/600, sección 23.58/600, marca 21.44/600, producto 19.3/300-400, precio grande 600-700, pills 13.9/600. `font-variant-numeric: tabular-nums` en todo precio.

## Orden de ejecución (con verificación por paso)

1. **BUG FUENTE (primero, sí o sí):** en producción `--font-sans` computa vacía → app entera en fuente de sistema. Debug: conflicto entre `:root` custom y `@theme` de Tailwind v4 en `app/globals.css:73`. Fix robusto: aplicar `poppins.className` directo en `<body>` (layout.tsx) además de la variable. Verificar con Puppeteer: `getComputedStyle(document.body).fontFamily` debe incluir "Poppins".
2. **Tokens:** reescribir paleta en `globals.css` (variables de arriba). La app va a quedar "rara" hasta migrar componentes — avisar a Facu que es transitorio dentro de la sesión.
3. **Layout global:** header nuevo (hamburguesa + logo B SVG + "Brújula de precios" + íconos), bottom-nav blanca con blur y puntito dorado en activo, drawer de categorías (curva `cubic-bezier(0.32,0.72,0,1)` 400ms). Logo: copiar SVG de `design-lab/logo-brujula.svg`.
4. **Vista por vista en este orden** (cada una: migrar → `npx tsc --noEmit` → screenshot Puppeteer vs mockup → seguir): Inicio → Catálogo → Detalle → Mi Lista → Perfil → Planes (nueva).
5. **Limpieza:** borrar `vista-comparativa.tsx` (vista muerta, inalcanzable — verificado 09/06), `vista-ofertas.tsx` si sigue duplicando Inicio, `bomba-card.tsx` si quedó huérfana. `themeColor` en layout.tsx: `#006d38` → `#ffffff`.
6. **QA final:** recorrido completo + `npm run lint` + calculadora end-to-end.

## Decisiones de diseño NO negociables (aprobadas por Facu)

- **Claro, no oscuro.** Fotos de producto sobre placa `--plate` con `mix-blend-mode: multiply` (en blanco se integran solas).
- **Grid catálogo SIN logos de mayoristas**: solo mejor precio + "Ahorrás X% · 3 precios" en verde. Desktop: 4 columnas, placas grandes (280px), gaps 34/24, sidebar nav izquierda, max-width 1500px.
- **Detalle desktop:** imagen 500px sticky izquierda (OJO: ningún ancestro con `overflow: hidden` — mata el sticky), TODO lo scrolleable a la derecha incluyendo "De la misma categoría". Barra de rango de precios (degradé verde→dorado→rojo apagado, dots con precio) + calculadora de margen CONVIVEN.
- **Mi Lista = ticket** con header sticky (total + "Ahorrás $X" siempre visibles) y toggle **"Productos" / "Dónde comprar"** (nunca "plan de compra" ni "paradas" — es "mayoristas"). Modo Dónde comprar: ranking un-solo-lugar + card borde dorado "COMPRÁ EN VARIOS PARA AHORRAR MÁS" agrupada por mayorista. CTA cambia a "Enviar por WhatsApp".
- **Perfil liviano**: header rico (avatar+stats CountUp) + banner dorado de upgrade + grupos iOS (Mi negocio / Mis mayoristas con frescura del dato / Avisos / Ayuda). SIN sección de planes inline.
- **Planes = pantalla aparte**: título grande, toggle Mensual/Anual ("Ahorrá 20%", shuffle de dígitos al cambiar), PRO destacada dorada con RECOMENDADO + sweep de brillo en CTA, Gratis con candados. Precio $4.999 es PLACEHOLDER (tiers sin definir).
- **VALORACIONES vacías: eliminadas** hasta tener data. En su lugar, insight de precio auto-generado (ej: "Maxiconsumo está 72% por encima del mejor").
- **Efectos aprobados y dónde**: LogoLoop (Inicio), ClickSpark dorado en "+" (Catálogo), CountUp (stats Perfil/Inicio), Shuffle de precio (Planes y slider del Detalle), sweep en CTA PRO. NADA MÁS — Particles/Aurora/cursores custom prohibidos. Todo respeta `prefers-reduced-motion` y las reglas de `/emil-design-eng` (skill instalada).
- Textos en lenguaje de mostrador: "más barato", "ahorrás", "dónde comprar" — cero jerga.

## Reglas durante la migración

- Cero hex hardcodeado en componentes: todo `var(--token)`. Grep final de `#[0-9a-f]{3,6}` en `components/` (excepto `reactbits/` y `ui/`) debe dar solo tokens.
- Skills a usar: `/emil-design-eng` para cada animación; `/impeccable` para crítica de cada vista terminada.
- ReactBits ya integrados disponibles: CountUp, AnimatedList, BlurText, SpotlightCard. SplitText NO (requiere GSAP premium).
- Datos: `calcularBombas()` y estructura en `lib/data.ts` no se tocan; el Top 20 sale de ahí.

## Pendientes que NO son de esta migración (cola)

- Tiers/precios reales (decisión de negocio de Facu)
- "Avisarme de bombas" funcional (hoy toggle dummy)
- Histórico de precios estilo "Today's Price" de Trolley (necesita semanas de scraping)
- Auth real (email/password PRO)
