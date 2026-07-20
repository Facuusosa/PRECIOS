#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER JUMBO (jumbo.com.ar) - VERSION PRO
Fuente tipo "cadena minorista" (no mayorista) — mismo trato que Coto,
Carrefour retail, Dia y Masonline. Sitio Cencosud sobre VTEX (via CloudFront,
SIN Cloudflare), sin auth, sin cookies (verificado 20/07/2026).

API: Intelligent Search (a diferencia de Dia/Masonline, el legacy Catalog
System NO sirve aca — verificado 20/07/2026: fq=C:{id} con IDs de nivel 1
funciona, pero con IDs de subcategoria (nivel 2/3) devuelve SIEMPRE 0 —
Jumbo solo indexa productos en la categoria raiz para el legacy. El
Intelligent Search con el slug simple en el path (bug ya documentado para
Dia) tampoco filtra ("recordsFiltered" identico para cualquier categoria =
fallback al catalogo completo) — la ruta que SI filtra correctamente es con
el prefijo "category-1/{slug}" (mismo patron que Carrefour retail):
  /api/io/_v/api/intelligent-search/product_search/category-1/{slug}
- hideUnavailableItems=true obligatorio (misma trampa Coto/Carrefour/regla 08).
- Caps medidos (identicos a Carrefour): count<=100, page<=50 -> techo 5.000
  por ruta. Con hideUnavailableItems=true NINGUNA de las 15 categorias
  "super" supera 3.900 (max: Almacen) — no hizo falta bajar a category-2.
- Categorias EXCLUIDAS (mismo criterio que las demas cadenas): Electro(15),
  Hogar y textil(16), Tiempo Libre(465, deportes/jugueteria), Sin
  Categoria(9999), Felices Fiestas(10038, estacional), Huevos de pascua(510,
  estacional), Panaderia duplicada(271), bug de categoria invalida
  (id=2147483647), Luces c/toma(541, decoracion).

EAN 100% (items[].ean) -> integracion directa por EAN, sin fuzzy.

Precio: Price = efectivo. ListPrice VIENE ROTO EN EL 100% DEL CATALOGO
(medido 20/07/2026 sobre 10.350 productos: TODOS los que tenian
ListPrice>Price daban un ratio mediano de 82x, hasta 8.264x — un ListPrice
nunca actualizado, no un precio de lista real). A diferencia de Carrefour/
Coto/Dia (donde ListPrice SI es confiable), en Jumbo se ignora del todo:
precio_regular = precio siempre, oferta = "" siempre. Si en el futuro Jumbo
corrige su feed, esto se puede revertir comparando contra un ratio razonable
(<3x) antes de confiar en ListPrice de nuevo.
"""

import os
import re
import sys
import json
import time
from datetime import datetime

import requests

API_BASE = "https://www.jumbo.com.ar/api/io/_v/api/intelligent-search/product_search/category-1"
PRODUCTO_BASE = "https://www.jumbo.com.ar"
PRODUCTOS_POR_PAGINA = 100
PAGINA_MAX = 50
CAP_ALERTA = 4_500
DELAY = 0.5
MIN_PRODUCTS_EXPECTED = 6_000  # disponibles medidos 20/07/2026: bruto ~10.460 antes de dedupe

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Solo "super" — mismo criterio que las demas cadenas (excluye Electro, Hogar
# y textil, Tiempo Libre). Slugs obtenidos de category/tree/3 (20/07/2026).
CATEGORIAS = [
    ("Almacen",     "almacen"),
    ("Bebidas",     "bebidas"),
    ("Frescos",     "frutas-y-verduras"),
    ("Carnes",      "carnes"),
    ("Pescados",    "pescados-y-mariscos"),
    ("Fiambres",    "quesos-y-fiambres"),
    ("Lacteos",     "lacteos"),
    ("Congelados",  "congelados"),
    ("Panaderia",   "panaderia-y-pasteleria"),
    ("Rotiseria",   "rotiseria"),
    ("Perfumeria",  "perfumeria"),
    ("Limpieza",    "limpieza"),
    ("Mascotas",    "mascotas"),
    ("Bebe",        "mundo-bebe"),
    ("Pastas",      "pastas-frescas"),
]

PRECIO_MIN = 50
PRECIO_MAX = 2_000_000

_RE_2DO_AL = re.compile(r"2d[oa]\s+al\s+(\d+)\s*%", re.I)
_RE_NXM = re.compile(r"\b([2-9])\s*x\s*([1-9])\b", re.I)


def fetch_pagina(session, slug, page):
    url = f"{API_BASE}/{slug}"
    params = {
        "page": str(page),
        "count": str(PRODUCTOS_POR_PAGINA),
        "hideUnavailableItems": "true",
    }
    for espera in (0, 5, 15):
        if espera:
            print(f"    [WARN] error en {slug} pag {page}, reintento en {espera}s")
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


def texto_oferta(offer):
    """Solo promos por cantidad (teasers) — el descuento directo via ListPrice
    NO se usa en Jumbo porque el campo viene roto (ver docstring del modulo)."""
    partes = []
    promo_cantidad = False
    for t in offer.get("teasers") or []:
        cond = t.get("conditions") or {}
        nombres_cond = {p.get("name") for p in (cond.get("parameters") or [])}
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
        efectos = {p.get("name"): p.get("value")
                   for p in ((t.get("effects") or {}).get("parameters") or [])}
        pd = efectos.get("PercentualDiscount")
        if pd:
            partes.append(f"{pd}% llevando {cond.get('minimumQuantity')}")
            promo_cantidad = True

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

    if not offer.get("AvailableQuantity"):
        return None

    try:
        precio = float(offer.get("Price") or 0)
    except (TypeError, ValueError):
        return None
    if not (PRECIO_MIN <= precio <= PRECIO_MAX):
        return None
    # ListPrice no se usa como precio_regular: viene roto en el 100% del
    # catalogo (ver docstring del modulo) — se publica igual al efectivo.
    precio_regular = precio

    nombre = (prod.get("productName") or "").strip()
    if not nombre:
        return None

    oferta, promo_cantidad = texto_oferta(offer)

    link_text = prod.get("linkText") or ""
    link = f"{PRODUCTO_BASE}/{link_text}/p" if link_text else PRODUCTO_BASE

    imagenes = item.get("images") or []
    imagen = (imagenes[0] or {}).get("imageUrl", "") if imagenes else ""

    subcategoria = ""
    cats = prod.get("categories") or []
    if cats:
        segs = [s for s in cats[0].split("/") if s]
        if len(segs) >= 2:
            subcategoria = segs[1]

    return {
        "nombre": nombre,
        "precio": precio,
        "precio_regular": precio_regular,
        "oferta": oferta,
        "ean": ean,
        "sku": str(item.get("itemId") or ""),
        "sector": categoria_display,
        "subcategoria": subcategoria,
        "imagen": imagen,
        "link": link,
        "fuente": "Jumbo",
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
              f"considerar bajar a category-2")

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
                continue
            acumulado[registro["ean"]] = registro
            if registro["oferta"]:
                stats["con_oferta"] += 1
            if promo_cantidad:
                stats["promo_cantidad"] += 1

        if pagina % 5 == 0 or pagina == paginas:
            print(f"    Pag {pagina}/{paginas}: {len(acumulado)} unicos acumulados")


def main():
    print("INICIO: Scraper Jumbo PRO (VTEX Intelligent Search)")
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
              f"- revisar categorias/slugs (pueden haber cambiado).")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               f"output_jumbo_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo - {n} productos unicos (solo disponibles)")
    print(f"Con alguna oferta real: {stats['con_oferta']} ({stats['con_oferta'] * 100 // max(n, 1)}%)")
    print(f"  de las cuales promo por cantidad (2do al X% / NxM): {stats['promo_cantidad']}")
    print(f"Guardado en: {output_file}")
    print("\nResumen por categoria (nuevos aportados):")
    for nombre, count in resumen.items():
        print(f"  {nombre}: {count}")

    return productos_lista, resumen


if __name__ == "__main__":
    main()
