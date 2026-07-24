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

import os, sys, json, re, time, glob, threading
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(TARGETS_DIR, "cache_enriquecimiento.json")

WORKERS   = 6     # 6 workers — curl_cffi impersonation aguanta mas sin ser detectado
DELAY     = 0.1   # delay por worker — 6 workers x 0.1s = ~0.017s efectivo global
SAVE_EACH = 200
IMPERSONATE = "safari15_3"

PRECIO_MIN     = 100
PRECIO_MAX     = 500_000
PRECIO_TTL_DIAS = 7   # precios se re-consultan si tienen >7 dias; EANs son permanentes

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Session persistente por thread — evita TLS handshake por cada producto
_thread_local = threading.local()

def _get_session():
    if not hasattr(_thread_local, "session"):
        _thread_local.session = crear_sesion()
    return _thread_local.session


def encontrar_archivo_input(path_arg=None):
    if path_arg and os.path.exists(path_arg):
        return path_arg
    patron = os.path.join(TARGETS_DIR, "output_maxiconsumo*.json")
    archivos = sorted(glob.glob(patron), key=os.path.getmtime, reverse=True)
    if archivos:
        return archivos[0]
    generico = os.path.join(TARGETS_DIR, "output_maxiconsumo.json")
    if os.path.exists(generico):
        return generico
    return None


def crear_sesion():
    session = curl_requests.Session()
    session.headers.update(HEADERS)
    return session


def extraer_ean_detalle(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                data = data[0] if data else {}
            for field in ("gtin13", "gtin", "gtin8", "gtin12"):
                val = str(data.get(field, "")).strip()
                if val and val.isdigit() and 8 <= len(val) <= 14:
                    return val
        except Exception:
            pass
    m = re.search(r'"(?:sku|ean|barcode|gtin)"\s*:\s*"(\d{8,14})"', html, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def _extraer_precio_bulto_cerrado(soup) -> float:
    # Estructura real de Maxiconsumo:
    # <span class="price-label">Precio unitario por bulto cerrado</span>
    # <span class="price-wrapper price-including-tax" data-label="con iva">
    #   <span class="price">$\xa02.149,89</span>
    # </span>
    label = soup.find("span", class_="price-label",
                      string=re.compile(r"bulto cerrado", re.IGNORECASE))
    if label:
        container = label.parent  # span.price-container
        wrapper = container.find("span", class_="price-including-tax") if container else None
        price_span = wrapper.find("span", class_="price") if wrapper else None
        if price_span:
            # Formato argentino: "$\xa02.149,89" -> 2149.89
            txt = re.sub(r"[^\d,]", "", price_span.get_text(strip=True))
            txt = txt.replace(",", ".")
            try:
                return float(txt)
            except ValueError:
                pass
    return 0.0


def _get_con_guardian(session, url, timeout_total=25):
    """session.get() con limite duro de tiempo real via thread daemon.

    Verificado 22/07/2026 (mismo bug que targets/maxiconsumo/scraper_pro.py): una
    conexion colgada de Cloudflare puede no disparar nunca el timeout de curl_cffi,
    trabando el ThreadPoolExecutor entero (su __exit__ espera a TODOS los futuros).
    join(timeout_total) corta la espera pase lo que pase; el thread daemon abandonado
    no bloquea el cierre del proceso.
    """
    resultado = {}

    def _trabajo():
        try:
            resultado["r"] = session.get(url, impersonate=IMPERSONATE, timeout=20)
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


def extraer_precio_detalle(session, url: str) -> tuple[float, str]:
    try:
        r = _get_con_guardian(session, url)
        if r.status_code != 200:
            return 0.0, ""
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        precio = 0.0

        # Prioridad 1: precio de bulto cerrado (correcto para productos multi-unidad)
        precio = _extraer_precio_bulto_cerrado(soup)

        # Prioridad 2: meta tag (correcto para productos de unidad individual)
        if not precio:
            meta = soup.find("meta", property="product:price:amount")
            if meta and meta.get("content"):
                try:
                    precio = float(meta["content"])
                except ValueError:
                    pass

        # Prioridad 3: JSON de Magento con finalPrice
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


def _procesar_uno(idx: int, producto: dict) -> tuple[int, float, str]:
    session = _get_session()  # reusar session del thread — sin TLS handshake por producto
    url = producto.get("link", "")
    if not url:
        return idx, 0.0, ""
    precio, ean = extraer_precio_detalle(session, url)
    time.sleep(DELAY)
    return idx, precio, ean


def _precio_vigente(entrada: dict) -> bool:
    """El precio del cache es usable solo si tiene menos de PRECIO_TTL_DIAS dias."""
    fecha_str = entrada.get("fecha_precio", "")
    if not fecha_str:
        return False  # sin fecha = precio sin TTL del cache viejo -> forzar re-consulta
    try:
        fecha = date.fromisoformat(fecha_str)
        return (date.today() - fecha).days < PRECIO_TTL_DIAS
    except ValueError:
        return False


def cargar_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


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

    cache = cargar_cache()
    cache_hits = 0
    precios_expirados = 0
    for p in productos:
        sku = p.get("sku", "")
        if sku and sku in cache:
            entrada = cache[sku]
            # EAN: permanente, no expira nunca
            if not p.get("ean") and entrada.get("ean"):
                p["ean"] = entrada["ean"]
            # Precio: solo si tiene fecha y es reciente
            precio_cache = entrada.get("precio", 0)
            if not p.get("precio") and PRECIO_MIN <= precio_cache <= PRECIO_MAX:
                if _precio_vigente(entrada):
                    p["precio"] = precio_cache
                    cache_hits += 1
                else:
                    precios_expirados += 1  # sera re-consultado
    print(f"Cache: {len(cache)} SKUs | precios vigentes aplicados: {cache_hits} | expirados (re-consultar): {precios_expirados}", flush=True)

    sin_precio = [i for i, p in enumerate(productos) if not p.get("precio") or p["precio"] == 0]
    sin_ean = [i for i, p in enumerate(productos) if not p.get("ean")]
    # Procesar todos los que faltan EAN (tengan precio o no) para maximizar cobertura de matching
    a_procesar = sorted(set(sin_ean))
    print(f"Sin precio: {len(sin_precio)} (cache ahorro {cache_hits})", flush=True)
    print(f"Sin EAN:    {len(sin_ean)}", flush=True)
    print(f"A visitar:  {len(a_procesar)} paginas de detalle ({WORKERS} workers)", flush=True)
    secs = len(a_procesar) * DELAY / WORKERS
    print(f"Tiempo estimado: ~{secs/60:.1f} minutos", flush=True)
    print(flush=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_salida = os.path.join(TARGETS_DIR, f"output_maxiconsumo_{ts}.json")

    lock = threading.Lock()
    contador = 0
    precios_actualizados = 0
    eans_encontrados = 0
    errores = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futuros = {
            executor.submit(_procesar_uno, idx, productos[idx]): idx
            for idx in a_procesar
        }
        for fut in as_completed(futuros):
            try:
                idx, precio, ean = fut.result()
            except Exception:
                with lock:
                    errores += 1
                    contador += 1
                continue

            p = productos[idx]
            with lock:
                contador += 1
                if PRECIO_MIN <= precio <= PRECIO_MAX:
                    productos[idx]["precio"] = precio
                    precios_actualizados += 1
                if ean:
                    productos[idx]["ean"] = ean
                    eans_encontrados += 1
                if not precio and not ean:
                    errores += 1

                sku = p.get("sku", "")
                if sku:
                    entrada_vieja = cache.get(sku, {})
                    precio_valido = precio if PRECIO_MIN <= precio <= PRECIO_MAX else 0
                    cache[sku] = {
                        # Precio nuevo con fecha de hoy; si no hubo precio, preservar el viejo solo si sigue vigente
                        "precio": precio_valido or (entrada_vieja.get("precio", 0) if _precio_vigente(entrada_vieja) else 0),
                        "fecha_precio": date.today().isoformat() if precio_valido else entrada_vieja.get("fecha_precio", ""),
                        # EAN permanente: tomar el nuevo si existe, sino preservar el viejo
                        "ean": ean or entrada_vieja.get("ean", ""),
                    }

                if contador <= 5 or contador % 200 == 0:
                    print(f"  [{contador}/{len(a_procesar)}] precio=${precio:.0f} ean={ean or '-'} - {p['nombre'][:40]}", flush=True)

                if contador % SAVE_EACH == 0:
                    _guardar(productos, data, archivo_salida)
                    guardar_cache(cache)
                    print(f"  [CHECKPOINT] {contador}/{len(a_procesar)} | precios+{precios_actualizados} | EANs+{eans_encontrados}", flush=True)

    _guardar(productos, data, archivo_salida)
    guardar_cache(cache)

    print(flush=True)
    print("=" * 50, flush=True)
    print("TERMINADO", flush=True)
    print(f"Precios actualizados: {precios_actualizados} / {len(sin_precio)}", flush=True)
    print(f"EANs encontrados:     {eans_encontrados} / {len(sin_ean)} ({eans_encontrados*100//max(len(sin_ean),1)}%)", flush=True)
    print(f"Sin datos aun:        {errores}", flush=True)
    con_precio_final = sum(1 for p in productos if p.get("precio") and p["precio"] > 0)
    con_ean_final = sum(1 for p in productos if p.get("ean"))
    print(f"Total con precio: {con_precio_final} / {len(productos)}", flush=True)
    print(f"Total con EAN:    {con_ean_final} / {len(productos)} ({con_ean_final*100//max(len(productos),1)}%)", flush=True)
    print(f"Guardado en: {archivo_salida}", flush=True)


def _guardar(productos: list, data_original, ruta: str) -> None:
    out = productos if isinstance(data_original, list) else {**data_original, "productos": productos}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
