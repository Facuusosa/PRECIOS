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
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_URL = "https://maxiconsumo.com/sucursal_burzaco"
DELAY = 0.3   # reducido de 0.4 — con impersonation es seguro
MIN_PRODUCTS_EXPECTED = 3500
IMPERSONATE = "safari15_3"
CAT_WORKERS = 1   # secuencial: paralelo 3 triggerea rate-limit de Cloudflare (bug 18/06)

_cat_thread_local = threading.local()

def _get_cat_session():
    if not hasattr(_cat_thread_local, "session"):
        s = curl_requests.Session()
        s.headers.update(HEADERS)
        _cat_thread_local.session = s
    return _cat_thread_local.session

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
    """Devuelve (productos_con_stock, skus_crudos_de_la_pagina).

    skus_crudos incluye tambien los sin stock: el bucle de paginacion los
    necesita para distinguir 'pagina sin items' (fin real) de 'pagina entera
    sin stock' (hay que seguir) y para detectar la pagina repetida que Magento
    devuelve al pasarse del final. Verificado 14/07/2026: frescos.html pag 11
    venia 100% sin stock y el corte viejo (if not prods) tiraba la categoria.
    """
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("li", class_="item product product-item")
    productos = []
    skus_crudos = []
    for item in items:
        try:
            enlace = item.find("a", class_="product-item-link")
            if not enlace:
                continue
            nombre = enlace.get_text(strip=True)
            link = enlace.get("href", "")
            sku_m = re.search(r"-(\d+)(?:\.html)?$", link)
            sku = sku_m.group(1) if sku_m else ""
            skus_crudos.append(sku or nombre)

            # Saltar productos sin stock (precio inflado o no disponible)
            sin_stock = bool(item.find(string=re.compile(r"disponibilidad cr[ií]tica", re.IGNORECASE)))
            if sin_stock:
                continue

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
    return productos, skus_crudos


def _get_con_guardian(session, url, timeout_total=30):
    """session.get() con limite duro de tiempo real, no solo el timeout de curl.

    Verificado 22/07/2026: una conexion colgada (bloqueo de Cloudflare que ni
    siquiera cierra el socket) dejo el proceso 30+ min esperando una sola pagina
    sin disparar el timeout=25 de curl_cffi ni ninguna excepcion. Un thread
    daemon con join(timeout_total) corta la espera pase lo que pase; el thread
    colgado queda abandonado (daemon=True: no bloquea el cierre del proceso).
    """
    resultado = {}

    def _trabajo():
        try:
            resultado["r"] = session.get(url, impersonate=IMPERSONATE, headers=HEADERS, timeout=25)
        except Exception as e:
            resultado["e"] = e

    t = threading.Thread(target=_trabajo, daemon=True)
    t.start()
    t.join(timeout_total)
    if t.is_alive():
        raise TimeoutError(f"sin respuesta tras {timeout_total}s (conexion colgada)")
    if "e" in resultado:
        raise resultado["e"]
    return resultado["r"]


def scrape_categoria(session_ignored, nombre_display, slug, idx, total):
    session = _get_cat_session()  # session persistente por thread
    print(f"\n[{idx}/{total}] Sector: {nombre_display}")
    url_base = f"{BASE_URL}/{slug}.html"

    sector_prods = {}
    pagina = 1
    skus_pagina_anterior = None
    paginas_sin_nuevos = 0
    MAX_PAGINAS = 300   # tope duro: 12/pag x 300 = 3600, mas que cualquier categoria

    while pagina <= MAX_PAGINAS:
        url = url_base if pagina == 1 else f"{url_base}?p={pagina}"

        # Reintento con backoff: un timeout suelto (bloqueo/rate-limit intermitente de
        # Cloudflare, no error de codigo) no debe cortar el resto de la categoria entera.
        # Verificado 22/07/2026: Bebidas/Frescos/Limpieza murieron en la pagina 1 por UN
        # timeout, y Almacen perdio el resto por un blip en la pagina 156 -- con reintento
        # esas categorias tienen otra chance de pasar el bloqueo.
        r = None
        backoffs = (10, 30)
        for intento in range(len(backoffs) + 1):
            try:
                r = _get_con_guardian(session, url)
                break
            except Exception as e:
                if intento < len(backoffs):
                    espera = backoffs[intento]
                    print(f"  [WARN] Pag {pagina}: {e} -- reintentando en {espera}s ({intento + 1}/{len(backoffs)})")
                    time.sleep(espera)
                else:
                    print(f"  [ERROR] Pag {pagina}: {e} -- {len(backoffs) + 1} intentos agotados")
        if r is None:
            break  # timeout persistente tras reintentos: recien ahi se corta la categoria

        if r.status_code != 200:
            print(f"  [WARN] Pag {pagina}: status {r.status_code}")
            break

        prods, skus_crudos = parsear_pagina(r.text, nombre_display)
        if not skus_crudos:
            break  # pagina sin items = fin real de la categoria
        if skus_crudos == skus_pagina_anterior:
            break  # Magento repite la misma pagina al pasarse del final
        skus_pagina_anterior = skus_crudos
        # OJO: prods vacio con items crudos = pagina entera sin stock -> seguir

        nuevos = 0
        for p in prods:
            key = p["sku"] or p["nombre"]
            if key not in sector_prods:
                sector_prods[key] = p
                nuevos += 1

        # Corte por estancamiento: verificado 22/07/2026 que Almacen paso de la pagina 130
        # a la 300 (170 requests inutiles) sin agregar NINGUN producto nuevo -- el sitio
        # reordena/repite cerca del limite sin devolver una pagina IDENTICA (por eso el
        # chequeo de "skus_crudos == skus_pagina_anterior" no lo agarraba). 3 paginas
        # seguidas sin nada nuevo es fin real de la categoria.
        if nuevos == 0:
            paginas_sin_nuevos += 1
            if paginas_sin_nuevos >= 3:
                break
        else:
            paginas_sin_nuevos = 0

        if pagina % 5 == 0:
            print(f"  Pag {pagina}: {len(sector_prods)} unicos acumulados")

        pagina += 1
        time.sleep(DELAY)

    total_sector = len(sector_prods)
    minimos = {"Almacen": 800, "Perfumeria": 500, "Bebidas": 400, "Limpieza": 400}
    minimo = minimos.get(nombre_display, 0)
    if minimo and total_sector < minimo:
        print(f"  [WARN] {nombre_display}: {total_sector} productos (esperado >={minimo}) -- posible bloqueo")
    print(f"  {nombre_display}: {total_sector} productos totales")
    return sector_prods


def main():
    print("INICIO: Scraper Maxiconsumo PRO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categorias: {len(CATEGORIAS)}")
    print("=" * 50)

    todos = {}
    lock = threading.Lock()
    total = len(CATEGORIAS)

    with ThreadPoolExecutor(max_workers=CAT_WORKERS) as executor:
        futuros = {
            executor.submit(scrape_categoria, None, nombre, slug, idx, total): nombre
            for idx, (nombre, slug) in enumerate(CATEGORIAS, start=1)
        }
        for fut in as_completed(futuros):
            nombre_cat = futuros[fut]
            try:
                prods = fut.result()
            except Exception as e:
                # Una categoria que crashea no mata el scrape entero (regla 01:
                # log, skip, continuar). Antes el traceback moria en el buffer.
                print(f"  [ERROR] Categoria {nombre_cat} crasheo: {type(e).__name__}: {e}")
                continue
            with lock:
                for key, prod in prods.items():
                    if key not in todos:
                        todos[key] = prod

    productos_lista = list(todos.values())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if len(productos_lista) < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Productos insuficientes: {len(productos_lista)} < {MIN_PRODUCTS_EXPECTED}")
        # Guardar igual lo recolectado (nunca tirar scraping real a la basura): un intento
        # insuficiente puede completar categorias que el intento anterior no pudo, y sirve
        # para mezclar a mano el mejor resultado de varios intentos del mismo dia.
        # OJO: el nombre NUNCA debe empezar con "output_maxiconsumo_" -- actualizar_catalogo.py:694
        # globea ese patron y lo tomaria como fuente valida, contaminando el catalogo con una
        # corrida incompleta (categorias enteras faltantes).
        debug_file = os.path.join(os.path.dirname(__file__), f"descartado_insuficiente_maxiconsumo_{timestamp}.json")
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(productos_lista, f, ensure_ascii=False, indent=2)
        print(f"Guardado igual (insuficiente, no se usa en el catalogo automaticamente): {debug_file}")
        sys.exit(1)

    output_file = os.path.join(os.path.dirname(__file__), f"output_maxiconsumo_raw_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"Scraping completo -- {len(productos_lista)} productos unicos")
    print(f"Guardado en: {output_file}")

    return productos_lista


if __name__ == "__main__":
    main()
