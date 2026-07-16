#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de precios reales contra la web de cada mayorista.
Compara el precio del catalogo vs lo que muestra el sitio hoy.

Uso:
  python scripts/verificar_precios_real.py         # verifica top 10 ABC=A
  python scripts/verificar_precios_real.py 20      # verifica top 20

Requiere credenciales en .env:
  YAGUAR_USERNAME, YAGUAR_PASSWORD
  CARREFOUR_PHPSESSID, CARREFOUR_CF_CLEARANCE
  MAXICONSUMO_EMAIL, MAXICONSUMO_PASSWORD (opcionales — sitio publico)

Genera: data/quality/verificacion_precios_YYYYMMDD_HHMMSS.json
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

CATALOGO_PATH = BASE_DIR / "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"
OUTPUT_DIR = BASE_DIR / "data/quality"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOLERANCIA = 0.10      # diferencia de precio aceptable: 10%
DELAY = 1.5            # segundos entre requests
MIN_VERIFICADOS = 10   # con menos comparaciones efectivas la tasa es ruido, no señal

# Exit codes (pipeline_local.py decide con esto si publica):
#   0 = ok (tasa >= 80% con >= MIN_VERIFICADOS comparados)
#   1 = divergencia real -> NO publicar
#   2 = inconcluso (pocos comparados: red caida, sesion expirada) -> publicar + alertar

try:
    from curl_cffi import requests as cf_requests
    CURL_DISPONIBLE = True
except ImportError:
    import requests as cf_requests
    CURL_DISPONIBLE = False
    print("AVISO: curl_cffi no instalada — usando requests (puede fallar con Cloudflare)")

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Helpers de verificacion por mayorista
# ---------------------------------------------------------------------------

def _verificar_yaguar(link: str, precio_catalogo: float) -> dict:
    """Navega la pagina del producto en Yaguar y extrae el precio."""
    if not link:
        return {"estado": "sin_link"}
    try:
        session = cf_requests.Session(impersonate="safari15_3") if CURL_DISPONIBLE else cf_requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            "Cookie": f"wordpress_logged_in_test=test",
        }
        r = session.get(link, headers=headers, timeout=20)
        if r.status_code != 200:
            return {"estado": "error_http", "codigo": r.status_code}

        soup = BeautifulSoup(r.text, "html.parser")
        # Yaguar fraccionado muestra primero el total del pack x3 y despues el
        # unitario — el catalogo guarda el unitario, comparar contra ese
        precio_elem = soup.select_one(".yaguar-fracc-precio-unitario .woocommerce-Price-amount")
        if not precio_elem:
            precio_elem = soup.select_one(".woocommerce-Price-amount.amount bdi")
        if not precio_elem:
            precio_elem = soup.select_one(".woocommerce-Price-amount.amount")
        if not precio_elem:
            return {"estado": "precio_no_encontrado"}

        texto = precio_elem.get_text(strip=True)
        limpio = re.sub(r"[^\d,.]", "", texto).replace(".", "").replace(",", ".")
        try:
            precio_real = float(limpio)
        except ValueError:
            return {"estado": "precio_no_parseable", "texto": texto}

        diferencia = abs(precio_real - precio_catalogo) / precio_catalogo if precio_catalogo > 0 else 1
        return {
            "estado": "ok" if diferencia <= TOLERANCIA else "diverge",
            "precio_catalogo": precio_catalogo,
            "precio_real": precio_real,
            "diferencia_pct": round(diferencia * 100, 1),
        }
    except Exception as e:
        return {"estado": "excepcion", "error": str(e)[:100]}


def _verificar_maxiconsumo(link: str, precio_catalogo: float) -> dict:
    """Navega la pagina del producto en Maxiconsumo y extrae el precio."""
    if not link:
        return {"estado": "sin_link"}
    try:
        session = cf_requests.Session(impersonate="safari15_3") if CURL_DISPONIBLE else cf_requests.Session()
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"}
        r = session.get(link, headers=headers, timeout=20)
        if r.status_code != 200:
            return {"estado": "error_http", "codigo": r.status_code}

        # NO parsear el DOM: el cache de Magento a veces sirve la ficha sin el precio
        # renderizado, y el primer .price-box puede ser de un producto relacionado del
        # carrusel (falso DIVERGE, caso Canuelas 900cc 01/07/2026). El dataLayer de GTM
        # embebido trae el precio del producto principal server-side y es estable.
        m = re.search(r'"price_unit_package":[\d.]+,"price":([\d.]+)', r.text)
        if not m:
            candidatos = re.findall(r'"price":([\d.]+)', r.text)
            if len(candidatos) != 1:
                return {"estado": "precio_no_encontrado"}
            m_precio = candidatos[0]
        else:
            m_precio = m.group(1)

        try:
            precio_real = float(m_precio)
        except ValueError:
            return {"estado": "precio_no_parseable", "texto": m_precio}

        diferencia = abs(precio_real - precio_catalogo) / precio_catalogo if precio_catalogo > 0 else 1
        return {
            "estado": "ok" if diferencia <= TOLERANCIA else "diverge",
            "precio_catalogo": precio_catalogo,
            "precio_real": precio_real,
            "diferencia_pct": round(diferencia * 100, 1),
        }
    except Exception as e:
        return {"estado": "excepcion", "error": str(e)[:100]}


def _limpiar_precio_carrefour(texto: str) -> float:
    """Copia de limpiar_precio() de targets/maxicarrefour/scraper_pro.py.

    El data-price de Carrefour viene en formato ingles ("10,869.00" / "899.00"):
    coma de miles y punto decimal. La limpieza estilo argentino (punto=miles)
    lo rompe: "899.00" -> 89900 (bug 01/07/2026, 20 falsos DIVERGE).
    """
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
        return float(limpio)
    except ValueError:
        return 0.0


def _verificar_maxicarrefour(ean: str, precio_catalogo: float) -> dict:
    """Verifica precio de MaxiCarrefour buscando por EAN via la API del buscador.

    IMPORTANTE: solo funciona con la sesion PHP viva — PHPSESSID expira por
    inactividad a las pocas horas del scrape (medido 01/07/2026: scrape 16:52 OK,
    a las 19:47 todo el sitio devolvia data-price="private"). Correr esta
    verificacion PEGADA al pipeline, no como script suelto horas despues.
    """
    if not ean:
        return {"estado": "sin_ean"}
    try:
        phpsessid = os.getenv("CARREFOUR_PHPSESSID", "")
        cf_clearance = os.getenv("CARREFOUR_CF_CLEARANCE", "")
        if not phpsessid:
            return {"estado": "sin_cookies"}

        # Receta identica al scraper (impersonate chrome131 + estos headers):
        # otras combinaciones pasan Cloudflare pero el precio viene "private".
        session = cf_requests.Session(impersonate="chrome131") if CURL_DISPONIBLE else cf_requests.Session()
        session.cookies.update({"PHPSESSID": phpsessid, "cf_clearance": cf_clearance})
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Referer": "https://comerciante.carrefour.com.ar/",
        }
        # La API VTEX (/api/catalog_system/...) requiere auth propia y esta muerta
        # para nosotros; este es el mismo endpoint del buscador que usa
        # _carrefour_links_hibrido en actualizar_catalogo.py.
        url = (f"https://comerciante.carrefour.com.ar/products?currentUrl=search/{ean}"
               f"&filters=&orderBy=default&currentPage=1&itemsPerPage=12&method=productsList")
        r = session.get(url, headers=headers, timeout=20)

        if r.status_code == 401 or "/login" in str(r.url):
            return {"estado": "cookies_expiradas"}
        if r.status_code != 200:
            return {"estado": "error_http", "codigo": r.status_code}

        soup = BeautifulSoup(r.text, "html.parser")
        item = soup.find(class_="item_card") or soup.find(class_="item_card_public")
        if not item:
            return {"estado": "producto_no_encontrado"}

        # Mismo parsing que el scraper: number_price (texto) o data-price del boton
        precio_texto = ""
        price_div = item.find(class_="number_price")
        if price_div:
            precio_texto = price_div.get_text(strip=True)
        if not precio_texto:
            cart = item.find(class_="cart_button")
            if cart:
                precio_texto = cart.get("data-price", "")

        if precio_texto == "private":
            return {"estado": "sesion_expirada"}
        precio_real = _limpiar_precio_carrefour(precio_texto)
        if precio_real <= 0:
            return {"estado": "precio_no_parseable", "texto": precio_texto[:40]}

        diferencia = abs(precio_real - precio_catalogo) / precio_catalogo if precio_catalogo > 0 else 1
        return {
            "estado": "ok" if diferencia <= TOLERANCIA else "diverge",
            "precio_catalogo": precio_catalogo,
            "precio_real": precio_real,
            "diferencia_pct": round(diferencia * 100, 1),
        }
    except Exception as e:
        return {"estado": "excepcion", "error": str(e)[:100]}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"VERIFICADOR DE PRECIOS REALES — top {n} productos ABC=A")
    print("=" * 55)

    with open(CATALOGO_PATH, encoding="utf-8") as f:
        catalogo = json.load(f)

    # Seleccionar top N productos ABC=A con 2+ fuentes MAYORISTAS de precio.
    # coto/carrefour (cadenas) no entran al gate: son referencia gondola,
    # no precio de compra
    _MAYORISTAS = ("yaguar", "maxicarrefour", "maxiconsumo")
    def _n_may(p):
        return sum(1 for k in _MAYORISTAS if p.get("precios", {}).get(k, 0) > 0)
    candidatos = [p for p in catalogo if p.get("abc") == "A" and _n_may(p) >= 2]
    # Ordenar por cantidad de fuentes (más fuentes primero)
    candidatos.sort(key=_n_may, reverse=True)
    muestra = candidatos[:n]

    if not muestra:
        print("No se encontraron productos ABC=A con 2+ precios.")
        sys.exit(1)

    resultados = []
    ok_total = 0
    verificados_total = 0

    for i, prod in enumerate(muestra, 1):
        nombre = prod.get("nombre_display", "?")
        ean = prod.get("ean", "")
        fuentes = prod.get("fuentes", {})
        precios = prod.get("precios", {})

        print(f"\n[{i}/{len(muestra)}] {nombre[:55]}")

        resultado_prod = {"nombre": nombre, "ean": ean, "fuentes": {}}

        # Yaguar
        if precios.get("yaguar", 0) > 0:
            link_yag = fuentes.get("yaguar", {}).get("link", "")
            r = _verificar_yaguar(link_yag, precios["yaguar"])
            resultado_prod["fuentes"]["yaguar"] = r
            estado = r["estado"]
            if estado == "ok":
                ok_total += 1
                verificados_total += 1
                print(f"  Yaguar:       OK ${r['precio_real']:,.0f} (cat: ${precios['yaguar']:,.0f})")
            elif estado == "diverge":
                verificados_total += 1
                print(f"  Yaguar:       DIVERGE ${r['precio_real']:,.0f} vs ${precios['yaguar']:,.0f} ({r['diferencia_pct']}%)")
            else:
                print(f"  Yaguar:       {estado}")
            time.sleep(DELAY)

        # Maxiconsumo
        if precios.get("maxiconsumo", 0) > 0:
            link_mco = fuentes.get("maxiconsumo", {}).get("link", "")
            r = _verificar_maxiconsumo(link_mco, precios["maxiconsumo"])
            resultado_prod["fuentes"]["maxiconsumo"] = r
            estado = r["estado"]
            if estado == "ok":
                ok_total += 1
                verificados_total += 1
                print(f"  Maxiconsumo:  OK ${r['precio_real']:,.0f} (cat: ${precios['maxiconsumo']:,.0f})")
            elif estado == "diverge":
                verificados_total += 1
                print(f"  Maxiconsumo:  DIVERGE ${r['precio_real']:,.0f} vs ${precios['maxiconsumo']:,.0f} ({r['diferencia_pct']}%)")
            else:
                print(f"  Maxiconsumo:  {estado}")
            time.sleep(DELAY)

        # MaxiCarrefour
        if precios.get("maxicarrefour", 0) > 0:
            r = _verificar_maxicarrefour(ean, precios["maxicarrefour"])
            resultado_prod["fuentes"]["maxicarrefour"] = r
            estado = r["estado"]
            if estado == "ok":
                ok_total += 1
                verificados_total += 1
                print(f"  MaxiCarrefour:OK ${r['precio_real']:,.0f} (cat: ${precios['maxicarrefour']:,.0f})")
            elif estado == "diverge":
                verificados_total += 1
                print(f"  MaxiCarrefour:DIVERGE ${r['precio_real']:,.0f} vs ${precios['maxicarrefour']:,.0f} ({r['diferencia_pct']}%)")
            else:
                print(f"  MaxiCarrefour:{estado}")
            time.sleep(DELAY)

        resultados.append(resultado_prod)

    # Resumen
    tasa = ok_total / verificados_total * 100 if verificados_total > 0 else 0
    print(f"\n{'=' * 55}")
    print(f"RESUMEN: {ok_total}/{verificados_total} precios correctos ({tasa:.1f}%)")

    # Desglose de lo que NO se pudo comparar — sin esto, una fuente entera puede
    # quedar ciega en silencio (01/07/2026: 20/20 'excepcion' en MCF y el resumen
    # igual decia 97.5% OK). Un estado raro repetido = esa fuente no se verifico.
    no_verificados = {}
    for rp in resultados:
        for fuente, res in rp["fuentes"].items():
            if res.get("estado") not in ("ok", "diverge"):
                clave = f"{fuente}:{res.get('estado')}"
                no_verificados[clave] = no_verificados.get(clave, 0) + 1
    if no_verificados:
        print("NO VERIFICADOS (no cuentan para la tasa):")
        for clave, cant in sorted(no_verificados.items(), key=lambda x: -x[1]):
            print(f"  {clave}: {cant}")

    # Fuente entera ciega -> inconcluso. La tasa global no lo ve: el 15/07/2026
    # los 20 checks MCF dieron sesion_expirada y el gate salio exit 0 con 97.4%
    # calculado solo sobre Yaguar+MCO — MCF publico sin red de seguridad.
    fuentes_ciegas = []
    for fuente in _MAYORISTAS:
        intentos = sum(1 for rp in resultados if fuente in rp["fuentes"])
        efectivos = sum(1 for rp in resultados
                        if rp["fuentes"].get(fuente, {}).get("estado") in ("ok", "diverge"))
        if intentos >= 5 and efectivos == 0:
            fuentes_ciegas.append(fuente)
            print(f"FUENTE SIN VERIFICAR: {fuente} ({intentos} intentos, 0 comparaciones efectivas)")

    if verificados_total < MIN_VERIFICADOS:
        print(f"INCONCLUSO: solo {verificados_total} precios comparados (minimo: {MIN_VERIFICADOS}) — "
              "no hay evidencia suficiente para aprobar ni bloquear.")
    elif tasa < 80:
        print("ALERTA: Mas del 20% de precios divergen — el catalogo puede estar desactualizado.")
    elif fuentes_ciegas:
        print(f"INCONCLUSO: fuente(s) sin verificar: {', '.join(fuentes_ciegas)} -- el resto dentro del rango.")
    else:
        print("OK: Precios dentro del rango esperado.")

    # Guardar JSON
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"verificacion_precios_{ts}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "fecha": ts,
            "muestra": n,
            "tasa_ok_pct": round(tasa, 1),
            "ok": ok_total,
            "verificados": verificados_total,
            "fuentes_sin_verificar": fuentes_ciegas,
            "resultados": resultados,
        }, f, ensure_ascii=False, indent=2)
    print(f"Reporte guardado: {out_path}")

    # Prioridad: divergencia real (1) > inconcluso (2) > ok (0)
    if verificados_total >= MIN_VERIFICADOS and tasa < 80:
        sys.exit(1)
    if verificados_total < MIN_VERIFICADOS or fuentes_ciegas:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
