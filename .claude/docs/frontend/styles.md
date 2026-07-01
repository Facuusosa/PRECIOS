# Rules: Styles

## Tailwind CSS v4
- Import correcto: `@import 'tailwindcss'` — NUNCA `@tailwind base/components/utilities` (directivas viejas)
- Clases custom: usar `@utility` — nunca `@apply` en v4
- No estilos inline (`style={{}}`) salvo valores dinámicos que no se pueden expresar en clases

## Diseño
- Mobile-first siempre — breakpoints: `sm:`, `md:`, `lg:`
- Paleta de colores definida en design tokens — no usar hex directamente en componentes
- Espaciado: usar escala de Tailwind (`p-4`, `gap-6`) — no píxeles arbitrarios salvo excepción justificada
- Tipografía: definida en el design system — no cambiar font-size arbitrariamente

## Componentes visuales — inspiración
- **godly.website** — referencia para layouts y efectos premium antes de diseñar desde cero
- **skills.sh** — animaciones y transiciones (prioridad máxima)

## Dark mode
- MVP: modo oscuro por defecto (comerciantes usan en ambientes variados)
- Clases `dark:` para overrides si se agrega toggle después

## Design tokens de Brújula (colores reales del proyecto)

```
#0a0a0a  — negro principal (fondos oscuros, botones primarios, texto principal)
#f7f7f7  — gris muy claro (fondos de página, secciones neutras)
#d4a574  — gold/acento (badge FREE, CTA de upgrade, elementos de conversión)
#16a34a  — verde (checkmarks, confirmación, "Guardado", éxito)
#6b7280  — gris medio (texto secundario, iconos Lock, subtítulos)
#e5e7eb  — gris borde (separadores, borders de cards en modo claro)
```

Usar estos valores siempre que sea posible. No inventar variantes nuevas sin justificación.

## Accesibilidad
- Usar Radix UI para cualquier componente interactivo — ya tiene aria labels y keyboard nav
- Contraste: mínimo WCAG AA para texto sobre fondo
- No remover `outline` en focus sin reemplazarlo por otro indicador visible
