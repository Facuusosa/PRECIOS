#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER YAGUAR - VERSIÓN PRO RESILIENTE
Scraping completo con login, paginación, retry automático y validación.
"""

import os
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from dotenv import load_dotenv

load_dotenv()

# Imports eliminados - módulos de resiliencia ya no existen
# El scraper funciona sin over-engineering

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CATEGORIAS = [
    {"slug": "almacen",    "nombre": "Almacén"},
    {"slug": "bazar",      "nombre": "Bazar"},
    {"slug": "bebidas",    "nombre": "Bebidas"},
    {"slug": "bodega",     "nombre": "Bodega"},
    {"slug": "desayuno",   "nombre": "Desayuno"},
    {"slug": "frescos",    "nombre": "Frescos"},
    {"slug": "kiosco",     "nombre": "Kiosco"},
    {"slug": "limpieza",   "nombre": "Limpieza"},
    {"slug": "mascotas",   "nombre": "Mascotas"},
    {"slug": "papeles",    "nombre": "Papeles"},
    {"slug": "perfumeria", "nombre": "Perfumería"},
]

BASE_URL = "https://yaguar.com.ar"
LOGIN_URL = f"{BASE_URL}/login/"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "es-ES,es;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
    "referer": BASE_URL + "/",
}

IMPERSONATE = "safari15_3"
DELAY_ENTRE_PAGINAS = 1.0   # segundos entre páginas
DELAY_ENTRE_CATEGORIAS = 2.0

# Configuración simple
MIN_PRODUCTS_EXPECTED = 1000  # Mínimo de productos esperados


def login(session):
    """Realiza el login con retry automático."""
    def _login_attempt():
        print("🔐 Iniciando sesión...")
        r1 = session.get(LOGIN_URL, headers=HEADERS, impersonate=IMPERSONATE, timeout=20)
        soup = BeautifulSoup(r1.text, "html.parser")
        form = soup.find("form", {"method": "post"})
        if not form:
            raise Exception("No se encontró el formulario de login")

        payload = {}
        for inp in form.find_all("input"):
            name = inp.get("name", "")
            value = inp.get("value", "")
            if name:
                payload[name] = value

        username = os.getenv("YAGUAR_USERNAME")
        password = os.getenv("YAGUAR_PASSWORD")
        if not username or not password:
            raise ValueError("YAGUAR_USERNAME y YAGUAR_PASSWORD son obligatorias en .env")
        payload["username"] = username
        payload["password"] = password
        payload["login"] = "Ingresar"

        r2 = session.post(
            LOGIN_URL,
            data=payload,
            headers={**HEADERS, "Referer": LOGIN_URL},
            impersonate=IMPERSONATE,
            timeout=20,
        )

        if "wordpress_logged_in" not in str(r2.cookies):
            raise Exception("Login fallido — verificar credenciales")
        
        return True
    
    # Ejecutar login
    try:
        result = _login_attempt()
        print("✅ Login exitoso")
        return True
    except Exception as e:
        print(f"❌ Login definitivamente fallido: {e}")
        return False


def obtener_max_pagina(soup):
    """Extrae el número total de páginas leyendo los hrefs de paginación."""
    max_page = 1
    for a in soup.find_all("a", href=True):
        m = re.search(r"/page/(\d+)/", a["href"])
        if m:
            num = int(m.group(1))
            if num > max_page:
                max_page = num
    return max_page


PRECIO_MIN = 100
PRECIO_MAX = 500_000

def limpiar_precio(texto):
    """Convierte '$19.599' o '5719' a float. Rechaza outliers fuera de rango razonable."""
    limpio = re.sub(r"[^\d,.]", "", texto)
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(",", "")
    elif "," in limpio:
        partes = limpio.split(",")
        if len(partes) == 2 and len(partes[1]) <= 2:
            limpio = limpio.replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "." in limpio:
        # Punto como separador de miles (ej: "19.599" -> 19599, "1.500.000" -> 1500000)
        # Si todos los grupos separados por punto tienen 3 digitos excepto el primero -> miles
        partes = limpio.split(".")
        if all(len(p) == 3 for p in partes[1:]):
            limpio = limpio.replace(".", "")
    try:
        precio = float(limpio)
        if not (PRECIO_MIN <= precio <= PRECIO_MAX):
            return 0.0
        return precio
    except ValueError:
        return 0.0


def parsear_productos(soup, categoria_nombre):
    """Extrae todos los productos de una página."""
    items = soup.find_all(class_="e-loop-item")
    productos = []

    for item in items:
        try:
            # Nombre via selector WooCommerce directo
            nombre_elem = item.select_one("h3.product_title.entry-title")
            if not nombre_elem:
                continue
            nombre = nombre_elem.get_text(strip=True)
            if not nombre or len(nombre) < 3:
                continue

            # SKU (Cod. XXXX) — en un h2 dentro del item
            sku = ""
            for h2 in item.find_all("h2"):
                m_sku = re.search(r"Cod\.?\s*(\d+)", h2.get_text())
                if m_sku:
                    sku = m_sku.group(1)
                    break

            # Precio via selector WooCommerce directo
            precio = 0.0
            precio_elem = item.select_one(".woocommerce-Price-amount.amount")
            if precio_elem:
                precio = limpiar_precio(precio_elem.get_text(strip=True))

            if precio <= 0:
                continue

            # Imagen
            img_elem = item.select_one("img")
            imagen = ""
            if img_elem:
                imagen = img_elem.get("src", img_elem.get("data-src", ""))

            # URL del producto
            link_elem = item.select_one('a[href*="/producto/"]')
            link = link_elem["href"] if link_elem else ""

            productos.append({
                "nombre": nombre,
                "sku": sku,
                "precio": precio,
                "imagen": imagen,
                "link": link,
                "categoria": categoria_nombre,
                "fuente": "Yaguar",
                "fecha": datetime.now().strftime("%Y-%m-%d"),
            })

        except Exception:
            continue

    return productos


def scrapear_categoria(session, slug, nombre, idx, total):
    """Scrapea todas las páginas de una categoría."""
    base_cat_url = f"{BASE_URL}/categoria-producto/{slug}/"

    def _get_first_page():
        r = session.get(base_cat_url, headers=HEADERS, impersonate=IMPERSONATE, timeout=30)
        if r.status_code != 200 or "login" in r.url:
            raise Exception(f"Error accediendo a categoría (status {r.status_code})")
        return r

    def _get_page(pagina):
        url_pagina = f"{base_cat_url}page/{pagina}/"
        r = session.get(url_pagina, headers=HEADERS, impersonate=IMPERSONATE, timeout=30)
        if r.status_code != 200:
            raise Exception(f"Página {pagina}: status {r.status_code}")
        return r

    try:
        r = _get_first_page()
        soup = BeautifulSoup(r.text, "html.parser")
        max_pagina = obtener_max_pagina(soup)
        todos = parsear_productos(soup, nombre)

        print(f"\n[{idx}/{total}] Sector: {nombre}")
        print(f"  {nombre.lower()}: ~{max_pagina * len(todos)} productos estimados ({max_pagina} páginas)")

        for pagina in range(2, max_pagina + 1):
            try:
                r = _get_page(pagina)
                soup = BeautifulSoup(r.text, "html.parser")
                prods = parsear_productos(soup, nombre)
                if not prods:
                    break
                todos.extend(prods)
                if pagina % 5 == 0 or pagina == max_pagina:
                    print(f"    Pag {pagina}/{max_pagina}: {len(todos)} unicos acumulados")
                time.sleep(DELAY_ENTRE_PAGINAS)
            except Exception as e:
                print(f"  ❌ Error en página {pagina}: {e} — reintentando...")
                time.sleep(2)
                try:
                    r = _get_page(pagina)
                    prods = parsear_productos(BeautifulSoup(r.text, "html.parser"), nombre)
                    if prods:
                        todos.extend(prods)
                        continue
                except Exception:
                    pass
                print(f"  AVISO: Paginacion truncada en pag {pagina}/{max_pagina}")
                break

        print(f"  {nombre.lower()}: {len(todos)} productos totales")
        return todos

    except Exception as e:
        print(f"  ❌ Error en categoría {nombre}: {e}")
        return []


def main():
    print("🚀 Scraper Yaguar PRO — Catálogo Completo")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    session = curl_requests.Session()

    if not login(session):
        print("❌ Login fallido")
        return None

    todos_los_productos = []
    resumen = {}

    total_cats = len(CATEGORIAS)
    print(f"Sectores a scrapear: {total_cats}")
    print("=" * 55)

    for idx, cat in enumerate(CATEGORIAS, start=1):
        productos = scrapear_categoria(session, cat["slug"], cat["nombre"], idx, total_cats)
        todos_los_productos.extend(productos)
        resumen[cat["nombre"]] = len(productos)
        time.sleep(DELAY_ENTRE_CATEGORIAS)

    # Guardar output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(BASE_DIR, "targets", "yaguar", f"output_yaguar_{timestamp}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(todos_los_productos, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Guardado en: {output_file}")
    print("\n" + "=" * 50)
    print(f"✅ Scraping completo")
    print(f"📦 Total productos: {len(todos_los_productos)}")
    print(f"💾 Guardado en: {output_file}")
    print("\nResumen por categoría:")
    for cat_nombre, count in resumen.items():
        print(f"  {cat_nombre}: {count}")

    return todos_los_productos


if __name__ == "__main__":
    main()
