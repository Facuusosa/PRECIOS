#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER MASONLINE (masonline.com.ar) - VERSION PRO
Fuente tipo "cadena minorista" (no mayorista) — mismo trato que Coto,
Carrefour retail y Dia. Sitio sobre VTEX (header powered=vtex via CloudFront,
SIN Cloudflare), sin auth, sin cookies (verificado 20/07/2026).

API: legacy Catalog System (igual patron que Dia — mas simple que Intelligent
Search, que en este sitio no fue necesario probar porque el legacy ya
funciona directo):
  /api/catalog_system/pub/products/search?fq=C:{id}&_from=X&_to=Y
- Paginacion por indice, step 50. Cap clasico VTEX ~2.500 por fq: una sola
  categoria (Desayunos y Meriendas, id 200039) lo roza (~2.900 medido) —
  se acepta el corte con WARN, mismo criterio que Dia.
- El arbol de categorias de Masonline NO tiene agrupador "super" (a
  diferencia de Dia/Jumbo): cada nodo del arbol (depth 2) ya es una
  categoria especifica (ids 200xxx). Por eso CATEGORIAS agrupa varios ids
  bajo un mismo sector display para el catalogo (ej. "Almacen" = 12 ids).
- Sin hideUnavailableItems en el legacy: trae tambien productos sin stock
  con precios de anos de antiguedad (misma trampa que Coto/Carrefour/Dia/
  regla 08) — filtro obligatorio por AvailableQuantity>0 del lado cliente.

EAN 100% (items[].ean) -> integracion directa por EAN, sin fuzzy.

Precio: Price = efectivo, ListPrice = regular (tachado). Trampa de precio
por unidad de medida vive en las specifications del producto — nunca usar,
mismo patron ya documentado para Coto/Carrefour/Dia (regla 09).
"""

import os
import re
import sys
import json
import time
from datetime import datetime

import requests

API_BASE = "https://www.masonline.com.ar/api/catalog_system/pub/products/search"
PRODUCTO_BASE = "https://www.masonline.com.ar"
STEP = 50
CAP_ALERTA = 2_400
DELAY = 0.5
MIN_PRODUCTS_EXPECTED = 5_500  # medido 20/07/2026: 7.433 reales (disponibles+dedupe) de ~29.800 brutos

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Solo "super" — mismo criterio que Dia/Carrefour (excluye Electro, Hogar y
# Textil, Bazar y Cocina, Jugueteria, Herramientas/Pintureria, Patio y
# Jardin, Climatizacion, TV/Audio/Informatica/Celulares/Gaming, Camping/
# Deportes/Viaje, Libreria y Arte, Accesorios para Auto, Indumentaria).
# IDs obtenidos de /api/catalog_system/pub/category/tree/2 (20/07/2026).
CATEGORIAS = [
    ("Almacen", [
        200005,  # Aceites, Vinagres y Aderezos
        200009,  # Arroz, Legumbres y Pastas
        200019,  # Caldos, Sopas y Pure
        200027,  # Condimentos y Especias
        200029,  # Conservas y Enlatados
        200039,  # Desayunos y Meriendas
        200053,  # Harinas
        200064,  # Kiosco
        200043,  # Panaderia
        200079,  # Panificados
        200094,  # Reposteria
        200100,  # Snacks
    ]),
    ("Frescos", [
        200022,  # Carniceria
        200088,  # Pescaderia
        200057,  # Huevos
        200103,  # Verduras
        200048,  # Frutas
        200066,  # Lacteos
        200093,  # Quesos
        200046,  # Fiambres y Embutidos
        200084,  # Pastas y Tapas
    ]),
    ("Congelados", [200028]),
    ("Bebidas", [
        200023,  # Cervezas
        200104,  # Vinos y Espumantes
        200044,  # Fernet y Aperitivos
        200015,  # Bebidas Blancas, Licores y Whiskys
        200051,  # Gaseosas
        200006,  # Aguas
        200062,  # Jugos
        200016,  # Bebidas Isotonicas y Energizantes
        200001,  # A Base de Hierbas
    ]),
    ("Perfumeria", [
        200031,  # Cuidado de la Piel
        200032,  # Cuidado del Adulto
        200012,  # Pañales e Higiene
        200030,  # Cuidado de la Mama
        200034,  # Cuidado del Cabello
        200035,  # Cuidado Oral
        200036,  # Cuidado Personal
        200076,  # Nutricion
        200092,  # Farmacia
        200047,  # Fragancias
        200038,  # Dermocosmetica
        200033,  # Maquillaje
        200042,  # Electro Belleza
        200112,  # Proteccion Femenina
    ]),
    ("Limpieza", [
        200002,  # Accesorios de Limpieza
        200011,  # Baño
        200040,  # Desodorante de Ambientes
        200060,  # Insecticidas
        200068,  # Lavandinas
        200082,  # Papeles, Bolsas y Films
        200090,  # Pisos y Muebles
        200113,  # Limpieza de Baño
        200067,  # Lavado de la Ropa
        200086,  # Limpieza del Hogar
    ]),
    ("Mascotas", [
        200087,  # Perros
        200052,  # Gatos
    ]),
    ("Bebe", [200065]),  # Lactancia y Alimentacion
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
    partes = []
    if 0 < precio < precio_regular:
        pct = round((1 - precio / precio_regular) * 100)
        if pct >= 1:
            partes.append(f"{pct}% OFF")

    promo_cantidad = False
    for t in offer.get("PromotionTeasers") or []:
        cond = t.get("Conditions") or {}
        nombres_cond = {p.get("Name") for p in (cond.get("Parameters") or [])}
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
        "fuente": "Masonline",
        "stock": True,  # sin stock se filtra arriba
        "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
    }, promo_cantidad


def scrape_categoria_id(session, nombre_display, cat_id, acumulado, stats):
    total = total_disponible(session, cat_id)
    if total is None:
        print(f"    [SKIP] id={cat_id}: API sin respuesta")
        return
    if total == 0:
        return
    if total > CAP_ALERTA:
        print(f"    [WARN] id={cat_id} ({total} disponibles) cerca del cap clasico de 2.500 por fq")

    desde = 0
    pagina = 0
    while desde < total:
        hasta = min(desde + STEP - 1, total - 1, CAP_ALERTA + STEP)
        pagina += 1
        if pagina > 1:
            time.sleep(DELAY)
        data = fetch_rango(session, cat_id, desde, hasta)
        if data is None:
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
                continue
            acumulado[registro["ean"]] = registro
            if registro["oferta"]:
                stats["con_oferta"] += 1
            if promo_cantidad:
                stats["promo_cantidad"] += 1

        desde += STEP


def main():
    print("INICIO: Scraper Masonline PRO (VTEX legacy Catalog System)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sectores a scrapear: {len(CATEGORIAS)}")
    print("=" * 55)

    session = requests.Session()
    session.headers.update(HEADERS)

    todos = {}
    stats = {"con_oferta": 0, "promo_cantidad": 0}
    resumen = {}

    for i, (nombre_display, ids) in enumerate(CATEGORIAS, start=1):
        print(f"\n[{i}/{len(CATEGORIAS)}] Sector: {nombre_display} ({len(ids)} subcategorias)")
        antes = len(todos)
        for j, cat_id in enumerate(ids, start=1):
            scrape_categoria_id(session, nombre_display, cat_id, todos, stats)
            if j % 5 == 0 or j == len(ids):
                print(f"    Subcat {j}/{len(ids)}: {len(todos)} unicos acumulados")
            time.sleep(DELAY)
        resumen[nombre_display] = len(todos) - antes
        print(f"  {nombre_display}: {resumen[nombre_display]} productos nuevos")

    productos_lista = list(todos.values())
    n = len(productos_lista)

    if n < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Solo {n} productos (min esperado: {MIN_PRODUCTS_EXPECTED}) "
              f"- revisar categorias/IDs (pueden haber cambiado).")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               f"output_masonline_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo - {n} productos unicos (solo disponibles)")
    print(f"Con alguna oferta real: {stats['con_oferta']} ({stats['con_oferta'] * 100 // max(n, 1)}%)")
    print(f"  de las cuales promo por cantidad (2do al X% / NxM): {stats['promo_cantidad']}")
    print(f"Guardado en: {output_file}")
    print("\nResumen por sector (nuevos aportados):")
    for nombre, count in resumen.items():
        print(f"  {nombre}: {count}")

    return productos_lista, resumen


if __name__ == "__main__":
    main()
