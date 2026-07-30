#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER NINI MAYORISTA - VERSION PRO

CUENTA PRESTADA POR UN TERCERO (no es de Facu) -- ver .claude/rules/02-scrapers.md.
Este scraper es SOLO LECTURA por diseño: nunca modifica cantidades, nunca confirma
ni anula pedidos. El sitio corre sobre un backend Node.js con una API RPC generica
(POST /nodejs/{daoName}/{method}) que tambien expone metodos de escritura reales
(Nini.Models.Order.Confirm/Reserve/destroy) -- _METODOS_PERMITIDOS es un whitelist
duro: cualquier combinacion daoName/method fuera de esa lista aborta antes de armar
el request, para que un typo o un cambio futuro no termine llamando algo destructivo.

Arquitectura (investigado en vivo 29/07/2026):
- El sitio es una SPA que NO expone URLs profundas (?nini.controllers.listadoDeProductos
  redirige al login si se navega directo -- el estado vive en la sesion del servidor,
  igual que el form MAXI PEDIDO de MaxiCarrefour).
- El flujo minimo para que el servidor resuelva un "pedido en curso" (requisito para
  poder pedir precios) es el mismo que hace un humano: login -> Creacion de pedido ->
  Continuar -> Seguir comprando. Replicado 1:1 con Playwright, sin tocar mas botones.
- Una vez ahi, los datos reales viven detras de una API JSON (no hace falta parsear
  HTML): onlineDeparmentDao/findFacets (8 departamentos), onlineSectorDao/findAll
  (135 sectores, id con prefijo de departamento: 210040 = depto 210 + sector 040),
  onlineProductDao/findAllWithOrder (productos con precio, paginado por
  offsetProducts/limit=50, ya filtrado a onlyStock=true por el propio sitio).
- El id del "pedido en curso" (currentOrder.id) es obligatorio en cada pedido de
  productos pero NO esta en ningun global de JS accesible -- se captura interceptando
  el primer request real que dispara el propio sitio al llegar al listado (Playwright
  page.on("request"), sin JS inyectado). Nunca se hardcodea: si el dueño real de la
  cuenta confirma/anula su pedido, ese id puede cambiar de un dia para el otro.
"""

import os
import re
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_URL = "http://ecommerce.nini.com.ar:8081/ventas.online/?nini.controllers.listadoDeProductos"

NINI_USERNAME = os.getenv("NINI_USERNAME", "")
NINI_PASSWORD = os.getenv("NINI_PASSWORD", "")

SELLER_ID = "989"
ZONE = "10000007"
LIMIT = 50
PRECIO_MIN = 20
PRECIO_MAX = 500_000
MIN_PRODUCTS_EXPECTED = 3500  # calibrado sobre la primera corrida real (29/07/2026): 7.248 productos

# Whitelist duro de operaciones permitidas -- SOLO lectura. Ver docstring del modulo.
_METODOS_PERMITIDOS = {
    ("onlineDeparmentDao", "findFacets"),
    ("onlineSectorDao", "findAll"),
    ("onlineProductDao", "findAllWithOrder"),
}


def _fetch_dao(page, dao_name: str, method: str, filtros: dict) -> str:
    """POST a la API interna reusando la sesion ya logueada del `page`.
    Aborta antes de armar el request si (dao_name, method) no esta en el
    whitelist de solo-lectura -- ver _METODOS_PERMITIDOS."""
    if (dao_name, method) not in _METODOS_PERMITIDOS:
        raise ValueError(
            f"Metodo no permitido por el guardrail de seguridad: {dao_name}/{method} "
            "(cuenta prestada -- este scraper es SOLO LECTURA)"
        )
    resultado = page.evaluate(
        r"""
        async ({daoName, method, filtros, userName, sellerId, zone}) => {
            const p = new URLSearchParams();
            p.set('daoName', daoName);
            p.set('method', method);
            for (const [k, v] of Object.entries(filtros)) p.set(k, v);
            p.set('params[sellerId]', sellerId);
            p.set('params[isClient]', 'true');
            p.set('params[userName]', userName);
            p.set('params[zone]', zone);
            p.set('params[quotaSellerId]', userName);
            const r = await fetch('/nodejs/' + daoName + '/' + method, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                body: p.toString()
            });
            // El backend responde en ISO-8859-1 sin declararlo en el Content-Type --
            // r.text() asume UTF-8 y corrompe ñ/é/á en replacement chars (bug real
            // detectado 29/07/2026: "CAÑUELAS" salia como "CA�UELAS"). Se decodifica
            // el charset real del header si esta, sino se asume iso-8859-1 (confirmado
            // con el error 502 del gateway, que declara ese charset por defecto).
            const buf = await r.arrayBuffer();
            const ct = r.headers.get('content-type') || '';
            const match = ct.match(/charset=([\w-]+)/i);
            const charset = match ? match[1] : 'iso-8859-1';
            return new TextDecoder(charset).decode(buf);
        }
        """,
        {
            "daoName": dao_name, "method": method, "filtros": filtros,
            "userName": NINI_USERNAME, "sellerId": SELLER_ID, "zone": ZONE,
        },
    )
    return resultado


def login_y_resolver_pedido(page) -> str:
    """Replica el flujo exacto validado a mano: login -> Creacion de pedido ->
    Continuar -> Seguir comprando. Nunca toca cantidad de producto, Confirmar
    Pedido, Anular Pedido ni Guardar en Borrador -- esos botones existen en esta
    cuenta prestada y este scraper jamas hace click ahi.

    Devuelve el id del pedido en curso (currentOrder.id), capturado interceptando
    el primer request real de findAllWithOrder que dispara el propio sitio."""
    print("Iniciando sesion...")
    page.goto(BASE_URL, timeout=30000, wait_until="domcontentloaded")
    page.wait_for_selector("#userName", timeout=15000)
    page.fill("#userName", NINI_USERNAME)
    page.fill("#password", NINI_PASSWORD)

    order_id = {}

    def _on_request(request):
        if "findAllWithOrder" in request.url and "id" not in order_id:
            post_data = request.post_data or ""
            m = re.search(r"currentOrder%5D%5Bid%5D=(\d+)", post_data)
            if m:
                order_id["id"] = m.group(1)

    page.on("request", _on_request)

    page.click("#login")
    page.wait_for_selector("#crearPedido", timeout=15000)
    print("Login exitoso")

    page.click("#crearPedido")
    page.wait_for_selector("#next", timeout=15000)
    page.click("#next")
    page.wait_for_selector("#goToHome", timeout=15000)
    page.click("#goToHome")
    page.wait_for_timeout(2500)

    if "id" not in order_id:
        # El listado por defecto a veces no dispara findAllWithOrder solo -- forzar
        # un click de navegacion real (solo lectura) para que el sitio lo dispare.
        try:
            page.locator("li[class*='nini_models_departament_'] a").first.click(timeout=5000)
            page.wait_for_timeout(2000)
        except Exception:
            pass

    if "id" not in order_id:
        raise RuntimeError(
            "No se pudo capturar el id del pedido en curso (currentOrder.id) -- "
            "abortando sin tocar nada mas."
        )
    print(f"Pedido en curso resuelto: {order_id['id']}")
    return order_id["id"]


def obtener_departamentos(page) -> list:
    txt = _fetch_dao(page, "onlineDeparmentDao", "findFacets", {})
    return json.loads(txt)


def obtener_sectores(page) -> list:
    txt = _fetch_dao(page, "onlineSectorDao", "findAll", {})
    return json.loads(txt)


def _limpiar_precio(valor) -> float:
    try:
        precio = float(valor)
    except (TypeError, ValueError):
        return 0.0
    if not (PRECIO_MIN <= precio <= PRECIO_MAX):
        return 0.0
    return precio


def obtener_productos_sector(page, order_id: str, departamento_id: str, sector_id: str,
                              categoria_nombre: str) -> list:
    """Pagina onlineProductDao/findAllWithOrder para un sector hasta cubrir totalProducts."""
    productos = []
    offset = 0
    total = None
    while total is None or offset < total:
        filtros = {
            "params[filter][where]": "",
            "params[filter][staticWhere]": "",
            "params[filter][departamentId]": departamento_id,
            "params[filter][sectorId]": sector_id,
            "params[filter][lineId]": "null",
            "params[filter][sublineId]": "null",
            "params[filter][catalogId]": "null",
            "params[filter][orderId]": "null",
            "params[filter][onlypaquete]": "true",
            "params[filter][onlyrelated]": "null",
            "params[filter][trademarkId]": "null",
            "params[filter][supplierId]": "null",
            "params[filter][presentation]": "null",
            "params[filter][selectedPopular]": "null",
            "params[filter][showMostPopular]": "false",
            "params[filter][currentOrder][id]": order_id,
            "params[filter][articlesInCatalog]": "false",
            "params[filter][offsetPromotions]": "0",
            "params[filter][offsetProducts]": str(offset),
            "params[filter][magazinePage]": "null",
            "params[filter][withStock]": "true",
            "params[filter][advertisingProductId]": "null",
            "params[filter][buyArticles][]": "-1",
            "params[filter][limit]": str(LIMIT),
        }
        txt = _fetch_dao(page, "onlineProductDao", "findAllWithOrder", filtros)
        try:
            data = json.loads(txt)
        except json.JSONDecodeError:
            print(f"    AVISO: respuesta invalida en sector {sector_id} offset {offset} -- corto sector")
            break
        if not data:
            break
        if total is None:
            total = int(data[0].get("totalProducts", len(data)) or len(data))
        for p in data:
            precio = _limpiar_precio(p.get("price", 0))
            if precio <= 0:
                continue
            nombre = f"{p.get('smallDescription', '').strip()} {p.get('presentationOrder', '').strip()}".strip()
            sku = str(p.get("id", "")).strip()
            if not nombre or not sku:
                continue
            productos.append({
                "nombre": nombre,
                "sku": sku,
                "precio": precio,
                "marca": p.get("trademark", "") or "",
                "stock": p.get("stock", ""),
                "categoria": categoria_nombre,
                "fuente": "Nini",
                "fecha": datetime.now().strftime("%Y-%m-%d"),
            })
        offset += LIMIT
        time.sleep(0.2)
    return productos


def main():
    print("Scraper Nini Mayorista PRO")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    if not NINI_USERNAME or not NINI_PASSWORD:
        print("ERROR: NINI_USERNAME y NINI_PASSWORD son obligatorias en .env")
        sys.exit(1)

    todos = []
    vistos = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        try:
            order_id = login_y_resolver_pedido(page)
        except Exception as e:
            print(f"ERROR fatal en login/resolucion de pedido: {e}")
            browser.close()
            sys.exit(1)

        departamentos = obtener_departamentos(page)
        sectores = obtener_sectores(page)
        print(f"Departamentos: {len(departamentos)} | Sectores: {len(sectores)}")
        print("=" * 55)

        depto_por_id = {d["id"]: d["description"] for d in departamentos}

        for idx, sector in enumerate(sectores, start=1):
            sector_id = sector["id"]
            depto_id = sector_id[:3]
            categoria = depto_por_id.get(depto_id, depto_id)
            nuevos = obtener_productos_sector(page, order_id, depto_id, sector_id, categoria)
            agregados = 0
            for prod in nuevos:
                if prod["sku"] in vistos:
                    continue
                vistos.add(prod["sku"])
                todos.append(prod)
                agregados += 1
            if idx % 10 == 0 or idx == len(sectores):
                print(f"[{idx}/{len(sectores)}] {sector['description']}: {agregados} nuevos ({len(todos)} acumulados)")

        browser.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(BASE_DIR, "targets", "nini", f"output_nini_{timestamp}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 55)
    print(f"Scraping completo -- {len(todos)} productos unicos")
    print(f"Guardado en: {output_file}")

    if len(todos) < MIN_PRODUCTS_EXPECTED:
        print(f"ERROR: {len(todos)} productos < minimo esperado {MIN_PRODUCTS_EXPECTED}")
        sys.exit(1)

    return todos


if __name__ == "__main__":
    main()
