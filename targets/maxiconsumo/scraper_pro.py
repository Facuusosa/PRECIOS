#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER MAXICONSUMO - VERSION PRO
Estrategia: paginar categorias top-level en /sucursal_burzaco/{categoria}.html
"""

import os
import json
import re
import time
import sys
from datetime import datetime
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_URL = "https://maxiconsumo.com/sucursal_burzaco"
DELAY = 0.4
MIN_PRODUCTS_EXPECTED = 500
IMPERSONATE = "safari15_3"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
}

CATEGORIAS = [
    ("Almacen",      "almacen"),
    ("Bebidas",      "bebidas"),
    ("Frescos",      "frescos"),
    ("Limpieza",     "limpieza"),
    ("Perfumeria",   "perfumeria"),
    ("Hogar y Bazar","hogar-y-bazar"),
    ("Congelados",   "congelados"),
    ("Mascotas",     "mascotas"),
]


PRECIO_MIN = 100
PRECIO_MAX = 500_000

def limpiar_precio(texto):
    if not texto:
        return 0.0
    limpio = re.sub(r"[^\d,.]", "", str(texto))
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        partes = limpio.split(",")
        if len(partes) == 2 and len(partes[1]) <= 2:
            limpio = limpio.replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    try:
        precio = float(limpio)
        if not (PRECIO_MIN <= precio <= PRECIO_MAX):
            return 0.0
        return precio
    except ValueError:
        return 0.0


def parsear_pagina(html, sector):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("li", class_="item product product-item")
    productos = []
    for item in items:
        try:
            enlace = item.find("a", class_="product-item-link")
            if not enlace:
                continue
            nombre = enlace.get_text(strip=True)
            link = enlace.get("href", "")
            sku_m = re.search(r"-(\d+)(?:\.html)?$", link)
            sku = sku_m.group(1) if sku_m else ""

            precio_span = item.find("span", class_="price")
            precio = limpiar_precio(precio_span.get_text(strip=True)) if precio_span else 0.0

            img = item.find("img", class_="product-image-photo")
            imagen = img.get("src", "") if img else ""

            productos.append({
                "nombre": nombre,
                "precio": precio,
                "sku": sku,
                "ean": "",
                "imagen": imagen,
                "link": link,
                "sector": sector,
                "subcategoria": "",
                "fuente": "Maxiconsumo",
                "stock": True,
                "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception:
            continue
    return productos


def scrape_categoria(session, nombre_display, slug, idx, total):
    print(f"\n[{idx}/{total}] Sector: {nombre_display}")
    url_base = f"{BASE_URL}/{slug}.html"

    sector_prods = {}
    pagina = 1

    while True:
        url = url_base if pagina == 1 else f"{url_base}?p={pagina}"
        try:
            r = session.get(url, impersonate=IMPERSONATE, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                print(f"  [WARN] Pag {pagina}: status {r.status_code}")
                break

            prods = parsear_pagina(r.text, nombre_display)
            if not prods:
                break

            nuevos = 0
            for p in prods:
                key = p["sku"] or p["nombre"]
                if key not in sector_prods:
                    sector_prods[key] = p
                    nuevos += 1

            if pagina % 5 == 0:
                print(f"  Pag {pagina}: {len(sector_prods)} unicos acumulados")

            if nuevos == 0:
                break

            pagina += 1
            time.sleep(DELAY)

        except Exception as e:
            print(f"  [ERROR] Pag {pagina}: {e}")
            break

    print(f"  {nombre_display}: {len(sector_prods)} productos totales")
    return sector_prods


def main():
    print("INICIO: Scraper Maxiconsumo PRO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categorias: {len(CATEGORIAS)}")
    print("=" * 50)

    session = curl_requests.Session()
    session.headers.update(HEADERS)

    todos = {}

    for idx, (nombre, slug) in enumerate(CATEGORIAS, start=1):
        prods = scrape_categoria(session, nombre, slug, idx, len(CATEGORIAS))
        for key, prod in prods.items():
            if key not in todos:
                todos[key] = prod

    productos_lista = list(todos.values())

    if len(productos_lista) < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Productos insuficientes: {len(productos_lista)} < {MIN_PRODUCTS_EXPECTED}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(__file__), f"output_maxiconsumo_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"Scraping completo -- {len(productos_lista)} productos unicos")
    print(f"Guardado en: {output_file}")

    return productos_lista


if __name__ == "__main__":
    main()
