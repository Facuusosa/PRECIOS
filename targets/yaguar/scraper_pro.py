#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER YAGUAR - VERSION PRO (WooCommerce Store API)

El sitio elimino la navegacion HTML el ~10/07/2026: /categoria-producto/{slug}/,
/tienda/page/N/ y las fichas /producto/{slug}/ redirigen TODOS a /tienda/ (una
pagina fija con 16 productos). El scraper HTML anterior acumulaba esa pagina
repetida miles de veces (34.886 registros = 5.137 unicos el 09/07) y truncaba
el catalogo real.

La via actual es la Store API publica de WooCommerce (/wp-json/wc/store/v1/),
verificada 10/07/2026:
  - catalogo completo: 7.384 productos (x-wp-total)
  - precios identicos al HTML logueado del 09/07 (SKUs 90050 y 87568 exactos)
  - cf-cache-status: BYPASS (no es cache viejo de Cloudflare — regla 09)
  - mismos SKUs que CODIGOS.xlsx -> el matching a EAN sigue funcionando
"""

import os
import html
import json
import sys
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "https://yaguar.com.ar"
LOGIN_URL = f"{BASE_URL}/login/"
API_URL = f"{BASE_URL}/wp-json/wc/store/v1"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "es-ES,es;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
    "referer": BASE_URL + "/",
}

IMPERSONATE = "safari15_3"
DELAY_ENTRE_PAGINAS = 0.5  # la API no mostro throttle; delay de cortesia (regla anti-bloqueo Yaguar)
PER_PAGE = 100             # maximo aceptado por la Store API

PRECIO_MIN = 100
PRECIO_MAX = 500_000
MIN_PRODUCTS_EXPECTED = 5000  # catalogo real medido 10/07/2026: ~7.4k


def login(session):
    """Login WordPress. La Store API dio precios identicos anonimo vs logueado
    (medido 10/07), pero mantenemos el login por si Yaguar activa precios B2B
    diferenciados — costo cero y garantiza el precio del server (regla 09)."""
    def _login_attempt():
        print("Iniciando sesion...")
        r1 = session.get(LOGIN_URL, headers=HEADERS, impersonate=IMPERSONATE, timeout=20)
        soup = BeautifulSoup(r1.text, "html.parser")
        form = soup.find("form", {"method": "post"})
        if not form:
            raise Exception("No se encontro el formulario de login")

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

    try:
        _login_attempt()
        print("Login exitoso")
        return True
    except Exception as e:
        print(f"Login definitivamente fallido: {e}")
        return False


def get_api(session, path, params=""):
    """GET a la Store API con 3 reintentos. Devuelve (json, headers) o (None, {})."""
    url = f"{API_URL}{path}?{params}" if params else f"{API_URL}{path}"
    for intento in range(1, 4):
        try:
            r = session.get(url, headers=HEADERS, impersonate=IMPERSONATE, timeout=30)
            if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
                return r.json(), r.headers
            print(f"    API {path}: status {r.status_code} (intento {intento}/3)")
        except Exception as e:
            print(f"    API {path}: {e} (intento {intento}/3)")
        time.sleep(5 * intento)
    return None, {}


def obtener_categorias_top(session):
    """Categorias top-level (parent == 0) con sus counts, paginando la API."""
    todas = []
    pagina = 1
    while True:
        data, headers = get_api(session, "/products/categories",
                                f"per_page=100&page={pagina}")
        if data is None:
            break
        todas.extend(data)
        total_pages = int(headers.get("x-wp-totalpages", 1) or 1)
        if pagina >= total_pages:
            break
        pagina += 1
        time.sleep(DELAY_ENTRE_PAGINAS)
    top = [c for c in todas if c.get("parent", 0) == 0 and c.get("count", 0) > 0]
    return top


def parsear_producto(p, categoria_nombre):
    """Producto de la Store API -> formato de output del catalogo."""
    prices = p.get("prices", {}) or {}
    try:
        minor = int(prices.get("currency_minor_unit", 0) or 0)
        precio = float(prices.get("price") or 0) / (10 ** minor)
    except (TypeError, ValueError):
        precio = 0.0
    if not (PRECIO_MIN <= precio <= PRECIO_MAX):
        return None
    sku = str(p.get("sku", "") or "").strip()
    nombre = html.unescape(p.get("name", "") or "").strip()
    if not nombre or not sku:
        return None
    imagenes = p.get("images") or []
    return {
        "nombre": nombre,
        "sku": sku,
        "precio": precio,
        "imagen": imagenes[0].get("src", "") if imagenes else "",
        "link": p.get("permalink", ""),
        "categoria": categoria_nombre,
        "fuente": "Yaguar",
        "fecha": datetime.now().strftime("%Y-%m-%d"),
    }


def scrapear_lote(session, params_base, categoria_nombre, vistos, todos):
    """Pagina la Store API con params_base y acumula productos con SKU no visto.
    Devuelve cuantos productos nuevos agrego."""
    nuevos_total = 0
    pagina = 1
    total_pages = 1
    while pagina <= total_pages:
        data, headers = get_api(session, "/products",
                                f"{params_base}&per_page={PER_PAGE}&page={pagina}")
        if data is None:
            print(f"    AVISO: pagina {pagina} fallo tras reintentos — corto lote")
            break
        total_pages = int(headers.get("x-wp-totalpages", total_pages) or total_pages)
        for p in data:
            prod = parsear_producto(p, categoria_nombre)
            if prod is None or prod["sku"] in vistos:
                continue
            vistos.add(prod["sku"])
            todos.append(prod)
            nuevos_total += 1
        if pagina % 5 == 0 or pagina == total_pages:
            print(f"    Pag {pagina}/{total_pages}: {len(todos)} unicos acumulados")
        pagina += 1
        time.sleep(DELAY_ENTRE_PAGINAS)
    return nuevos_total


def main():
    print("Scraper Yaguar PRO — WooCommerce Store API")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    session = curl_requests.Session()
    if not login(session):
        print("Login fallido — abortando")
        sys.exit(1)

    # Total real del catalogo, para validar cobertura al final
    _, headers = get_api(session, "/products", "per_page=1")
    total_api = int(headers.get("x-wp-total", 0) or 0)
    print(f"Catalogo segun la API: {total_api} productos")

    categorias = obtener_categorias_top(session)
    if not categorias:
        print("ERROR: no se pudieron obtener las categorias — abortando")
        sys.exit(1)
    print(f"Sectores a scrapear: {len(categorias)}")
    print("=" * 55)

    todos = []
    vistos = set()
    resumen = {}

    for idx, cat in enumerate(categorias, start=1):
        print(f"\n[{idx}/{len(categorias)}] Sector: {cat['name']} (count={cat['count']})")
        nuevos = scrapear_lote(session, f"category={cat['id']}", cat["name"], vistos, todos)
        resumen[cat["name"]] = nuevos
        print(f"  {cat['name'].lower()}: {nuevos} productos nuevos")

    # Barrido general para atrapar productos sin categoria top-level
    print(f"\n[extra] Barrido general (productos sin categoria)")
    huerfanos = scrapear_lote(session, "orderby=id&order=asc", "", vistos, todos)
    resumen["(sin categoria)"] = huerfanos
    print(f"  sin categoria: {huerfanos} productos nuevos")

    if total_api and len(todos) < total_api * 0.9:
        print(f"AVISO: solo {len(todos)} de {total_api} productos de la API "
              f"(algunos pueden no tener precio valido o SKU)")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(BASE_DIR, "targets", "yaguar", f"output_yaguar_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo — {len(todos)} productos unicos")
    print(f"Guardado en: {output_file}")
    print("\nResumen por sector:")
    for cat_nombre, count in resumen.items():
        print(f"  {cat_nombre}: {count}")

    if len(todos) < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: {len(todos)} productos < minimo esperado {MIN_PRODUCTS_EXPECTED}")
        sys.exit(1)

    return todos


if __name__ == "__main__":
    main()
