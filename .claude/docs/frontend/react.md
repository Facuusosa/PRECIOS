# Rules: React

## Stack
- Next.js 16 App Router, React 19, TypeScript estricto
- Radix UI para componentes accesibles — no reinventar inputs, modals, dropdowns
- Framer Motion para micro-interactions, GSAP para animaciones complejas
- lucide-react para iconos

## Estructura
- 4 vistas en `components/`: `vista-inicio.tsx`, `vista-comparar.tsx`, `vista-lista.tsx`, `vista-cuenta.tsx`
- Estado global en `app/page.tsx`: `vistaActiva`, `listaGuardados`, `sectorInicial`
- Data en `lib/data.ts`: tipos, `queryMap`, `calcularBombas()`, `formatearPrecio()`
- No prop drilling más de 2 niveles — usar estado en `page.tsx` o context si hace falta

## Patrones
- Componentes funcionales siempre — no class components
- Props tipadas con `interface` o `type` — nunca sin tipado
- Handlers nombrados `handleAccion` (ej: `handleGuardar`, `handleComparar`)
- Efectos secundarios en `useEffect` con dependencias explícitas — no dejar array vacío por defecto

## Animaciones — orden de consulta obligatorio
1. **skills.sh** — PRIMERA opción para cualquier animación o microinteracción
2. **21st.dev/community/components** — componentes React listos para usar
3. **ReactBits** (`components/reactbits/`) — ya integrado en el proyecto
4. Construir desde cero solo si no existe en ninguno de los anteriores

## Reglas
- Sin `any` explícito — única excepción: imports de JSON
- No agregar dependencias sin justificación clara (revisar si ya hay algo en el stack)
- No comentarios salvo WHY no obvio
