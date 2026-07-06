#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER CARREFOUR RETAIL (carrefour.com.ar) - VERSION PRO
Fuente tipo "cadena minorista" (no mayorista). NO confundir con MaxiCarrefour
(mayorista B2B, otra plataforma con cookies). Este es el sitio B2C sobre VTEX:
API Intelligent Search publica, sin login, sin cookies (Cloudflare presente
pero no bloquea /api/ — verificado 05/07/2026 hasta con requests plano).
EAN 100% (items[].ean) -> integracion directa por EAN, sin fuzzy.

API: /api/io/_v/api/intelligent-search/product_search/category-1/{slug}
- hideUnavailableItems=true es OBLIGATORIO: el indice arrastra ~69% de
  productos muertos (Price=0 o precio de anos con AvailableQuantity=0 —
  misma trampa que Coto/regla 08). Doble filtro: server + AvailableQuantity>0.
- Caps medidos: count<=100, page<=50 -> techo 5.000 por ruta. Ninguna
  categoria disponible supera ~2.200; si alguna pasa de 4.500 se avisa
  (mitigacion: bajar a category-2/{slug}, probado OK).
- Fallback si IS muere (es app api/io versionable): legacy
  /api/catalog_system/pub/products/search?fq=C:{id} (cap 2.550 por fq).

Precio (verificado contra la web renderizada 05/07/2026, 4/4 exactos):
- Price = precio EFECTIVO unitario (= spotPrice = sellingPrice)
- ListPrice = precio regular (tachado). Oferta directa = Price < ListPrice.
- Promos "2do al 70%"/3x2 NO alteran Price: viven en teasers con
  minimumQuantity>=2. El DOM muestra el promedio c/u con promo — no es
  el precio unitario.
- "Tarjeta Carrefour 15%" aparece en el 100% de los productos y es promo
  de MEDIO DE PAGO (teaser con RestrictionsBins) -> jamas contarla como oferta.
"""

import os
import re
import sys
import json
import time
from datetime import datetime

import requests

API_BASE = "https://www.carrefour.com.ar/api/io/_v/api/intelligent-search/product_search/category-1"
PRODUCTO_BASE = "https://www.carrefour.com.ar"
PRODUCTOS_POR_PAGINA = 100   # cap medido de la API (count>100 -> 400)
PAGINA_MAX = 50              # cap medido (page>50 -> 400)
CAP_ALERTA = 4_500           # colchon antes del techo de 5.000 por ruta
DELAY = 0.5                  # 1 solo 429 aislado en ~80 requests; 0.5s + backoff alcanza
MIN_PRODUCTS_EXPECTED = 8_000  # disponibles medidos 05/07/2026: ~11.500

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Solo super — se excluyen carnes/frutas/panaderia (peso variable, sin
# contraparte mayorista) y Electro/Hogar/Textil/etc. (decision 05/07/2026)
CATEGORIAS = [
    ("Almacen",     "almacen"),
    ("Desayuno",    "desayuno-y-merienda"),
    ("Bebidas",     "bebidas"),
    ("Frescos",     "lacteos-y-productos-frescos"),
    ("Congelados",  "congelados"),
    ("Limpieza",    "limpieza"),
    ("Perfumeria",  "perfumeria-y-farmacia"),
    ("Mascotas",    "mascotas"),
    ("Bebe",        "mundo-bebe"),
]

PRECIO_MIN = 50
PRECIO_MAX = 2_000_000

_RE_2DO_AL = re.compile(r"2d[oa]\s+al\s+(\d+)\s*%", re.I)
_RE_NXM = re.compile(r"\b([2-9])\s*x\s*([1-9])\b", re.I)


def fetch_pagina(session, slug, page):
    """GET con retry/backoff ante 429 (medido: aislado, no sistematico)."""
    url = f"{API_BASE}/{slug}"
    params = {
        "page": str(page),
        "count": str(PRODUCTOS_POR_PAGINA),
        "hideUnavailableItems": "true",
    }
    for espera in (0, 5, 15):
        if espera:
            print(f"    [WARN] 429 en {slug} pag {page}, reintento en {espera}s")
            time.sleep(espera)
        try:
            r = session.get(url, params=params, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code != 429:
            return None
    return None


def texto_oferta(offer, precio, precio_regular):
    """Texto de oferta para el catalogo. Combina descuento directo (ya
    reflejado en Price) y promos por cantidad (NO reflejadas en Price).
    Devuelve (texto, tiene_promo_cantidad)."""
    partes = []
    if 0 < precio < precio_regular:
        pct = round((1 - precio / precio_regular) * 100)
        if pct >= 1:
            partes.append(f"{pct}% OFF")

    promo_cantidad = False
    for t in offer.get("teasers") or []:
        cond = t.get("conditions") or {}
        nombres_cond = {p.get("name") for p in (cond.get("parameters") or [])}
        # RestrictionsBins = promo de medio de pago (Tarjeta Carrefour) — no es
        # oferta de gondola y viene en el 100% de los productos
        if "RestrictionsBins" in nombres_cond:
            continue
        if (cond.get("minimumQuantity") or 0) < 2:
            continue
        nombre_t = t.get("name") or ""
        m = _RE_2DO_AL.search(nombre_t)
        if m:
            partes.append(f"2do al {m.group(1)}%")
            promo_cantidad = True
            continue
        m = _RE_NXM.search(nombre_t)
        if m:
            partes.append(f"{m.group(1)}x{m.group(2)}")
            promo_cantidad = True
            continue
        # Fallback estructurado: PercentualDiscount = descuento promedio por
        # unidad llevando N (2do al 70% -> 35). Cubre nomenclatura nueva.
        efectos = {p.get("name"): p.get("value")
                   for p in ((t.get("effects") or {}).get("parameters") or [])}
        pd = efectos.get("PercentualDiscount")
        if pd:
            partes.append(f"{pd}% llevando {cond.get('minimumQuantity')}")
            promo_cantidad = True

    # dedupe preservando orden (puede haber teasers repetidos)
    return " + ".join(dict.fromkeys(partes)), promo_cantidad


def parsear_producto(prod, categoria_display):
    items = prod.get("items") or []
    if not items:
        return None
    item = items[0]

    ean = str(item.get("ean") or "").strip()
    if not ean or not ean.strip("0").strip():
        return None

    sellers = item.get("sellers") or []
    seller = next((s for s in sellers if s.get("sellerDefault")), sellers[0] if sellers else None)
    if not seller:
        return None
    offer = seller.get("commertialOffer") or {}

    # Doble filtro de stock: hideUnavailableItems (server) + esto. Los muertos
    # arrastran precios de anos de antiguedad (regla 08 / leccion Coto)
    if not offer.get("AvailableQuantity"):
        return None

    try:
        precio = float(offer.get("Price") or 0)
        precio_regular = float(offer.get("ListPrice") or 0)
    except (TypeError, ValueError):
        return None
    if not (PRECIO_MIN <= precio <= PRECIO_MAX):
        return None
    if precio_regular < precio:
        precio_regular = precio

    nombre = (prod.get("productName") or "").strip()
    if not nombre:
        return None

    oferta, promo_cantidad = texto_oferta(offer, precio, precio_regular)

    link_text = prod.get("linkText") or ""
    link = f"{PRODUCTO_BASE}/{link_text}/p" if link_text else PRODUCTO_BASE

    imagenes = item.get("images") or []
    imagen = (imagenes[0] or {}).get("imageUrl", "") if imagenes else ""

    # categories[0] es el path mas profundo: "/Almacen/Pastas secas/..."
    subcategoria = ""
    cats = prod.get("categories") or []
    if cats:
        segs = [s for s in cats[0].split("/") if s]
        if len(segs) >= 2:
            subcategoria = segs[1]

    return {
        "nombre": nombre,
        "precio": precio,                  # efectivo: descuento directo ya aplicado
        "precio_regular": precio_regular,  # ListPrice (= precio si no hay oferta directa)
        "oferta": oferta,                  # "" | "25% OFF" | "2do al 70%" | combinados
        "ean": ean,
        "sku": str(item.get("itemId") or ""),
        "sector": categoria_display,
        "subcategoria": subcategoria,
        "imagen": imagen,
        "link": link,
        "fuente": "Carrefour",
        "stock": True,  # sin stock se filtra arriba (server + AvailableQuantity)
        "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
    }, promo_cantidad


def scrape_categoria(session, nombre_display, slug, acumulado, stats):
    data = fetch_pagina(session, slug, 1)
    if data is None:
        print(f"  [SKIP] {nombre_display}: API sin respuesta")
        return

    total = data.get("recordsFiltered", 0)
    print(f"  {nombre_display}: {total} disponibles reportados")
    if total > CAP_ALERTA:
        print(f"  [WARN] {nombre_display} cerca del cap de 5.000 por ruta — "
              f"considerar bajar a category-2 (ver plan-carrefour.md)")

    paginas = min((total + PRODUCTOS_POR_PAGINA - 1) // PRODUCTOS_POR_PAGINA, PAGINA_MAX)

    for pagina in range(1, paginas + 1):
        if pagina > 1:
            time.sleep(DELAY)
            data = fetch_pagina(session, slug, pagina)
            if data is None:
                print(f"    [WARN] {nombre_display} pag {pagina}: sin respuesta, sigo")
                continue
        productos = data.get("products") or []
        if not productos:
            break

        for prod in productos:
            parseado = parsear_producto(prod, nombre_display)
            if not parseado:
                continue
            registro, promo_cantidad = parseado
            if registro["ean"] in acumulado:
                continue  # solapamiento entre categorias -> dedupe por EAN
            acumulado[registro["ean"]] = registro
            if registro["oferta"]:
                stats["con_oferta"] += 1
            if promo_cantidad:
                stats["promo_cantidad"] += 1

        if pagina % 5 == 0 or pagina == paginas:
            print(f"    Pag {pagina}/{paginas}: {len(acumulado)} unicos acumulados")


def main():
    print("INICIO: Scraper Carrefour retail PRO (VTEX Intelligent Search)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categorias a scrapear: {len(CATEGORIAS)}")
    print("=" * 55)

    session = requests.Session()
    session.headers.update(HEADERS)

    todos = {}
    stats = {"con_oferta": 0, "promo_cantidad": 0}
    resumen = {}

    for i, (nombre_display, slug) in enumerate(CATEGORIAS, start=1):
        print(f"\n[{i}/{len(CATEGORIAS)}] Categoria: {nombre_display}")
        antes = len(todos)
        scrape_categoria(session, nombre_display, slug, todos, stats)
        resumen[nombre_display] = len(todos) - antes
        print(f"  {nombre_display}: {resumen[nombre_display]} productos nuevos")
        time.sleep(DELAY)

    productos_lista = list(todos.values())
    n = len(productos_lista)

    if n < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Solo {n} productos (min esperado: {MIN_PRODUCTS_EXPECTED}) "
              f"— revisar API Intelligent Search / fallback legacy.")
        sys.exit(1)

    # Sanidad de ofertas: si las promos por cantidad casi desaparecen, lo mas
    # probable es que Carrefour cambio la nomenclatura de teasers (silencioso)
    pct_promo = stats["promo_cantidad"] * 100 // max(n, 1)
    if pct_promo < 5:
        print(f"[WARN] Solo {pct_promo}% con promo por cantidad (esperado ~20%) — "
              f"revisar si cambio el formato de teasers")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               f"output_carrefour_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo — {n} productos unicos (solo disponibles)")
    print(f"Con alguna oferta real: {stats['con_oferta']} ({stats['con_oferta'] * 100 // max(n, 1)}%)")
    print(f"  de las cuales promo por cantidad (2do al X% / NxM): {stats['promo_cantidad']}")
    print(f"Guardado en: {output_file}")
    print("\nResumen por categoria (nuevos aportados):")
    for nombre, count in resumen.items():
        print(f"  {nombre}: {count}")

    return productos_lista, resumen


if __name__ == "__main__":
    main()
