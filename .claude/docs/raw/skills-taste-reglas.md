# Reglas de diseño extraídas de las 4 skills de "taste"

> Síntesis orientada a los problemas diagnosticados en Brújula de Precios:
> 37 bordes por pantalla (objetivo ~10), 8 colores de texto (objetivo 3),
> font-weights 700-900 en todo, logos full-color repetidos en grid, placeholders vacíos visibles.
> Contexto: app dark mobile-first (390px), Next.js 16 + Tailwind v4,
> paleta #0a0a0a / #141414 / #d4a574 / #16a34a, Poppins (body) + Barlow Condensed (precios).

Fuente: `.claude/skills/{design-taste-frontend,gpt-taste,high-end-visual-design,redesign-existing-projects}/SKILL.md`

---

## 1. design-taste-frontend (Senior UI/UX Engineer — corrección de sesgos LLM)

1. **Anti-card overuse (Rule 4):** con densidad de datos alta, los contenedores card genéricos están PROHIBIDOS. Agrupar con `border-t`, `divide-y` o espacio negativo puro. Card solo cuando la elevación comunica jerarquía real. → Ataca directo los 37 bordes: una lista de productos se separa con `divide-y divide-white/5`, no con 1 borde completo por item.
2. **Máximo 1 color de acento, saturación < 80%.** Base neutra única (no mezclar grises cálidos y fríos en el mismo proyecto). → Para Brújula: dorado #d4a574 es EL acento; verde #16a34a queda solo como color semántico de éxito/ahorro, no decorativo.
3. **Jerarquía por peso y color, no por tamaño gigante.** "El primer heading no debe gritar". Display: `tracking-tighter leading-none`; body: `text-base leading-relaxed max-w-[65ch]`.
4. **Nunca negro puro #000000** — usar off-black (zinc-950 / #0a0a0a ya cumple). Nunca glows neón ni sombras `box-shadow` por defecto: si hay sombra, teñirla al tono del fondo.
5. **Números en monospace / tabular** en contextos de datos densos (`font-mono` o `tabular-nums`). → Precios de Brújula: Barlow Condensed + `font-variant-numeric: tabular-nums` para que las columnas de precios alineen.
6. **Estados obligatorios:** loading = skeleton con la forma del layout (no spinner circular), empty states compuestos que indiquen cómo poblar datos, errores inline. → Ataca los placeholders vacíos visibles: nunca mostrar un hueco; mostrar skeleton o empty state diseñado.
7. **Feedback táctil:** en `:active` usar `scale-[0.98]` o `-translate-y-[1px]`. Spring physics `stiffness: 100, damping: 20` en interactivos — nunca easing lineal.
8. **Glassmorphism real:** `backdrop-blur` + borde interno 1px `border-white/10` + `shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`. Solo en elementos fixed/sticky (nav, modals).
9. **Performance móvil:** animar SOLO `transform` y `opacity`. Nunca `h-screen` → `min-h-[100dvh]`. Animaciones perpetuas aisladas en Client Components memoizados.
10. **Prohibidos (AI tells):** texto con gradiente en headers grandes, acentos sobresaturados, números falsos redondos (99.99%, 50%), layouts de 3 cards iguales en fila.

## 2. gpt-taste (GSAP Motion Engineer — estructura y respiración)

1. **Regla de hierro de 2 líneas:** ningún título debe pasar de 2-3 líneas. Si pasa, achicar fuente con `clamp(3rem, 5vw, 5.5rem)` y ensanchar contenedor. En 390px: títulos máx ~`text-3xl` para no superar 2 líneas.
2. **Espaciado masivo entre secciones:** `py-32 md:py-48` en desktop — adaptado a mobile app: mínimo `py-10`/`py-12` entre bloques de pantalla; las secciones deben sentirse "capítulos", no apiladas sin aire.
3. **Bento sin huecos:** `grid-auto-flow: dense` (`grid-flow-dense`) en toda grid; verificar matemáticamente que `col-span`/`row-span` encastren sin celdas vacías. → Ataca placeholders vacíos: ninguna grid puede mostrar un hueco muerto.
4. **Restricción de cards:** 3-5 cards intencionales > 8 desordenadas. Menos contenedores, mejor llenados.
5. **Ban de meta-labels baratos:** "SECCIÓN 01", "QUESTION 05" y similares prohibidos para siempre. Labels solo si aportan significado real.
6. **Contraste de botones perfecto:** fondo oscuro = texto blanco, fondo claro = texto oscuro. Texto invisible = falla catastrófica. → Botón dorado #d4a574 lleva texto #0a0a0a, no blanco.
7. **Hover/touch physics en todo clickeable:** `group-hover:scale-105 transition-transform duration-700 ease-out` dentro de `overflow-hidden`.
8. **Imágenes con tratamiento CSS** (`grayscale`, `mix-blend-luminosity`, `opacity-90`, `contrast-125`) para que no parezcan stock pegado. → Es LA solución a logos full-color repetidos: pasarlos a monocromo/luminosity y devolver color solo al activo o en hover.
9. **Anti scroll horizontal:** envolver la página en `overflow-x-hidden w-full max-w-full` si hay animaciones que salen de viewport.
10. **Plan antes de código:** definir layout, tipografía y animaciones en un `<design_plan>` antes de tocar UI — no improvisar componente por componente.

## 3. high-end-visual-design (Awwwards-tier — materialidad y motion)

1. **Bordes prohibidos:** borde genérico `1px solid gray` BANEADO. Sombras duras oscuras (`shadow-md`, `rgba(0,0,0,0.3)`) baneadas. Los bordes que queden: hairlines `border-white/10` o `ring-1 ring-white/5` — nunca grises sólidos visibles.
2. **Arquetipo "Ethereal Glass"** (el que corresponde a Brújula dark): fondo OLED `#050505`-`#0a0a0a`, mesh/radial gradients sutiles de fondo, cards casi negras con hairlines `white/10`, tipografía grotesk ancha.
3. **Double-Bezel (usar con moderación):** card premium = shell exterior (`bg-white/5`, `ring-1 ring-white/10`, `p-1.5`, `rounded-[2rem]`) + núcleo interior con radio concéntrico `rounded-[calc(2rem-0.375rem)]` y highlight `shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)]`. → SOLO para la card héroe de cada pantalla (1 por vista), porque duplica bordes.
4. **Botones pill + button-in-button:** CTA `rounded-full px-6 py-3`; si lleva flecha, va dentro de su propio círculo `w-8 h-8 rounded-full bg-white/10` pegado al padding derecho.
5. **Eyebrow tags:** micro-badge sobre títulos: `rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.2em] font-medium`. (Único uso legítimo de uppercase pequeño.)
6. **Motion con cubic-bezier custom:** `duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]` — nunca `linear` ni `ease-in-out`. Press: `active:scale-[0.98]`.
7. **Entradas de scroll:** elementos entran con `translate-y-16 blur-md opacity-0 → translate-y-0 blur-0 opacity-100` en 800ms+, vía `IntersectionObserver` o `whileInView` — nunca `window.addEventListener('scroll')`.
8. **Stagger en navegación/listas:** items aparecen con delays escalonados 100/150/200ms, no todos a la vez.
9. **Blur solo en fixed/sticky** (nav, overlays). Nunca `backdrop-blur` en contenedores que scrollean — mata los FPS en mobile.
10. **Mobile collapse universal:** debajo de 768px todo layout asimétrico cae a `w-full px-4 py-8` single-column; sin rotaciones ni overlaps (conflicto de touch targets); `min-h-[100dvh]` siempre.

## 4. redesign-existing-projects (auditoría y orden de fixes)

1. **No reescribir: escanear → diagnosticar → fix dirigido** con el stack existente. Cambios chicos y revisables.
2. **Orden de prioridad de fixes (impacto/riesgo):** 1) fuentes, 2) limpieza de paleta, 3) hover/active states, 4) layout y spacing, 5) reemplazar componentes genéricos, 6) loading/empty/error states, 7) pulido tipográfico final.
3. **Pesos intermedios:** si solo se usan 400 y 700 (o 700-900 como Brújula), introducir Medium (500) y SemiBold (600) para jerarquía sutil. El peso máximo se reserva para 1 elemento por pantalla (el precio o el H1).
4. **Card genérica (borde + sombra + fondo) = anti-patrón.** Quitar el borde, O usar solo color de fondo, O usar solo espaciado. Elegir UNO de los tres por componente, nunca los tres juntos.
5. **Una sola familia de grises**, todos teñidos con el mismo matiz. Un solo acento — eliminar el resto. → De 8 colores de texto a 3: primario (blanco ~#f7f7f7), secundario (un gris, ej. white/60), acento (#d4a574). Verde solo semántico.
6. **Números tabulares:** `font-variant-numeric: tabular-nums` en toda interfaz data-heavy.
7. **Tracking negativo en headers grandes, positivo en labels chicos.** `text-wrap: balance` para evitar palabras huérfanas.
8. **Sombras teñidas al fondo**, nunca negro puro a baja opacidad. Dirección de luz consistente en toda la app.
9. **Transiciones 200-300ms en todo interactivo**; `scale(0.98)` en press; focus ring visible (accesibilidad, no opcional); skeleton loaders con la forma del layout; empty states diseñados; nada de links muertos a `#`; indicar página activa en la navegación.
10. **Radio variable:** más cerrado en elementos internos, más suave en contenedores (concéntrico). No un solo border-radius uniforme en todo.
11. **Sin secciones de tono saltado:** no meter un bloque claro random en página dark — usar un tono apenas distinto de la misma paleta (#141414 sobre #0a0a0a).

---

## Reglas consolidadas para Brújula (15 reglas accionables)

Conflictos resueltos:
- **Fuentes:** las 4 skills empujan Geist/Satoshi/Outfit, pero `redesign-existing-projects` manda "trabajar con el stack existente" y Poppins/Barlow Condensed no están baneadas (la banlist es Inter/Roboto/Arial/Open Sans/Helvetica). **Se mantienen Poppins + Barlow Condensed** — cambiar fuentes ahora es riesgo sin retorno; el problema de Brújula es bordes/colores/pesos, no la fuente.
- **Double-Bezel (high-end) vs anti-card (design-taste):** Double-Bezel agrega bordes y el diagnóstico pide bajar de 37 a 10. **Gana anti-card como default; Double-Bezel solo en 1 card héroe por pantalla.** Razón: en 390px dark, las listas necesitan divide-y, no marcos anidados.
- **GSAP scroll pinning/scrubbing (gpt-taste) vs simplicidad mobile:** pinning y scroll-hijack son patrones de landing desktop. **Se descartan para la app; quedan stagger, entrada con fade-up y hover/press physics**, que sí funcionan a 390px sin costo de FPS.
- **Hero centrado (gpt-taste lo prefiere) vs ban de centrado (design-taste):** irrelevante a 390px — todo es single-column; se hereda alineado a la izquierda como default (lectura más rápida en listas de datos).

### Las 15 reglas

1. **Presupuesto de bordes: máx 10 por pantalla.** Listas y grupos se separan con `divide-y divide-white/5` o espacio negativo — nunca 1 card con borde por item. Card completa solo si la elevación significa algo (ej. mejor precio destacado). Verificación: contar nodos con `border`/`ring` en DevTools por vista, debe dar <= 10.
2. **Los bordes que sobrevivan son hairlines:** `border-white/10` o `ring-1 ring-white/5`. Prohibido cualquier gris sólido visible (`border-gray-700` opaco) y `shadow-md` negro.
3. **3 colores de texto, exactos:** primario `#f7f7f7`, secundario `rgba(255,255,255,0.6)` (un solo gris, siempre el mismo), acento `#d4a574`. Verde `#16a34a` SOLO semántico (ahorro, éxito, "guardado") — nunca decorativo. Eliminar los otros 5 colores de texto del código.
4. **Escala de pesos: 400 / 500 / 600, y 700+ para UN solo elemento por pantalla** (el precio protagonista o el H1). Jerarquía por peso+color, no por gritar con 800-900 en todo.
5. **Títulos máx 2 líneas a 390px.** Si envuelve a 3+, bajar el tamaño (`clamp()`) — nunca dejar un muro de texto bold.
6. **Precios con `tabular-nums`:** Barlow Condensed + `font-variant-numeric: tabular-nums` en todo número, para que columnas comparativas alineen dígito a dígito.
7. **Tracking:** negativo en display grande (`tracking-tight`/`tracking-tighter`), positivo solo en eyebrow-labels `text-[10px] uppercase tracking-[0.2em]`. Nada de uppercase en texto normal. `text-wrap: balance` en títulos.
8. **Logos de mayoristas en grid: monocromo por defecto** (`grayscale opacity-70` o `mix-blend-luminosity`), color completo solo en el item activo/seleccionado o el ganador de precio. Un logo full-color repetido N veces = ruido; en mono se vuelve textura.
9. **Cero placeholders vacíos visibles:** todo estado sin datos muestra skeleton (con la forma exacta del layout, shimmer sutil) o un empty state diseñado que diga cómo poblarlo. Grids con `grid-flow-dense` — ninguna celda muerta.
10. **Feedback táctil universal:** todo elemento tocable tiene `active:scale-[0.98]` + `transition duration-200`. Easing custom `ease-[cubic-bezier(0.32,0.72,0,1)]` — prohibido `linear` y `ease-in-out`.
11. **Entradas escalonadas, no instantáneas:** listas/cards entran con fade-up (`translate-y-4 opacity-0 → 0/100`) y stagger de ~60-100ms por item (en mobile, delays más cortos que los 100-200ms de desktop), vía `whileInView` o IntersectionObserver. Nunca listener de scroll manual.
12. **Performance mobile innegociable:** animar solo `transform`/`opacity`; `backdrop-blur` solo en nav sticky y overlays fijos; `min-h-[100dvh]` (nunca `h-screen`); animaciones perpetuas aisladas en Client Components memoizados.
13. **Superficies en 2 niveles, misma familia:** fondo `#0a0a0a`, superficie `#141414`; profundidad extra con un tono intermedio de la misma escala — nunca con sombras negras ni saltos de tono. Sombra (si hace falta) teñida al fondo. Radio concéntrico: contenedor más suave, interno más cerrado.
14. **Double-Bezel solo en la card héroe** de cada vista (ej. la "bomba" destacada o el resultado del calculador): shell `bg-white/5 ring-1 ring-white/10 p-1.5 rounded-2xl` + core con radio `calc()` concéntrico e inset highlight. Máximo 1 por pantalla — entra dentro del presupuesto de 10 bordes.
15. **Proceso de redesign:** no reescribir vistas; aplicar en este orden: (1) limpiar paleta de texto a 3, (2) bajar pesos, (3) podar bordes a hairlines/divide-y, (4) estados active/hover, (5) skeletons y empty states, (6) logos a mono, (7) motion de entrada. Verificar cada vista en 390px después de cada paso antes de seguir.
