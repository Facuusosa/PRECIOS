# SPEC COMPLETA — REDISEÑO BRÚJULA DE PRECIOS
> Archivo único de verdad. Ejecutar de arriba a abajo con loop de screenshots.
> Referencia visual: `.claude/docs/imagenparaclaude.jpg`
> App actual (anti-referencia): https://v0-brujula-de-precios.vercel.app
> Competidor (diferenciarse de): https://ahorroposadas.com

---

## ARQUITECTURA — 6 pantallas, 4 tabs en nav

```
BOTTOM NAV: [Inicio] [Catálogo] [Herramientas] [Perfil]

  Inicio (Home)
    ├─ Hero bomba del día (card grande dark green)
    ├─ Scroll horizontal bombas #2-#10
    └─ Circular Gallery sectores → tap → Catálogo filtrado

  Catálogo
    ├─ Search + pills por sector
    ├─ Grid 2 columnas (fotos reales de public/categories/)
    └─ tap → Detalle (pantalla full-screen, NO modal)
                └─ "Ver comparativa" → Comparativa (full-screen)
                                          └─ "Guardar" → Herramientas

  Herramientas
    ├─ Lista de productos guardados
    ├─ Resumen por mayorista + Mix Inteligente
    └─ Slide button "Armar mi lista"

  Perfil
    └─ Avatar, plan, settings
```

**Navegación drill-down (sin tab del nav):**
- Detalle y Comparativa son pantallas completas con back button (ChevronLeft)
- En React: `vistaAnterior` en estado para el back button
- Transición: slide from right (CSS transform translateX)

---

## REGLAS ABSOLUTAS DE DISEÑO

### ❌ PROHIBIDO — nunca hacer esto
- Emojis como íconos funcionales o decoración de UI
- Tablas de precios inline dentro de cards del catálogo (como la app actual — HORRIBLE)
- REF numbers visibles al usuario (7790360720382 → JAMÁS)
- Badges "OFERTA BOMBA", "3 FUENTES" — sin personalidad
- Glassmorphism / backdrop-filter / blur en cards o nav
- Colores fuera del sistema definido
- Gradientes genéricos tipo IA
- "CALCULAR" como texto de botón (parece terminal POS)

### ✅ SISTEMA DE ÍCONOS — solo esto
- **Nav:** Lucide (Home, LayoutGrid, Briefcase, User)
- **Acciones:** Lucide (Heart, ShoppingCart, ChevronLeft, ChevronRight, X, Plus, Minus, MoreHorizontal, Bell, LogOut, Calculator, CreditCard, Store)
- **Categorías en galería:** fotos reales `public/categories/` — NUNCA emoji
- **Métricas y stats:** solo tipografía bold/900 — sin emoji decorativo

### Filosofía antes de implementar cualquier elemento
Preguntarse: "¿hay una manera más disruptiva de hacer esto?"
Si la primera respuesta es un emoji o una tabla → buscar alternativa visual.
Para referencias de inspiración → godly.website, 21st.dev/community/components

---

## SISTEMA DE DISEÑO

### Paleta de colores
```css
--verde-oscuro:   #0a3d1f   /* headers, botones primarios, bg detalle */
--verde-hover:    #0d4820   /* hover states */
--blanco:         #ffffff   /* cards, fondos de contenido */
--crema:          #f8faf6   /* fondo catálogo y home */
--dorado:         #d4a574   /* Mix Inteligente, Mejor Precio badge, Plan Pro */
--gris-texto:     #4a5568   /* texto secundario */
--gris-borde:     #e2e8f0   /* separadores, bordes de cards */
--gris-imagen:    #f0ede6   /* fondo placeholder imagen de producto */
--rojo-peligro:   #ef4444   /* SOLO botón cerrar sesión */
```

### Tipografía
```
Font: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
900 → precios principales, hero titles (32px+)
700 → nombres producto, botones, headers de sección
600 → labels uppercase, badges, subtítulos
400 → texto secundario, descripción, metadatos
Regla: jerarquía OBVIA a primera vista — si no se lee de lejos, aumentar contraste de peso
```

### Espaciado y forma
```
Container:          max-width 600px, padding horizontal 20px
Gap entre cards:    16px
Card padding:       16px interno
Border-radius cards: 16px
Border-radius pills: 20px (full rounded)
Border-radius botones: 12px
Border-radius hero card: 20px
Bottom nav height:  64px + env(safe-area-inset-bottom)
Content padding-bottom: 88px (clearance del nav)
```

### Tokens CSS (agregar en globals.css)
```css
:root {
  --c-dark:    #0a3d1f;
  --c-hover:   #0d4820;
  --c-gold:    #d4a574;
  --c-cream:   #f8faf6;
  --c-img-bg:  #f0ede6;
  --c-border:  #e2e8f0;
  --c-text2:   #4a5568;
}
```

---

## PANTALLA 1 — Inicio (Home)

**Datos reales:** `calcularBombas()` de `lib/data.ts` → top 10 ordenado por `ahorroVsMaximo` desc

```
┌─────────────────────────────────────┐
│  BRÚJULA          hora    Lucide Bell│  ← bg blanco, saludo dinámico
│  Buenos días, Juan                  │     según hora del día
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │  HERO BOMBA (bomba[0])
│  │ MEJOR DIFERENCIA HOY  [gold]│    │  bg: linear-gradient(135deg, #0a3d1f, #0d4820)
│  │                    [img]    │    │  border-radius: 20px, padding: 24px
│  │  Fideos Matarazzo   ●-48%  │    │  imagen: 100x100 float right
│  │  Mostacholes N°52           │    │  badge: círculo 40px dorado
│  │  $799,90  en Maxiconsumo   │    │  precio: 28px bold/900 blanco
│  │                    [♡]      │    │  ♡: Lucide Heart, blanco/40
│  └─────────────────────────────┘    │
│                                     │
│  TOP AHORRO ──────────────────────  │  label 11px uppercase #4a5568
│                                     │
│  ┌──────┐ ┌──────┐ ┌──────┐ →      │  SCROLL HORIZONTAL (bombas 1-9)
│  │[img] │ │[img] │ │[img] │        │  mini-cards: 130x170px, border-radius 16px
│  │ ●48% │ │ ●42% │ │ ●35% │        │  bg: white, shadow
│  │$799  │ │$1649 │ │$599  │        │  imagen: 80x80 objeto real
│  │ ♡    │ │ ♡    │ │ ♡    │        │  badge: círculo pequeño verde oscuro
│  └──────┘ └──────┘ └──────┘        │  sin scrollbar visible (scrollbar-hide)
│                                     │
│  EXPLORÁ POR SECTOR ─────────────  │  label 11px uppercase letter-spacing 2px
│                                     │
│         [CIRCULAR GALLERY]          │  altura: 280px, centrado
│    Almacén    Bebidas               │  8 sectores con fotos reales
│  Limpieza       Frescos             │
│    Mascotas   Cuidado               │
│        Kiosco   Bazar               │
└─────────────────────────────────────┘
```

**Interacciones Inicio:**
- Tap en card bomba (hero o scroll) → `setProductoSeleccionado(bomba)` + `setVistaActiva('detalle')`
- ♡ Heart → toggle `favoritos` (useState Set<string> por producto.id)
- Tap sector en galería → `setSectorActivo(sector)` + `setVistaActiva('catalogo')`

---

## PANTALLA 2 — Catálogo

**Datos:** `productos` de `lib/data.ts` filtrado por `sectorActivo` + `textoBusqueda`
**Lógica de filtrado:** reusar de `vista-comparar.tsx` existente (normalización NFD, ordenamiento ABC)

```
┌─────────────────────────────────────┐
│  Catálogo                  [Search] │  ← bg blanco, Lucide Search al tap expande
├─────────────────────────────────────┤
│  🔍 Buscar producto...              │  ← search bar bg #f8faf6, siempre visible
├─────────────────────────────────────┤
│ [Todos][Almacén][Bebidas][Limpieza]→│  ← pills scroll horizontal
│                                     │     activa: bg #0a3d1f white
│                                     │     inactiva: bg white border #e2e8f0
├──────────────────┬──────────────────┤
│    [foto real]   │   [foto real]    │  GRID 2 COL
│      ●-42%       │     ●-28%        │  card: bg white, radius 16px
│  Fideos Matarazzo│  Aceite Cañuelas │  shadow: 0 2px 8px rgba(0,0,0,0.1)
│      $799        │     $1.649       │  hover: translateY(-4px) shadow++
│  ♡   [Agregar]   │  ♡   [Agregar]   │
├──────────────────┼──────────────────┤
│    [foto real]   │   [foto real]    │  IMAGE AREA: 140px height, bg #f0ede6
│      ●-59%       │     ●-47%        │  badge: circle 36px absolute top-right
│  Colgate X90g    │  Paté Swift      │         bg #0a3d1f, white, 11px bold
│     $1.499       │     $599         │  ACTIONS: Heart + "Agregar" button
│  ♡   [Agregar]   │  ♡   [Agregar]   │
└──────────────────┴──────────────────┘
```

**Interacciones Catálogo:**
- Tap card (excepto botones) → detalle
- Tap "Agregar" → detalle
- ♡ Heart → toggle favorito
- Pills → `setSectorActivo(pill)` → re-filtra grid
- Search → filtra en tiempo real (debounce 200ms)

**ProductCard props:**
```typescript
interface ProductCardProps {
  producto: Producto
  onTap: () => void
  onAgregar: () => void
  esFavorito: boolean
  onToggleFavorito: () => void
}
```

---

## PANTALLA 3 — Detalle del Producto

**Referencia visual:** imagenparaclaude.jpg — pantalla DERECHA
**Sin tab del nav** — pantalla completa, back button regresa a origen

```
┌─────────────────────────────────────┐
│ [←ChevronLeft]           [Cart]     │  bg: linear-gradient(135deg,#0a3d1f,#0d4820)
│                                     │  flecha y carrito: blanco, Lucide icons
│    ✦ Mejor Precio                   │  badge: pill bg #d4a574, texto #0a3d1f
│                                     │         11px bold, uppercase, padding 6px 12px
│           [imagen 200x200]          │  foto real centrada
│               ●-48%                 │  drop-shadow(0 20px 40px rgba(0,0,0,0.3))
│                                     │  badge descuento: 44px circle, bg #d4a574
├─────────────────────────────────────┤
│  FIDEOS MATARAZZO                   │  bg: blanco
│  MOSTACHOLES N°52 X500G             │  border-radius: 24px 24px 0 0
│                                     │  padding: 24px 20px
│  [en Maxiconsumo]                   │  "en Mayorista": pill bg #f0ede6, #4a5568
│                                     │
│  $799,90                            │  precio: 32px bold/900 #0a3d1f
│                                     │
│  Disponible en 3 mayoristas         │  12px #4a5568
│                                     │
│  ⬤  Agregar a mi lista             │  fila: círculo 48px negro + texto 16px bold
│                                     │
│  [    Ver comparativa  →    ]       │  full-width, border 2px #0a3d1f, color #0a3d1f
│                                     │  bg blanco, padding 16px, radius 12px
└─────────────────────────────────────┘
```

**Interacciones Detalle:**
- ← back → `setVistaActiva(vistaAnterior)` (puede ser 'inicio' o 'catalogo')
- "Agregar a mi lista" → mini sheet con slider de margen → `onGuardarEnLista()`
- "Ver comparativa" → `setVistaActiva('comparativa')`

---

## PANTALLA 4 — Comparativa

**Diferenciador único — ningún competidor argentino lo tiene**
**Sin tab del nav** — pantalla completa, back button regresa a Detalle

```
┌─────────────────────────────────────┐
│ [←]   Comparativa de precios        │  bg: blanco
│                                     │
│  [img 60x60]  Fideos Matarazzo      │  producto ref: imagen pequeña + nombre
│               N°52 X500g            │
├─────────────────────────────────────┤
│  PRECIOS POR MAYORISTA              │  label 11px uppercase #4a5568
│                                     │
│  Maxiconsumo           ★ Mejor      │  badge "Mejor precio": pill dorado
│  ████████████████████   $799        │  barra: height 10px, bg #0a3d1f
│                                     │  animación: width 0→X% en 0.6s ease-out
│  Yaguar                             │
│  ████████████          $1.149       │  barra: bg #2d6a4f
│                                     │
│  MaxiCarrefour                      │
│  ████████              $1.540       │  barra: bg #d4a574
│                                     │  track (vacío): bg #f0ede6, radius 5px
├─────────────────────────────────────┤
│  [Calculator icon]  Calculadora     │  Lucide Calculator + label bold
│                                     │
│  Comprando en Maxiconsumo: $799,90  │  readonly, se actualiza si cambia mayorista
│                                     │
│  Margen:          35%               │  label + valor actualizado en tiempo real
│  ━━━━━━━━━━━━━━●━━━━              │  slider range custom:
│                                     │    track: #e2e8f0
│  → Precio de venta:   $1.079       │    thumb: 20px circle #0a3d1f
│  → Ganancia/unidad:   $  279       │    fill: #0a3d1f (CSS var trick)
│  → Si comprás [12] u: $3.348       │  [12] es input editable
│                                     │
│  [ Guardar en mi lista ]            │  bg #0a3d1f, white, full-width, 18px padding
└─────────────────────────────────────┘
```

**Lógica barras:**
```typescript
const maxPrecio = Math.max(...precios.map(p => p.precio))
const widthPct = (precio / maxPrecio) * 100  // track = 100%, barra = este %
```

**Calculadora en tiempo real:**
```typescript
const precioVenta = precioCompra / (1 - margen/100)
const ganancia = precioVenta - precioCompra
const gananciaTotal = ganancia * cantidad
```

**Interacciones Comparativa:**
- Barras se animan al montar el componente (CSS animation delay)
- Slider margen → recalcula precio venta + ganancia en tiempo real
- Input cantidad → recalcula ganancia total
- "Guardar en mi lista" → `onGuardarEnLista({ producto, mayorista: mejorMayorista, precioCompra, margen, precioVenta, ganancia })` → navega a 'herramientas'

---

## PANTALLA 5 — Herramientas

```
┌─────────────────────────────────────┐
│  Herramientas                       │  bg: linear-gradient(135deg,#0a3d1f,#0d4820)
│  Tu lista de compras                │  color: blanco
├─────────────────────────────────────┤
│                                     │  ESTADO VACÍO (items.length === 0):
│    [ShoppingCart 48px #e2e8f0]      │    ícono Lucide grande gris claro
│   Todavía no guardaste nada         │    texto 16px bold #0a3d1f
│   Compará y guardá lo que necesitás │    texto 14px #4a5568
│   [ Ir al catálogo ]                │    botón bg #0a3d1f white
├─────────────────────────────────────┤
│  MIS PRODUCTOS (3)                  │  CON ITEMS:
│                                     │  label 11px uppercase #4a5568
│  ┌────────────────────────────────┐ │
│  │[img] Fideos Matarazzo     [⋯] │ │  card: white, radius 16px, padding 20px
│  │      $799  Maxiconsumo        │ │  img: 80x80, radius 12px, bg #f0ede6
│  └────────────────────────────────┘ │  ⋯: Lucide MoreHorizontal → eliminar
│  (más cards...)                     │
├─────────────────────────────────────┤
│  RESUMEN DE COMPRA                  │  label 11px uppercase #4a5568
│                                     │
│  Todo en Maxiconsumo   $3.947       │  card: white, border-left 4px #e2e8f0
│  Todo en Yaguar        $4.690       │  label 12px bold uppercase + total 28px/900
│                                     │
│  ┌──────────────────────────────┐   │  MIX INTELIGENTE card destacada:
│  │ ★ MIX INTELIGENTE           │   │  bg: linear-gradient(rgba(212,165,116,0.1),white)
│  │   $3.320  Ahorrás $627 (14%)│   │  border-left: 4px solid #d4a574
│  └──────────────────────────────┘   │  total: 28px/900, "Ahorrás": 12px #d4a574
│                                     │
│  Con margen 35%: $1.383 de ganancia │  14px #4a5568
│                                     │
│  ┌────────────────────────────────┐ │  SLIDE BUTTON
│  │  [🛒]  Deslizá para armar  ← │ │  Ref: 21st.dev/community/components/reuno-ui/slide-button
│  └────────────────────────────────┘ │  Thumb: SVG carrito custom, bg white, circle 50px
│                                     │  Track: bg #0a3d1f, height 60px, radius 30px
│                                     │  Estado 1 idle: "Deslizá para armar tu lista"
│                                     │  Estado 2 animando: "Armando lista..." + spinner
│                                     │  Estado 3 done: "¡Lista armada!" + Lucide Check #d4a574
│                                     │  Solo activo si items.length > 0
└─────────────────────────────────────┘
```

**Lógica Mix Inteligente:**
```typescript
// Para cada item en la lista, tomar el precio mínimo disponible entre mayoristas
const totalMix = items.reduce((sum, item) => {
  const minPrecio = Math.min(...item.producto.precios.map(p => p.precio).filter(p => p > 0))
  return sum + minPrecio
}, 0)
const totalMaxiconsumo = items.reduce((sum, item) => {
  const p = item.producto.precios.find(p => p.mayorista === 'Maxiconsumo')
  return sum + (p?.precio || 0)
}, 0)
// similar para Yaguar, MaxiCarrefour
```

---

## PANTALLA 6 — Perfil

```
┌─────────────────────────────────────┐
│  bg: #f8faf6 (toda la vista)        │
│                                     │
│              [JP]                   │  círculo 80px, bg #0a3d1f
│         Juan Pérez                  │  iniciales 32px bold blanco
│     juan@comercio.com               │  nombre 20px bold #0a3d1f
│                                     │  email 14px #4a5568
│  ┌──────────────────────────────┐   │
│  │ TU PLAN                 Pro │   │  card: bg linear-gradient(135deg,#0a3d1f,#0d4820)
│  │ ● Activo                    │   │  radius 20px, padding 20px
│  │ [Gestionar plan]            │   │  badge "Pro": pill bg #d4a574, #0a3d1f, bold
│  └──────────────────────────────┘   │  badge "Activo": pequeño #d4a574
│                                     │  botón: border white/30, color white
│  ┌──────────────────────────────┐   │
│  │ Bell Alertas de precio   >  │   │  cards menú: white, radius 16px, padding 20px
│  │ Store Mis mayoristas     >  │   │  ícono Lucide 20px #0a3d1f + texto 14px bold
│  │ CreditCard Suscripción   >  │   │  + subtexto 12px #4a5568 + ChevronRight
│  └──────────────────────────────┘   │
│                                     │
│  [ LogOut  Cerrar sesión ]          │  full-width, border 2px #ef4444
│                                     │  color #ef4444, bg transparent, radius 12px
└─────────────────────────────────────┘
```

---

## COMPONENTE: Circular Gallery

**Archivo:** `components/circular-gallery.tsx`
**Stack:** React puro + CSS — sin librerías externas

```typescript
interface CircularGalleryProps {
  sectores: { nombre: string; imagen: string }[]
  onSelectSector: (nombre: string) => void
  sectorActivo?: string
}

// Sectores disponibles con imágenes reales:
const SECTORES = [
  { nombre: 'Almacén',         imagen: '/categories/almacen_real.png' },
  { nombre: 'Bebidas',         imagen: '/categories/bebidas_real.png' },
  { nombre: 'Limpieza',        imagen: '/categories/limpieza_real.png' },
  { nombre: 'Frescos',         imagen: '/categories/frescos_real.png' },
  { nombre: 'Cuidado Personal',imagen: '/categories/perfumeria_real.png' },
  { nombre: 'Mascotas',        imagen: '/categories/mascotas.png' },
  { nombre: 'Kiosco',          imagen: '/categories/almacen.png' },
  { nombre: 'Bazar',           imagen: '/categories/hogar.png' },
]
```

**Posicionamiento matemático:**
```typescript
// Para N items, ángulo entre items = 360/N grados
// Cada item: rotate(angle + rotacion) translateX(radio) rotate(-(angle + rotacion))
const angulo = (360 / sectores.length) * index
const radio = 110  // px desde el centro
const transform = `rotate(${angulo + rotacion}deg) translateX(${radio}px) rotate(${-(angulo + rotacion)}deg)`
```

**Estado:**
```typescript
const [rotacion, setRotacion] = useState(0)
// Click: setRotacion(prev => prev + (360 / sectores.length))
```

**CSS crítico:**
```css
.gallery-container {
  position: relative;
  width: 280px;
  height: 280px;
  margin: 0 auto;
}
.gallery-item {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 80px;
  height: 80px;
  margin: -40px 0 0 -40px;  /* centering offset */
  border-radius: 50%;
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.4s ease, box-shadow 0.3s ease;
}
.gallery-item:hover {
  box-shadow: 0 4px 16px rgba(212,165,116,0.4);
  scale: 1.05;
}
.gallery-item.activo {
  border: 2px solid #d4a574;
}
.gallery-item img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 50%;
}
.gallery-item span {
  font-size: 10px;
  font-weight: 700;
  color: #0a3d1f;
  text-align: center;
  margin-top: 4px;
  line-height: 1.2;
}
```

---

## COMPONENTE: Slide Button

**Referencia exacta:** https://21st.dev/community/components/reuno-ui/slide-button/default
**Archivo:** `components/slide-button.tsx`
**Instrucción:** Visitar la URL, copiar el código del componente, adaptar con estos cambios:

```
Customización:
  - Ícono: SVG carrito custom (no arrow, no Lucide genérico)
    SVG carrito: M6 2L3 6v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6l-3-4H6zm0 0h12M3 6h18M16 10a4 4 0 01-8 0
  - Track: bg #0a3d1f, height 60px, border-radius 30px, padding 5px
  - Thumb: bg white, 50px circle, carrito SVG #0a3d1f centrado
  - Texto track: "Deslizá para armar tu lista", color rgba(255,255,255,0.6), no seleccionable
  - Estado loading (onSlideComplete dispara): spinner en thumb, texto "Armando lista..."
  - Estado success: Lucide Check en thumb, texto "¡Lista armada!", color #d4a574
  - Disabled si items.length === 0: opacity 0.4, cursor not-allowed
  - onComplete: procesa el Mix Inteligente (calcular totalMix) + feedback visual
```

---

## ESTADO GLOBAL (app/page.tsx)

```typescript
// Tipos de vista — ACTUALIZAR desde el actual
type Vista = 'inicio' | 'catalogo' | 'detalle' | 'comparativa' | 'herramientas' | 'perfil'

// Estado a agregar al actual:
const [vistaAnterior, setVistaAnterior] = useState<Vista>('inicio')
const [productoSeleccionado, setProductoSeleccionado] = useState<Producto | null>(null)
const [sectorActivo, setSectorActivo] = useState<string>('Almacén')
const [favoritos, setFavoritos] = useState<Set<string>>(new Set())

// Navegación a detalle (desde inicio o catálogo):
const handleVerProducto = (producto: Producto, desde: Vista) => {
  setVistaAnterior(desde)
  setProductoSeleccionado(producto)
  setVistaActiva('detalle')
}

// Navegación back desde detalle/comparativa:
const handleBack = () => setVistaActiva(vistaAnterior)

// Toggle favorito:
const handleToggleFavorito = (productoId: string) => {
  setFavoritos(prev => {
    const next = new Set(prev)
    next.has(productoId) ? next.delete(productoId) : next.add(productoId)
    return next
  })
}
```

---

## BOTTOM NAV

**Archivo:** `components/bottom-nav.tsx` — reescribir completamente

```typescript
// Diseño: flat, full-width, sin glassmorphism, sin bordes redondeados
// Items:
const items = [
  { id: 'inicio',       label: 'Inicio',       Icon: Home },
  { id: 'catalogo',     label: 'Catálogo',      Icon: LayoutGrid },
  { id: 'herramientas', label: 'Herramientas',  Icon: Briefcase },
  { id: 'perfil',       label: 'Perfil',        Icon: User },
]

// CSS:
position: fixed; bottom: 0; left: 0; right: 0; z-index: 100;
background: white; border-top: 1px solid #e2e8f0;
display: flex; padding: 12px 0 env(safe-area-inset-bottom);

// Cada item:
flex: 1; flex-direction: column; align-items: center; gap: 4px;
font-size: 10px; font-weight: 700; cursor: pointer;
color activo: #0a3d1f + border-bottom 2px solid #0a3d1f (solo en el ícono)
color inactivo: #4a5568
transition: color 0.2s ease
```

---

## ARCHIVOS A CREAR Y MODIFICAR

### Nuevos (crear desde cero)
```
components/circular-gallery.tsx     — galería sectores
components/vista-catalogo.tsx       — reemplaza/nueva basada en vista-comparar
components/vista-detalle.tsx        — pantalla detalle producto
components/vista-comparativa.tsx    — pantalla comparativa + calculadora
components/slide-button.tsx         — desde 21st.dev customizado
```

### Modificar (mantener lógica, cambiar visual)
```
app/globals.css                     — tokens de color, eliminar glassmorphism
app/page.tsx                        — tipos Vista + nuevos estados + handlers
components/bottom-nav.tsx           — flat design, nuevos labels e íconos
components/header.tsx               — simplificar, eliminar scroll velocity animation
components/vista-inicio.tsx         — home con bombas hero + scroll + circular gallery
components/vista-lista.tsx          — renombrar a "herramientas", mix inteligente, slide button
components/vista-cuenta.tsx         — "perfil" con nueva paleta
```

### No tocar
```
lib/data.ts                         — lógica de datos intacta (calcularBombas, etc.)
hooks/                              — use-modal-producto, use-mobile, use-toast
public/categories/                  — imágenes reales ya disponibles
```

---

## LOOP DE EJECUCIÓN (seguir este orden exacto)

```
SETUP:
  1. cd BRUJULA-DE-PRECIOS && npm run dev   → localhost:3000
  2. Tener imagenparaclaude.jpg abierta para comparar

POR CADA PANTALLA:
  a. Implementar el componente
  b. Screenshot Puppeteer: 390x844 (mobile) Y 1280x800 (desktop)
  c. Pantallas 2 y 3: comparar pixel a pixel con imagenparaclaude.jpg
  d. Pantallas 1,4,5,6: comparar con specs de este doc
  e. Ajustar → screenshot → repetir hasta convergencia visual
  f. npx tsc --noEmit → 0 errores antes de continuar a la siguiente pantalla

ORDEN DE IMPLEMENTACIÓN:
  1. globals.css (tokens)
  2. bottom-nav.tsx (flat)
  3. header.tsx (simplificar)
  4. circular-gallery.tsx (componente nuevo)
  5. slide-button.tsx (desde 21st.dev)
  6. vista-inicio.tsx (home)
  7. vista-catalogo.tsx (nuevo)
  8. vista-detalle.tsx (nuevo)
  9. vista-comparativa.tsx (nuevo)
  10. vista-lista.tsx → herramientas
  11. vista-cuenta.tsx → perfil
  12. page.tsx (wiring final)
```

---

## VERIFICACIÓN FINAL

```
□ npx tsc --noEmit → 0 errores
□ npm run lint → 0 warnings críticos
□ 6 pantallas cargan sin error en localhost:3000
□ Circular Gallery rota y filtra catálogo correctamente
□ Drill-down completo: Inicio → Catálogo → Detalle → Comparativa → Herramientas
□ Back button funciona desde Detalle y Comparativa
□ Calculadora de margen recalcula en tiempo real
□ Mix Inteligente calcula el mínimo real por producto
□ Slide button: idle → animando → completado
□ 0 emojis como íconos funcionales (solo Lucide + fotos reales)
□ 0 REF numbers visibles en ninguna pantalla
□ 0 botones sin onClick definido
□ Mobile 390px: scroll suave, sin overflow horizontal
□ Desktop 1280px: centrado, max-width 600px respetado
□ Favoritos (♡) persisten mientras la sesión está activa
```

---

## REFERENCIAS EXTERNAS (consultar en este orden para UI)

1. `imagenparaclaude.jpg` — referencia principal visual
2. https://21st.dev/community/components — componentes React (especialmente slide-button)
3. https://reactbits.dev/get-started — animaciones (ya en components/reactbits/)
4. https://godly.website — inspiración layouts premium
5. https://skills.sh — skills Claude Code pre-construidas
6. https://github.com/agentsmd/agents.md — agentes pre-construidos
