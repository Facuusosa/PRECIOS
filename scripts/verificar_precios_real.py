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

TOLERANCIA = 0.10  # diferencia de precio aceptable: 10%
DELAY = 1.5        # segundos entre requests

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

        soup = BeautifulSoup(r.text, "html.parser")
        # Precio Magento
        precio_elem = (
            soup.select_one(".price-box .price") or
            soup.select_one("[data-price-type='finalPrice'] .price") or
            soup.select_one(".product-info-price .price")
        )
        if not precio_elem:
            # Intentar JSON-LD
            for tag in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(tag.string or "")
                    if isinstance(data, dict) and data.get("price"):
                        precio_real = float(data["price"])
                        diferencia = abs(precio_real - precio_catalogo) / precio_catalogo if precio_catalogo > 0 else 1
                        return {
                            "estado": "ok" if diferencia <= TOLERANCIA else "diverge",
                            "precio_catalogo": precio_catalogo,
                            "precio_real": precio_real,
                            "diferencia_pct": round(diferencia * 100, 1),
                        }
                except Exception:
                    pass
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


def _verificar_maxicarrefour(ean: str, precio_catalogo: float) -> dict:
    """Verifica precio de MaxiCarrefour buscando por EAN con las cookies actuales."""
    if not ean:
        return {"estado": "sin_ean"}
    try:
        phpsessid = os.getenv("CARREFOUR_PHPSESSID", "")
        cf_clearance = os.getenv("CARREFOUR_CF_CLEARANCE", "")
        if not phpsessid:
            return {"estado": "sin_cookies"}

        session = cf_requests.Session(impersonate="safari15_3") if CURL_DISPONIBLE else cf_requests.Session()
        session.cookies.update({"PHPSESSID": phpsessid, "cf_clearance": cf_clearance})
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://comerciante.carrefour.com.ar/",
        }
        url = f"https://comerciante.carrefour.com.ar/api/catalog_system/pub/products/search/{ean}"
        r = session.get(url, headers=headers, timeout=20)

        if r.status_code == 401 or "/login" in r.url:
            return {"estado": "cookies_expiradas"}
        if r.status_code != 200:
            return {"estado": "error_http", "codigo": r.status_code}

        data = r.json()
        if not data:
            return {"estado": "producto_no_encontrado"}

        # Extraer precio del primer resultado
        try:
            precio_real = data[0]["items"][0]["sellers"][0]["commertialOffer"]["Price"]
            diferencia = abs(precio_real - precio_catalogo) / precio_catalogo if precio_catalogo > 0 else 1
            return {
                "estado": "ok" if diferencia <= TOLERANCIA else "diverge",
                "precio_catalogo": precio_catalogo,
                "precio_real": precio_real,
                "diferencia_pct": round(diferencia * 100, 1),
            }
        except (KeyError, IndexError):
            return {"estado": "precio_no_parseable"}
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

    # Seleccionar top N productos ABC=A con 2+ fuentes de precio
    candidatos = [
        p for p in catalogo
        if p.get("abc") == "A"
        and sum(1 for v in p.get("precios", {}).values() if v > 0) >= 2
    ]
    # Ordenar por cantidad de fuentes (más fuentes primero)
    candidatos.sort(key=lambda p: sum(1 for v in p["precios"].values() if v > 0), reverse=True)
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
    if tasa < 80:
        print("ALERTA: Mas del 20% de precios divergen — el catalogo puede estar desactualizado.")
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
            "resultados": resultados,
        }, f, ensure_ascii=False, indent=2)
    print(f"Reporte guardado: {out_path}")

    sys.exit(0 if tasa >= 80 else 1)


if __name__ == "__main__":
    main()
