#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER MAXICARREFOUR - VERSION PRO RESILIENTE
El API /products filtra por SECTOR (no por subcategoria).
Estrategia: scrapeamos los 10 sectores por separado, deduplicamos por EAN.
Cookies necesarias: PHPSESSID y cf_clearance (se renuevan logueandose en el sitio).
"""

import os
import sys
import json
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_URL = "https://comerciante.carrefour.com.ar"
PRODUCTOS_POR_PAGINA = 24
DELAY = 0.5
MIN_PRODUCTS_EXPECTED = 500

PHPSESSID    = os.getenv("CARREFOUR_PHPSESSID", "")
CF_CLEARANCE = os.getenv("CARREFOUR_CF_CLEARANCE", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL + "/",
}

SECTORES = [
    ("Bebidas",             "bebidas"),
    ("Almacen",             "almacen"),
    ("Desayuno y Merienda", "desayuno y merienda"),
    ("Limpieza",            "limpieza"),
    ("Perfumeria",          "perfumeria"),
    ("Lacteos y Frescos",   "lacteos y productos frescos"),
    ("Mundo Bebe",          "mundo bebe"),
    ("Mascotas",            "mascotas"),
    ("Panaderia",           "panaderia"),
    ("Bazar y Textil",      "bazar y textil"),
]


PRECIO_MIN = 100
PRECIO_MAX = 500_000

def limpiar_precio(texto):
    if not texto:
        return 0.0
    limpio = re.sub(r"[^\d,.]", "", str(texto))
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(",", "")
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


def parsear_pagina(html, sector_display):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all(class_="item_card")
    if not items:
        items = soup.find_all(class_="item_card_public")

    productos = []
    for item in items:
        try:
            ean = ""
            ean_div = item.find(class_="ean_price")
            if ean_div:
                m = re.search(r"\d{8,13}", ean_div.get_text())
                if m:
                    ean = m.group()
            if not ean:
                m = re.search(r"\d{8,13}", item.get("onclick", ""))
                if m:
                    ean = m.group()
            if not ean:
                continue

            desc_div = item.find(class_="item_card__description")
            nombre = desc_div.get_text(strip=True).title() if desc_div else ""
            if not nombre:
                continue

            precio = 0.0
            price_div = item.find(class_="number_price")
            if price_div:
                precio = limpiar_precio(price_div.get_text(strip=True))
            else:
                cart = item.find(class_="cart_button")
                if cart:
                    precio = limpiar_precio(cart.get("data-price", ""))

            img = item.select_one("img.principal_img")
            imagen = (img.get("src", "") if img
                      else f"https://tupedido.carrefour.com.ar/imagenesPDA/{ean}.jpg")

            link = ""
            a_tag = item.find("a", href=True)
            if a_tag:
                href = a_tag.get("href", "")
                if href.startswith("/"):
                    link = BASE_URL + href
                elif href.startswith("http"):
                    link = href

            sector = sector_display
            subcategoria = ""
            cart = item.find(class_="cart_button")
            if cart:
                sec_attr = cart.get("data-sector", "").strip()
                sub_attr = cart.get("data-section", "").strip()
                if sec_attr:
                    sector = sec_attr.title()
                if sub_attr:
                    subcategoria = sub_attr.title()

            productos.append({
                "nombre": nombre,
                "precio": precio,
                "ean": ean,
                "sku": ean,
                "sector": sector,
                "subcategoria": subcategoria,
                "imagen": imagen,
                "link": link,
                "fuente": "MaxiCarrefour",
                "stock": True,
                "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception:
            continue

    return productos


def scrape_sector(session, nombre_display, slug):
    current_url = f"sec/{slug}"

    r = session.get(f"{BASE_URL}/products", params={
        "currentUrl": current_url, "filters": "", "orderBy": "default",
        "currentPage": 1, "itemsPerPage": PRODUCTOS_POR_PAGINA, "method": "countProducts"
    }, timeout=20)
    total_str = r.text.strip()
    total = int(total_str) if total_str.isdigit() else 0

    if total == 0:
        print(f"  [SKIP] {nombre_display}: 0 productos")
        return {}

    paginas = (total + PRODUCTOS_POR_PAGINA - 1) // PRODUCTOS_POR_PAGINA
    print(f"  {nombre_display.lower()}: {total} productos ({paginas} paginas)")

    sector_prods = {}
    for pagina in range(1, paginas + 1):
        try:
            r = session.get(f"{BASE_URL}/products", params={
                "currentUrl": current_url, "filters": "", "orderBy": "default",
                "currentPage": pagina, "itemsPerPage": PRODUCTOS_POR_PAGINA,
                "method": "productsList",
            }, timeout=30)

            if r.status_code != 200:
                print(f"    [WARN] Pag {pagina}: status {r.status_code}")
                break

            prods = parsear_pagina(r.text, nombre_display)
            if not prods and pagina > 1:
                break

            for p in prods:
                if p["ean"] not in sector_prods:
                    sector_prods[p["ean"]] = p

            if pagina % 5 == 0 or pagina == paginas:
                print(f"    Pag {pagina}/{paginas}: {len(sector_prods)} unicos acumulados")

            time.sleep(DELAY)

        except Exception as e:
            print(f"    [ERROR] Pag {pagina}: {e}")
            break

    return sector_prods


def main():
    print("INICIO: Scraper MaxiCarrefour PRO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sectores a scrapear: {len(SECTORES)}")
    print("=" * 55)

    if not PHPSESSID or not CF_CLEARANCE:
        print("ERROR: Cookies no configuradas. Verificá el archivo .env")
        sys.exit(1)

    session = requests.Session()
    session.cookies.update({"PHPSESSID": PHPSESSID, "cf_clearance": CF_CLEARANCE})
    session.headers.update(HEADERS)

    todos_los_productos = {}
    resumen = {}

    for i, (display_name, slug) in enumerate(SECTORES, start=1):
        print(f"\n[{i}/{len(SECTORES)}] Sector: {display_name}")
        sector_prods = scrape_sector(session, display_name, slug)
        for ean, prod in sector_prods.items():
            if ean not in todos_los_productos:
                todos_los_productos[ean] = prod
        resumen[display_name] = len(sector_prods)

    productos_lista = list(todos_los_productos.values())

    if len(productos_lista) < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Solo {len(productos_lista)} productos (min esperado: {MIN_PRODUCTS_EXPECTED}) — probablemente cookies expiradas.")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(__file__), f"output_maxicarrefour_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo — {len(productos_lista)} productos únicos")
    print(f"Guardado en: {output_file}")
    print("\nResumen por sector:")
    for nombre, count in resumen.items():
        print(f"  {nombre}: {count}")

    return productos_lista, resumen


if __name__ == "__main__":
    main()
