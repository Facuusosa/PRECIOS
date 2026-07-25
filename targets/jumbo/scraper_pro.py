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

Precio regular: Price (del listado de categoria) = precio SIN descuento.
ListPrice VIENE ROTO EN EL 100% DEL CATALOGO (medido 20/07/2026 sobre
10.350 productos: TODOS los que tenian ListPrice>Price daban un ratio
mediano de 82x, hasta 8.264x — un ListPrice nunca actualizado, no un precio
de lista real). A diferencia de Carrefour/Coto/Dia (donde ListPrice SI es
confiable), en Jumbo se ignora del todo como precio regular.

Precio efectivo (oferta real) — fix 24/07/2026: el listado de categoria
(product_search) NO trae el descuento real. Verificado con Puppeteer contra
la ficha renderizada: 5/6 productos de muestra tenian 25-40% off que la API
de categoria no reflejaba (ficha con JS: Kitkat $2.800 -> $1.680, Milka
$12.250 -> $7.962,5, etc.). El precio real se calcula en el browser vía
POST a `/_v/search-promotions` (mismo dominio, sin auth) con hasta 20 SKUs
por request (limite duro del servidor: "SKU limit exceeded, maximum allowed
is 20" — probado con 50). Devuelve 3 grupos de promociones — sgc,
jumbo_prime, generic — y un mismo SKU puede aparecer en más de uno a la vez
(ej. Pan Bimbo: jumbo_prime "2do al 70%" 35% Y generic "Oferta" fixed_price
32% simultaneamente). La ficha real SIEMPRE usa el de mayor prioridad
sgc > jumbo_prime > generic (logica extraida del bundle JS de la tienda,
asset-...c34ee2.min.js — buscar "search-promotions" ahi si esto deja de
andar) — el frontend muestra el precio Jumbo Prime aun a usuarios anonimos,
sin login. Formula verificada 6/6 contra la ficha real (todos los
categoryType: segundo_al, percentual, fixed_price, nxm):
precio = precio_regular * (1 - float(promo["effectiveDiscount"])).
`effectiveDiscount` esta poblado incluso para categoryType "fixed_price"
(ya viene como % normalizado, no hace falta usar el "value" en pesos —
menos preciso: para Pan Bimbo effectiveDiscount 0.32 vs value $5.499 sobre
$8.100 real = 0.3210..., redondeado a 0.32 en el propio feed). El unico
caso sin effectiveDiscount visto (categoryType "Llevando n x", ~0.08% de
la muestra) no permite calcular precio — se deja precio_regular sin tocar,
igual que cualquier SKU sin promocion.

`seller` (PROMO_SELLER abajo) es el `defaultSeller` hardcodeado en el
bundle de la tienda para la cuenta VTEX "jumboargentinaio" — NO es el
sellerId "1" que trae el listado de categoria (probado, devuelve siempre
"item no encontrado"). Si el endpoint empieza a fallar, re-extraer
buscando "defaultSeller" en los bundles JS de jumbo.com.ar (ver metodo:
capturar performance.getEntriesByType('resource') en una ficha de producto
con Puppeteer, filtrar por "search-promotions", bajar los bundles JS
listados y grep "defaultSeller").
"""

import os
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

# Motor de promociones reales — ver docstring del modulo (fix 24/07/2026).
PROMO_URL = "https://www.jumbo.com.ar/_v/search-promotions"
PROMO_SELLER = "jumboargentinaj5202martinez"  # defaultSeller de la cuenta VTEX, no el sellerId "1"
PROMO_BATCH = 20  # limite duro del servidor: 21+ SKUs devuelve 500 "SKU limit exceeded"
PROMO_DELAY = 0.15
PROMO_GRUPOS_PRIORIDAD = ("sgc", "jumbo_prime", "generic")  # orden = el mismo que usa la ficha

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


def fetch_promociones(session, skus):
    """POST batch (<=PROMO_BATCH SKUs) a search-promotions. Devuelve el JSON
    crudo o None — ver docstring del modulo para el porque de este endpoint."""
    for espera in (0, 5, 15):
        if espera:
            print(f"    [WARN] error en search-promotions, reintento en {espera}s")
            time.sleep(espera)
        try:
            r = session.post(PROMO_URL, json={"seller": PROMO_SELLER, "skus": skus}, timeout=20)
        except requests.RequestException:
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code != 429:
            return None
    return None


def descuentos_del_lote(data):
    """sku -> (descuento_fraccion, texto_oferta). Prioridad sgc > jumbo_prime >
    generic: un sku puede tener promo en mas de un grupo a la vez (ej. Pan
    Bimbo con jumbo_prime Y generic simultaneos) y la ficha real siempre
    muestra la de mayor prioridad — ver docstring del modulo."""
    promociones = (data or {}).get("promotions") or {}
    resultado = {}
    for grupo in PROMO_GRUPOS_PRIORIDAD:
        for sku, promo in ((promociones.get(grupo) or {}).get("promotions") or {}).items():
            if sku in resultado:
                continue
            try:
                descuento = float(promo.get("effectiveDiscount"))
            except (TypeError, ValueError):
                continue
            if not (0 < descuento < 1):
                continue
            codigo = promo.get("code") or ""
            if codigo and not any(ch.isdigit() for ch in codigo):
                codigo = f"{codigo} -{round(descuento * 100)}%"
            resultado[sku] = (descuento, codigo)
    return resultado


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
        "oferta": "",  # se completa despues, con el precio real via search-promotions
        "ean": ean,
        "sku": str(item.get("itemId") or ""),
        "sector": categoria_display,
        "subcategoria": subcategoria,
        "imagen": imagen,
        "link": link,
        "fuente": "Jumbo",
        "stock": True,  # sin stock se filtra arriba (server + AvailableQuantity)
        "fecha_scraping": datetime.now().strftime("%Y-%m-%d"),
    }


def scrape_categoria(session, nombre_display, slug, acumulado):
    data = fetch_pagina(session, slug, 1)
    if data is None:
        print(f"  [SKIP] {nombre_display}: API sin respuesta")
        return

    total = data.get("recordsFiltered", 0)
    print(f"  {nombre_display}: {total} disponibles reportados")
    if total > CAP_ALERTA:
        print(f"  [WARN] {nombre_display} cerca del cap de 5.000 por ruta - "
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
            registro = parsear_producto(prod, nombre_display)
            if not registro or registro["ean"] in acumulado:
                continue
            acumulado[registro["ean"]] = registro

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
    resumen = {}

    for i, (nombre_display, slug) in enumerate(CATEGORIAS, start=1):
        print(f"\n[{i}/{len(CATEGORIAS)}] Categoria: {nombre_display}")
        antes = len(todos)
        scrape_categoria(session, nombre_display, slug, todos)
        resumen[nombre_display] = len(todos) - antes
        print(f"  {nombre_display}: {resumen[nombre_display]} productos nuevos")
        time.sleep(DELAY)

    productos_lista = list(todos.values())
    n = len(productos_lista)

    if n < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: Solo {n} productos (min esperado: {MIN_PRODUCTS_EXPECTED}) "
              f"- revisar categorias/slugs (pueden haber cambiado).")
        sys.exit(1)

    skus_a_registros = {}
    for registro in productos_lista:
        sku = registro["sku"]
        if sku:
            skus_a_registros.setdefault(sku, []).append(registro)
    skus_unicos = list(skus_a_registros.keys())

    print("\n" + "=" * 55)
    print(f"Buscando precio real (Jumbo Prime / campanas) para {len(skus_unicos)} SKUs unicos...")
    con_descuento_real = 0
    total_lotes = (len(skus_unicos) + PROMO_BATCH - 1) // PROMO_BATCH
    for indice_lote, i in enumerate(range(0, len(skus_unicos), PROMO_BATCH), start=1):
        lote = skus_unicos[i:i + PROMO_BATCH]
        data = fetch_promociones(session, lote)
        if data is not None:
            for sku, (descuento, codigo) in descuentos_del_lote(data).items():
                for registro in skus_a_registros[sku]:
                    registro["precio"] = round(registro["precio_regular"] * (1 - descuento), 2)
                    registro["oferta"] = codigo
                    con_descuento_real += 1
        if indice_lote % 50 == 0 or indice_lote == total_lotes:
            print(f"  Lote {indice_lote}/{total_lotes}: {con_descuento_real} con precio real hasta ahora")
        time.sleep(PROMO_DELAY)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               f"output_jumbo_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(productos_lista, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo - {n} productos unicos (solo disponibles)")
    print(f"Con precio real con descuento: {con_descuento_real} ({con_descuento_real * 100 // max(n, 1)}%)")
    print(f"Guardado en: {output_file}")
    print("\nResumen por categoria (nuevos aportados):")
    for nombre, count in resumen.items():
        print(f"  {nombre}: {count}")

    return productos_lista, resumen


if __name__ == "__main__":
    main()
