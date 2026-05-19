> ⚠️ ARCHIVADO — referencia técnica histórica. Ver `.claude/docs/plan.md` para el estado actual.

# Docs: Arquitectura

## Frontend — `/BRUJULA-DE-PRECIOS/`
- Next.js 16 App Router, React 19, TypeScript estricto
- Estado centralizado: `app/page.tsx` → `vistaActiva`, `listaGuardados`, `sectorInicial`
- 9 vistas en `components/`: `vista-inicio.tsx`, `vista-catalogo.tsx`, `vista-detalle.tsx`, `vista-comparativa.tsx`, `vista-comparar.tsx`, `vista-lista.tsx`, `vista-ofertas.tsx`, `vista-cuenta.tsx`, `vista-showcase.tsx`
- Componentes clave: `calculadora.tsx`, `header.tsx`, `bottom-nav.tsx`, `desktop-sidebar.tsx`, `product-card.tsx`, `bomba-card.tsx`
- Data: `lib/data.ts` (tipos, queryMap, calcularBombas, formatearPrecio) + `data/processed/catalogo_unificado.json`
- UI: Radix UI + Tailwind CSS v4 + Framer Motion + lucide-react

## Backend — `/targets/` + wrappers Python
```
scrape_yaguar.py         → targets/yaguar/scraper_pro.py         → actualizar_catalogo.py
scrape_maxicarrefour.py  → targets/maxicarrefour/scraper_pro.py  → actualizar_catalogo.py
scrape_maxiconsumo.py    → targets/maxiconsumo/scraper_pro.py    → enriquecer_eans.py → actualizar_catalogo.py
```
- `config.py`: URLs, categorías, delays — credenciales desde `.env` vía python-dotenv
- `actualizar_catalogo.py`: unifica 3 fuentes → `data/processed/catalogo_unificado.json`
- `start_web.py`: lanza Next.js en localhost:3000

## Data
- `data/raw/`: Excel internos (EAN, nombres) — no sensible
- `data/processed/catalogo_unificado.json`: catálogo unificado (17k+ productos)
- `data/config/pesos_comerciales.json`: conversión de unidades

## Flujo completo
```
Scraper Python → output_mayorista_TIMESTAMP.json → actualizar_catalogo.py → catalogo_unificado.json → lib/data.ts → Frontend
```

## Stack técnico
| Capa | Tech | Por qué |
|------|------|---------|
| Frontend | Next.js 16, React 19, TS | SSR, deploy fácil, typesafe |
| Estilos | Tailwind v4, Radix UI | Utility-first, accesibilidad built-in |
| HTTP mayoristas | curl_cffi | Bypassea bot detection de Cloudflare |
| Scraping | BeautifulSoup4 | HTML parsing sencillo |
| Data processing | pandas, openpyxl | Excel + transformaciones |
| Config | python-dotenv | Credenciales en .env, nunca hardcoded |
