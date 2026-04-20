#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENRIQUECEDOR DE PRECIOS - MAXICONSUMO
Visita las paginas de detalle de productos sin precio y extrae el precio
desde <meta property="product:price:amount" content="..."/>

Uso:
    python enriquecer_precios.py [archivo_input.json]

Si no se pasa archivo, usa el mas reciente output_maxiconsumo*.json
"""

import os, sys, json, re, time, glob
from datetime import datetime
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS_DIR = os.path.dirname(os.path.abspath(__file__))

DELAY = 0.35          # segundos entre requests
SAVE_EACH = 200       # guardar progreso cada N productos
IMPERSONATE = "safari15_3"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def encontrar_archivo_input(path_arg=None):
    if path_arg and os.path.exists(path_arg):
        return path_arg
    # Buscar el mas reciente output_maxiconsumo*.json en este directorio
    patron = os.path.join(TARGETS_DIR, "output_maxiconsumo*.json")
    archivos = sorted(glob.glob(patron), key=os.path.getmtime, reverse=True)
    if archivos:
        return archivos[0]
    # Tambien el nombre generico
    generico = os.path.join(TARGETS_DIR, "output_maxiconsumo.json")
    if os.path.exists(generico):
        return generico
    return None


def crear_sesion():
    session = curl_requests.Session()
    session.headers.update(HEADERS)
    return session


def extraer_ean_detalle(html: str) -> str:
    """Extrae EAN/GTIN desde JSON-LD o scripts de Magento en la página de detalle."""
    soup = BeautifulSoup(html, "html.parser")
    # JSON-LD (Schema.org Product)
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                data = data[0] if data else {}
            for field in ("gtin13", "gtin", "gtin8", "gtin12"):
                val = str(data.get(field, "")).strip()
                if val and val.isdigit() and len(val) in (8, 12, 13):
                    return val
        except Exception:
            pass
    # Magento init — busca secuencias de 8-13 dígitos en contexto de sku/ean/barcode
    m = re.search(r'"(?:sku|ean|barcode|gtin)"\s*:\s*"(\d{8,13})"', html, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def extraer_precio_detalle(session, url):
    """Visita la pagina de detalle y extrae precio y EAN del meta OG tag / JSON-LD."""
    try:
        r = session.get(url, impersonate=IMPERSONATE, timeout=20)
        if r.status_code != 200:
            return 0.0, ""
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        precio = 0.0
        meta = soup.find("meta", property="product:price:amount")
        if meta and meta.get("content"):
            try:
                precio = float(meta["content"])
            except ValueError:
                pass
        if not precio:
            for s in soup.find_all("script", type="text/x-magento-init"):
                txt = s.get_text()
                if "finalPrice" in txt:
                    m = re.search(r'"finalPrice"\s*:\s*\{"amount"\s*:\s*([\d.]+)', txt)
                    if m:
                        precio = float(m.group(1))
                        break
        ean = extraer_ean_detalle(html)
        return precio, ean
    except Exception:
        return 0.0, ""


def main():
    archivo = encontrar_archivo_input(sys.argv[1] if len(sys.argv) > 1 else None)
    if not archivo:
        print("ERROR: No se encontro archivo de input. Pasa la ruta como argumento.")
        sys.exit(1)

    print(f"Input: {archivo}", flush=True)
    with open(archivo, encoding="utf-8") as f:
        data = json.load(f)

    productos = data if isinstance(data, list) else data.get("productos", [])
    print(f"Total productos: {len(productos)}", flush=True)

    sin_precio = [i for i, p in enumerate(productos) if not p.get("precio") or p["precio"] == 0]
    sin_ean = [i for i, p in enumerate(productos) if not p.get("ean")]
    # Procesar: productos sin precio (obligatorio) + sin EAN (enriquecimiento)
    a_procesar = sorted(set(sin_precio) | set(sin_ean))
    print(f"Sin precio: {len(sin_precio)}", flush=True)
    print(f"Sin EAN:    {len(sin_ean)}", flush=True)
    print(f"A visitar:  {len(a_procesar)} páginas de detalle", flush=True)
    print(f"Tiempo estimado: ~{len(a_procesar) * DELAY / 60:.1f} minutos", flush=True)
    print(flush=True)

    session = crear_sesion()
    precios_actualizados = 0
    eans_encontrados = 0
    errores = 0

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_salida = os.path.join(TARGETS_DIR, f"output_maxiconsumo_{ts}.json")

    for contador, idx in enumerate(a_procesar, 1):
        p = productos[idx]
        url = p.get("link", "")
        if not url:
            errores += 1
            continue

        precio, ean = extraer_precio_detalle(session, url)
        necesitaba_precio = not p.get("precio") or p["precio"] == 0
        necesitaba_ean = not p.get("ean")

        if necesitaba_precio and precio > 0:
            productos[idx]["precio"] = precio
            precios_actualizados += 1
        if necesitaba_ean and ean:
            productos[idx]["ean"] = ean
            eans_encontrados += 1

        if contador <= 5 or contador % 200 == 0:
            print(f"  [{contador}/{len(a_procesar)}] precio=${precio:.0f} ean={ean or '-'} - {p['nombre'][:40]}", flush=True)

        if not precio and not ean:
            errores += 1

        if contador % SAVE_EACH == 0:
            _guardar(productos, data, archivo_salida)
            print(f"  [CHECKPOINT] {contador}/{len(a_procesar)} | precios+{precios_actualizados} | EANs+{eans_encontrados}", flush=True)

        time.sleep(DELAY)

    _guardar(productos, data, archivo_salida)

    print(flush=True)
    print("=" * 50, flush=True)
    print(f"TERMINADO", flush=True)
    print(f"Precios actualizados: {precios_actualizados} / {len(sin_precio)}", flush=True)
    print(f"EANs encontrados:     {eans_encontrados} / {len(sin_ean)} ({eans_encontrados*100//max(len(sin_ean),1)}%)", flush=True)
    print(f"Sin datos aun:        {errores}", flush=True)
    con_precio_final = sum(1 for p in productos if p.get("precio") and p["precio"] > 0)
    con_ean_final = sum(1 for p in productos if p.get("ean"))
    print(f"Total con precio: {con_precio_final} / {len(productos)}", flush=True)
    print(f"Total con EAN:    {con_ean_final} / {len(productos)} ({con_ean_final*100//max(len(productos),1)}%)", flush=True)
    print(f"Guardado en: {archivo_salida}", flush=True)


def _guardar(productos, data_original, ruta):
    if isinstance(data_original, list):
        out = productos
    else:
        data_original["productos"] = productos
        out = data_original
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
