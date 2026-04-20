#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación en vivo de precio en Maxiconsumo para un producto dado.
Uso: python verificar_precio.py "nombre del producto"
"""

import sys
import re
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

BASE_URL = "https://maxiconsumo.com"
IMPERSONATE = "safari15_3"
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
}


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
        return float(limpio)
    except ValueError:
        return 0.0


def buscar_producto(query: str) -> list[dict]:
    session = curl_requests.Session()
    url = f"{BASE_URL}/catalogsearch/result/?q={query.replace(' ', '+')}"

    try:
        r = session.get(url, impersonate=IMPERSONATE, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}", file=sys.stderr)
        return []

    if r.status_code != 200:
        print(f"[ERROR] Status {r.status_code}", file=sys.stderr)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.find_all("li", class_="item product product-item")

    resultados = []
    for item in items[:5]:
        enlace = item.find("a", class_="product-item-link")
        if not enlace:
            continue
        nombre = enlace.get_text(strip=True)
        precio_span = item.find("span", class_="price")
        precio = limpiar_precio(precio_span.get_text(strip=True)) if precio_span else 0.0
        if precio > 0:
            resultados.append({"nombre": nombre, "precio": precio})

    return resultados


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Uso: python verificar_precio.py <nombre producto>")
        sys.exit(1)

    print(f"Buscando en Maxiconsumo: '{query}'")
    resultados = buscar_producto(query)

    if not resultados:
        print("Sin resultados o Cloudflare bloqueó la request.")
        sys.exit(1)

    for r in resultados:
        print(f"  {r['nombre'][:55]:<55} | ${r['precio']:,.2f}")
