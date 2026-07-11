#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER DIA ONLINE (diaonline.supermercadosdia.com.ar) - VERSION PRO
Fuente tipo "cadena minorista" (no mayorista) — mismo trato que Coto y
Carrefour retail. Sitio sobre VTEX (accountName=diaio, header powered=vtex),
sin Cloudflare ni ningun anti-bot detectado (mas simple que Carrefour).

API: legacy Catalog System (verificado 06/07/2026) — el Intelligent Search
moderno (/api/io/_v/api/intelligent-search) NO filtra bien por categoria con
el slug simple (devuelve el catalogo completo), por eso se usa el legacy:
  /api/catalog_system/pub/products/search?fq=C:{id}&_from=X&_to=Y
- Paginacion por indice (_from/_to), step de 50 (confirmado estable; pedir
  100 de una vez trunca por debajo). Cap legacy clasico VTEX: 2.500 por fq —
  ninguna categoria "super" de DIA se acerca (max medido ~1.100).
- Sin parametro tipo hideUnavailableItems: el legacy trae TAMBIEN productos
  sin stock con precios de anos de antiguedad (misma trampa que Coto/Carrefour/
  regla 08) — filtro obligatorio por AvailableQuantity>0 del lado cliente.

EAN 100% (items[].ean) -> integracion directa por EAN, sin fuzzy.

Precio (verificado contra muestras reales 06/07/2026):
- Price = precio EFECTIVO. ListPrice = precio regular (tachado).
  Oferta directa = Price < ListPrice.
- Trampa de precio por unidad de medida (litro/kg) vive en las specifications
  del producto (PrecioPorUnd/UnidaddeMedida) — NUNCA usar, mismo patron que
  formatPrice (Coto) y pricePerUnit (Carrefour). Este scraper ni la toca.
- Promos "2do al X%"/NxM viven en PromotionTeasers[] (ya en PascalCase limpio,
  a diferencia del legacy crudo que serializa en <Name>k__BackingField).
- NO se detecto teaser de medio de pago (tipo "Tarjeta X%" de Carrefour) en
  muestras de Almacen (39 prods) ni Bebidas (50 prods, 16 con teaser real) —
  si aparece "RestrictionsBins" en conditions, igual se excluye por las dudas.
"""

import os
import re
import sys
import json
import time
from datetime import datetime

import requests

API_BASE = "https://diaonline.supermercadosdia.com.ar/api/catalog_system/pub/products/search"
PRODUCTO_BASE = "https://diaonline.supermercadosdia.com.ar"
STEP = 50                    # confirmado estable (100 trunca por debajo)
CAP_ALERTA = 2_400           # colchon antes del techo clasico VTEX de 2.500/fq
DELAY = 0.5
MIN_PRODUCTS_EXPECTED = 3_000  # disponibles medidos 06/07/2026: ~4.000-5.000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Solo super — mismo criterio que Carrefour retail (excluye Electro Hogar,
# Indumentaria, Tecnologia, Colchones, Aire libre, Hogar y Deco). IDs
# obtenidos de /api/catalog_system/pub/category/tree/3 (06/07/2026).
CATEGORIAS = [
    ("Almacen",     1),
    ("Desayuno",    80),
    ("Bebidas",     164),
    ("Frescos",     121),
    ("Congelados",  200),
    ("Limpieza",    282),
    ("Perfumeria",  216),
    ("Mascotas",    71),
    ("Bebe",        53),
]

PRECIO_MIN = 50
PRECIO_MAX = 2_000_000

_RE_2DO_AL = re.compile(r"2d[oa]\s+al\s+(\d+)\s*%", re.I)
_RE_NXM = re.compile(r"\b([2-9])\s*x\s*([1-9])\b", re.I)


def fetch_rango(session, cat_id, desde, hasta):
    """GET con retry/backoff ante 429/5xx."""
    params = {"fq": f"C:{cat_id}", "_from": str(desde), "_to": str(hasta)}
    for espera in (0, 5, 15):
        if espera:
            print(f"    [WARN] error en categoria {cat_id} rango {desde}-{hasta}, reintento en {espera}s")
            time.sleep(espera)
        try:
            r = session.get(API_BASE, params=params, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code in (200, 206):
            try:
                return r.json()
            except ValueError:
                return None
        if r.status_code == 404:
            return []
        if r.status_code not in (429, 500, 502, 503):
            return None
    return None


def total_disponible(session, cat_id):
    """Header 'resources: 0-N/TOTAL' de un pedido chico solo para conocer el total."""
    params = {"fq": f"C:{cat_id}", "_from": "0", "_to": "1"}
    try:
        r = session.get(API_BASE, params=params, timeout=30)
    except requests.RequestException:
        return None
    if r.status_code not in (200, 206):
        return None
    resources = r.headers.get("resources", "")
    m = re.search(r"/(\d+)$", resources)
    return int(m.group(1)) if m else None


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
    for t in offer.get("PromotionTeasers") or []:
        cond = t.get("Conditions") or {}
        nombres_cond = {p.get("Name") for p in (cond.get("Parameters") or [])}
        # Por las dudas: si algun dia aparece un teaser de medio de pago con
        # RestrictionsBins (patron Carrefour), no contarlo como oferta real.
        if "RestrictionsBins" in nombres_cond:
            continue
        if (cond.get("MinimumQuantity") or 0) < 2:
            continue
        nombre_t = t.get("Name") or ""
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
        efectos = {p.get("Name"): p.get("Value")
                   for p in ((t.get("Effects") or {}).get("Parameters") or [])}
        pd = efectos.get("PercentualDiscount")
        if pd:
            partes.append(f"{pd}% llevando {cond.get('MinimumQuantity')}")
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
    seller = next((s for s in sellers if s.get("sellerDefault") or s.get("SellerId") == "1"), sellers[0] if sellers else None)
    if not seller:
        return None
    offer = seller.get("commertialOffer") or {}

    # El legacy no tiene hideUnavailableItems: trae tambien sin stock con
    # precios viejos (regla 08 / misma trampa Coto/Carrefour) -> filtro obligatorio
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
        "fuente": "Dia",
        "stock": True,  # sin stock se filtra arriba
        "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
    }, promo_cantidad


def scrape_categoria(session, nombre_display, cat_id, acumulado, stats):
    total = total_disponible(session, cat_id)
    if total is None:
        print(f"  [SKIP] {nombre_display}: API sin respuesta")
        return
    print(f"  {nombre_display}: {total} disponibles reportados")
    if total > CAP_ALERTA:
        print(f"  [WARN] {nombre_display} cerca del cap clasico de 2.500 por fq - revisar")

    desde = 0
    pagina = 0
    paginas_totales = (total + STEP - 1) // STEP if total else 1
    while desde < total:
        hasta = min(desde + STEP - 1, total - 1, CAP_ALERTA + STEP)
        pagina += 1
        if pagina > 1:
            time.sleep(DELAY)
        data = fetch_rango(session, cat_id, desde, hasta)
        if data is None:
            print(f"    [WARN] {nombre_display} rango {desde}-{hasta}: sin respuesta, sigo")
            desde += STEP
            continue
        if not data:
            break

        for prod in data:
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

        if pagina % 5 == 0 or desde + STEP >= total:
            print(f"    Pag {pagina}/{paginas_totales}: {len(acumulado)} unicos acumulados")

        desde += STEP


def main():
    print("INICIO: Scraper DIA Online PRO (VTEX legacy Catalog System)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categorias a scrapear: {len(CATEGORIAS)}")
    print("=" * 55)

    session = requests.Session()
    session.headers.update(HEADERS)

    todos = {}
    stats = {"con_oferta": 0, "promo_cantidad": 0}
    resumen = {}

    for i, (nombre_display, cat_id) in enumerate(CATEGORIAS, start=1):
        print(f"\n[{i}/{len(CATEGORIAS)}] Categoria: {nombre_display}")
        antes = len(todos)
        scrape_categoria(session, nombre_display, cat_id, todos, stats)
        resumen[nombre_display] = len(todos) - antes
        print(f"  {nombre_display}: {resumen[nombre_display]} productos nuevos")
        time.sleep(DELAY)

    productos_lista = list(todos.values())
    n = len(productos_lista)

    if n < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Solo {n} productos (min esperado: {MIN_PRODUCTS_EXPECTED}) "
              f"- revisar categorias/IDs (pueden haber cambiado).")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               f"output_dia_{timestamp}.json")

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
