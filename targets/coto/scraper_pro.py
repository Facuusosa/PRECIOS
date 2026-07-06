#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER COTO DIGITAL - VERSION PRO
Fuente tipo "cadena minorista" (no mayorista). El buscador de Coto esta
tercerizado en Constructor.io (ac.cnstrc.com): API JSON publica, sin login,
sin cookies, sin WAF. Solo requiere la API key publica embebida en el JS del sitio.
EAN 100% (product_main_ean) -> integracion directa por EAN, sin fuzzy.

Cap de la API: max 10.000 resultados navegables por group_id (pag 51 devuelve
vacio aunque total_num_results sea mayor — medido 05/07/2026, Almacen=11.403).
Mitigacion: si una categoria supera el cap, se scrapean sus subgrupos
(response.groups[0].children) ademas de la raiz hasta el cap; dedupe por EAN.

Precio (verificado contra la web el 05/07/2026, caso Pomada Wassington 60cc):
- price[].listPrice  = precio regular de gondola (mediana entre sucursales)
- price[].formatPrice = precio por unidad de medida (litro/kg), NO es el precio
  (Glade 360ml: formatPrice 527.75 x 0.36 = listPrice 189.99)
- discounts[].discountPrice = precio de OFERTA vigente ("$8056.30"). Medido
  05/07/2026: ~55% de la gondola tiene oferta activa -> "precio" del output =
  precio efectivo (oferta si existe, sino regular); el regular va en
  "precio_regular" y el texto ("30%Dto") en "oferta".
Productos sin store_availability se saltean: Coto los muestra "no disponible"
sin precio, y su listPrice en Constructor puede tener AnOS de antiguedad
(misma trampa que la regla 08-precios-sin-stock de Maxiconsumo).
"""

import os
import sys
import json
import time
from datetime import datetime
from statistics import median

import requests

# Key PUBLICA de Constructor.io embebida en el JS de cotodigital — no es un
# secreto (cualquier visitante la ve en su browser). Overrideable por .env
# por si Coto la rota algun dia.
API_KEY = os.getenv("COTO_CONSTRUCTOR_KEY", "key_r6xzz4IAoTWcipni")
API_BASE = "https://ac.cnstrc.com/browse/group_id"
PRODUCTO_BASE = "https://www.cotodigital.com.ar/sitios/cdigi/productos"
PRODUCTOS_POR_PAGINA = 200
API_CAP = 10_000          # max resultados navegables por group_id
DELAY = 0.3               # API de terceros sin rate-limit observado; delay de cortesia
MIN_PRODUCTS_EXPECTED = 10_000  # universo con stock medido 05/07/2026: ~14.700

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Solo las 6 categorias de "super" — Hogar/Textil/Electro quedan afuera
# porque no tienen contraparte mayorista (decision de producto 04/07/2026)
CATEGORIAS = [
    ("Almacen",    "catv00001254"),
    ("Frescos",    "catv00001255"),
    ("Bebidas",    "catv00001256"),
    ("Limpieza",   "catv00001258"),
    ("Perfumeria", "catv00001257"),
    ("Congelados", "catv00001296"),
]

PRECIO_MIN = 50
PRECIO_MAX = 2_000_000


def fetch_pagina(session, group_id, page, per_page=PRODUCTOS_POR_PAGINA):
    r = session.get(
        f"{API_BASE}/{group_id}",
        params={
            "key": API_KEY,
            "i": "brujula-de-precios",
            "s": "1",
            "c": "ciojs-client-2.1436.1",
            "num_results_per_page": str(per_page),
            "page": str(page),
            "_dt": str(int(time.time() * 1000)),
        },
        timeout=30,
    )
    if r.status_code != 200:
        return None
    return r.json().get("response", {})


def precio_mediana(data):
    # Coto devuelve ~34 precios (uno por sucursal), casi siempre iguales pero
    # con outliers reales -> mediana robusta. listPrice = precio de venta;
    # formatPrice es por litro/kg y NO sirve (ver docstring del modulo)
    precios = []
    for p in data.get("price", []):
        try:
            v = float(p.get("listPrice", 0))
        except (TypeError, ValueError):
            continue
        if PRECIO_MIN <= v <= PRECIO_MAX:
            precios.append(v)
    if not precios:
        return 0.0
    return round(median(precios), 2)


def precio_oferta(data, precio_regular):
    """Precio de oferta vigente desde discounts[].discountPrice ("$8056.30").
    Devuelve 0 si no hay oferta valida (debe ser > 0 y < regular)."""
    for d in data.get("discounts") or []:
        crudo = str(d.get("discountPrice") or "").replace("$", "").replace(",", "").strip()
        try:
            v = float(crudo)
        except ValueError:
            continue
        if PRECIO_MIN <= v < precio_regular:
            texto = str(d.get("discountText") or "").strip()
            return v, texto
    return 0.0, ""


def parsear_resultado(res, categoria_display):
    data = res.get("data", {})

    ean = str(data.get("product_main_ean") or "").strip()
    if not ean or ean == "0":
        return None

    # Sin disponibilidad en ninguna sucursal = "no disponible" en la web, sin
    # precio visible; su listPrice puede ser de anos atras -> no capturar
    if not data.get("store_availability"):
        return None

    nombre = (data.get("sku_description") or res.get("value") or "").strip()
    if not nombre:
        return None

    precio_regular = precio_mediana(data)
    if precio_regular <= 0:
        return None

    oferta, oferta_texto = precio_oferta(data, precio_regular)
    # "precio" = lo que paga el publico HOY en la gondola digital
    precio = oferta if oferta > 0 else precio_regular

    imagen = data.get("image_url") or data.get("product_medium_image_url") or ""

    # data["url"] viene como "_/R-{id}-{id}-200"; la SPA resuelve por ID,
    # el slug es opcional (verificado en vivo 05/07/2026 con 3 formatos)
    url_rel = str(data.get("url") or "")
    if url_rel.startswith("_/R-"):
        link = f"{PRODUCTO_BASE}/{url_rel}"
    else:
        link = "https://www.cotodigital.com.ar/sitios/cdigi/nuevositio"

    subcategoria = ""
    grupos = data.get("groups", [])
    if grupos:
        path = [g.get("display_name", "") for g in grupos[0].get("path_list", [])]
        # path_list = ["Categorias", "Almacen", "Conservas", ...]
        if len(path) >= 3:
            subcategoria = path[2]

    return {
        "nombre": nombre,
        "precio": precio,
        "precio_regular": precio_regular,
        "oferta": oferta_texto,          # "" si no hay oferta vigente
        "ean": ean,
        "sku": str(data.get("sku_plu") or ""),
        "sector": categoria_display,
        "subcategoria": subcategoria,
        "imagen": imagen,
        "link": link,
        "fuente": "Coto",
        "stock": True,  # los sin disponibilidad se saltean arriba
        "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
    }


def scrape_grupo(session, group_id, categoria_display, acumulado, etiqueta):
    """Pagina un group_id completo (hasta el cap). Suma a `acumulado` (dict por EAN)."""
    resp = fetch_pagina(session, group_id, 1)
    if resp is None:
        print(f"    [WARN] {etiqueta}: sin respuesta de la API")
        return 0

    total = resp.get("total_num_results", 0)
    if total == 0:
        return 0

    paginas = min(
        (total + PRODUCTOS_POR_PAGINA - 1) // PRODUCTOS_POR_PAGINA,
        API_CAP // PRODUCTOS_POR_PAGINA,
    )

    nuevos = 0
    for pagina in range(1, paginas + 1):
        if pagina == 1:
            resultados = resp.get("results", [])
        else:
            time.sleep(DELAY)
            page_resp = fetch_pagina(session, group_id, pagina)
            if page_resp is None:
                print(f"    [WARN] {etiqueta} pag {pagina}: sin respuesta, sigo")
                continue
            resultados = page_resp.get("results", [])

        if not resultados:
            break

        for res in resultados:
            prod = parsear_resultado(res, categoria_display)
            if prod and prod["ean"] not in acumulado:
                acumulado[prod["ean"]] = prod
                nuevos += 1

        if pagina % 5 == 0 or pagina == paginas:
            print(f"    Pag {pagina}/{paginas}: {len(acumulado)} unicos acumulados")

    return nuevos


def scrape_categoria(session, nombre_display, group_id, acumulado):
    resp = fetch_pagina(session, group_id, 1, per_page=1)
    if resp is None:
        print(f"  [SKIP] {nombre_display}: API sin respuesta")
        return

    total = resp.get("total_num_results", 0)
    print(f"  {nombre_display}: {total} productos reportados")

    scrape_grupo(session, group_id, nombre_display, acumulado, nombre_display)

    if total > API_CAP:
        # El cap dejo productos afuera -> barrer tambien cada subgrupo
        hijos = []
        grupos = resp.get("groups", [])
        if grupos:
            hijos = grupos[0].get("children", [])
        print(f"  {nombre_display} supera el cap de {API_CAP} — barriendo {len(hijos)} subgrupos")
        for hijo in hijos:
            hijo_id = hijo.get("group_id", "")
            hijo_nombre = hijo.get("display_name", hijo_id)
            if not hijo_id:
                continue
            time.sleep(DELAY)
            nuevos = scrape_grupo(session, hijo_id, nombre_display, acumulado,
                                  f"{nombre_display}/{hijo_nombre}")
            if nuevos:
                print(f"    Subgrupo {hijo_nombre}: +{nuevos} nuevos")


def main():
    print("INICIO: Scraper Coto Digital PRO (Constructor.io API)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categorias a scrapear: {len(CATEGORIAS)}")
    print("=" * 55)

    session = requests.Session()
    session.headers.update(HEADERS)

    todos = {}
    resumen = {}

    for i, (nombre_display, group_id) in enumerate(CATEGORIAS, start=1):
        print(f"\n[{i}/{len(CATEGORIAS)}] Categoria: {nombre_display}")
        antes = len(todos)
        scrape_categoria(session, nombre_display, group_id, todos)
        resumen[nombre_display] = len(todos) - antes
        print(f"  {nombre_display}: {resumen[nombre_display]} productos nuevos")
        time.sleep(DELAY)

    productos_lista = list(todos.values())

    if len(productos_lista) < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Solo {len(productos_lista)} productos "
              f"(min esperado: {MIN_PRODUCTS_EXPECTED}) — revisar API/key.")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               f"output_coto_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    con_oferta = sum(1 for p in productos_lista if p["oferta"])
    print("\n" + "=" * 55)
    print(f"Scraping completo — {len(productos_lista)} productos unicos (solo con stock)")
    print(f"Con oferta vigente: {con_oferta} ({con_oferta * 100 // max(len(productos_lista), 1)}%)")
    print(f"Guardado en: {output_file}")
    print("\nResumen por categoria (nuevos aportados):")
    for nombre, count in resumen.items():
        print(f"  {nombre}: {count}")

    return productos_lista, resumen


if __name__ == "__main__":
    main()
