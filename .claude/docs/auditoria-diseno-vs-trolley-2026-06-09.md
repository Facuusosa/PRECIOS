# Auditoría de diseño: Brújula vs Trolley — 09/06/2026

**Método:** Puppeteer sobre producción (`v0-brujula-de-precios.vercel.app`) y `trolley.co.uk`,
viewport mobile 390px + desktop 1280px. Estilos medidos con `getComputedStyle()`, no a ojo.

---

## Números lado a lado (misma cantidad de pantalla)

| Métrica | Trolley | Brújula | Lectura |
|---|---|---|---|
| Colores de texto distintos | **3** (negro, blanco, gris) | **8** (4 grises distintos: `#6b7280`, `#555`, `#444`, `#ccc` + 2 blancos + dorado + negro) | Ruido |
| Fondos distintos | 6 | 10+ | Ruido |
| Elementos con borde | **10** | **37** | Ruido — Brújula encajona todo |
| Font-weights usados | 100–600 (mayoría 400/600) | 400–900 (mayoría 700/800/900) | Todo grita = nada destaca |
| Fuente aplicada | Poppins ✓ | **ui-sans-serif (fuente del sistema)** | LA identidad, rota |
| Acentos de color | 1 (púrpura) + pills negras | 5+ (dorado, azul "Ver", verde "Mejor precio", gradiente verde→rojo, logos full-color) | Sin identidad |

---

## Top 5 problemas (por impacto)

### 1. La tipografía custom NO se aplica en producción — bug CSS
- `document.fonts`: Poppins registrada (20 variantes) pero `unloaded` — nunca usada.
- `--font-poppins` llega bien al `<body>` (next/font OK: `"Poppins","Poppins Fallback"`).
- **`--font-sans` computa VACÍA en el body** → `font-family: var(--font-sans)` inválida → hereda el stack default de Tailwind (`ui-sans-serif, system-ui...`).
- El CSS deployado contiene DOS definiciones de `--font-sans`: la default de Tailwind y la custom (`var(--font-poppins),"Poppins",sans-serif`) — la custom pierde la cascada.
- Barlow Condensed (precios display) tampoco se renderiza.
- **Consecuencia:** toda la app se ve en la fuente genérica del sistema. Esto solo explica gran parte del "genérico de IA".
- Fix: debuggear la cascada en `app/globals.css:73` (probable conflicto `:root` vs `@layer theme` de Tailwind v4). Alternativa robusta: aplicar `poppins.className` directo o `font-family` explícita en `body`.

### 2. Logos de mayoristas a todo color repetidos en cada card del grid
- Cada card del catálogo: 3 logos full-color (Yaguar amarillo, MAXI azul, Maxiconsumo rojo/azul) → un grid visible tiene 12–18 logos gritando entre sí. Es la fuente #1 del "ruidoso" en catálogo.
- Trolley en grid NO muestra tiendas: solo marca, nombre, estrellas, **un** precio y per-unit. Los logos (chiquitos, contenidos) viven solo en el detalle ("Available at" / "Where To Buy").
- Decisión de diseño a tomar: el grid vende el *producto y su mejor precio*; la comparación vive en el detalle.

### 3. Duplicaciones estructurales (confunden y ensucian)
- **Categorías 2 veces** en Catálogo desktop: sidebar izquierda (11 ítems, mezcladas con navegación Para Ti/Mi Lista/Perfil) + chips arriba del grid (los mismos 11). El "ruido de las categorías del costado" que siente Facu es literal: es la misma información dos veces + navegación mezclada con filtros.
- **Buscador 2 veces**: header + dentro de la página de catálogo.
- **Card "Almacén" con el texto duplicado**: la imagen es un placeholder blanco con la palabra "Almacén" + el label "Almacén" abajo. Bebidas/Frescos tienen foto pero estilos de fondo inconsistentes entre sí.
- **"Ver todas las ofertas"** lleva a una vista visualmente idéntica al Inicio (mismo header "TOP Bombas Semanal", mismas stats) — no aporta nada nuevo.
- **VistaComparativa es inalcanzable**: `onVerComparativa` llega como prop a `vista-detalle.tsx:25` pero nunca se invoca — vista muerta (además es blanca, rompería el theme si apareciera).

### 4. Acentos de color sin sistema
- Conviven: dorado `#d4a574` (CTA, badges), **azul** botones "Ver" en detalle, **verde** badge "Mejor precio", **gradiente verde→rojo** (barra de rango de precio), logos full-color, `themeColor: '#006d38'` (verde viejo) en `app/layout.tsx:29`.
- Trolley: púrpura de marca + pills negras + azul SOLO en "VISIT". Todo lo demás es blanco/negro/gris.
- En detalle mobile: "MaxiCarrefou r" y "Maxicons umo" cortan palabras (ancho de columna mal calculado).

### 5. Vacíos y placeholders en producción
- "VALORACIONES ☆☆☆☆☆ Sin valoraciones aun" aparece en CADA bomba del Inicio — sección sin valor que se repite N veces (ruido + sensación de app vacía). Trolley solo muestra "What people say" cuando hay reseñas reales (con quote de usuario).
- Mi Lista vacía: 80% pantalla negra, ícono gris chico. Empty state sin onboarding visual.
- Búsqueda del header colapsada muestra "B ||||" (texto cortado + ícono barcode apretado) en 390px.

---

## Lo que Trolley hace bien y es copiable barato

1. **Las imágenes de producto flotan sobre el fondo** — sin caja con borde alrededor. Brújula mete cada foto en un bloque blanco con esquinas que pelea contra el fondo negro. (Con fondo oscuro: o se recortan las fotos a PNG o se acepta el bloque claro pero sin borde extra.)
2. **Pills negras de alto contraste** para badges ("Save £2.03", "82% Cheaper", "190G") — un solo estilo de badge para todo, siempre el mismo.
3. **Jerarquía por peso, no por color**: marca en 600, nombre en 300-400, precio grande 600. Brújula usa 700-900 en casi todo.
4. **Logos de tiendas en miniatura** en una fila horizontal con el precio debajo (mobile detalle: "Available at"). Una fila = toda la comparación.
5. **Aire**: separación entre secciones por whitespace, no por bordes/cajas.

---

## Quick wins ordenados (estimación de impacto vs esfuerzo)

| # | Acción | Impacto | Esfuerzo |
|---|---|---|---|
| 1 | Arreglar la fuente (bug `--font-sans`) | ALTÍSIMO — cambia toda la app | ~30-60 min |
| 2 | Grid catálogo: solo mejor precio + badge "3 precios" (logos fuera del grid) | ALTO — mata el ruido principal | ~1 h |
| 3 | Ocultar sección VALORACIONES hasta tener data real | MEDIO — menos ruido/vacío por card | ~15 min |
| 4 | Unificar acento: matar azul "Ver", verde "Mejor precio" → sistema dorado + pills | MEDIO | ~1 h |
| 5 | Rediseñar cards de categorías (foto real + un label + mismo tratamiento de fondo) | MEDIO — es lo que pidió Facu del Inicio | ~1-2 h |
| 6 | Catálogo desktop: sidebar solo navegación, categorías solo chips (o viceversa) | MEDIO | ~1 h |
| 7 | Borrar `vista-comparativa.tsx` (muerta) o conectarla y oscurecerla | BAJO (limpieza) | ~30 min |
| 8 | Fix wrap "MaxiCarrefou r" + buscador header "B ǁǁ" en mobile | BAJO | ~30 min |

**Nota:** el ítem 1 va primero sí o sí — cualquier decisión estética tomada viendo la fuente
del sistema es una decisión tomada sobre una app que no es la real.

---

## Capturas tomadas en esta sesión
Brújula: inicio-top, inicio-bomba1, inicio-medio, inicio-sectores, catalogo-top (mobile),
catalogo-grid, catalogo-desktop, catalogo-desktop-top, detalle-mobile, detalle-2,
lista-mobile, perfil-mobile, ofertas-mobile.
Trolley: home-mobile, home-precios, grid-mobile, detalle-mobile.
(En el historial de la sesión de Claude Code del 09/06/2026.)
