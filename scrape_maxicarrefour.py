#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import json
import os
import sys
import subprocess
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _output_sano_de_hoy() -> str:
    """Ruta del output MCF de hoy con >50% de precios > 0, o '' si no hay.

    Lo usa el rescate nocturno (renovar_cookies_diario.bat --solo-si-falta-hoy):
    si la corrida de la manana ya trajo datos sanos, no hay que scrapear de nuevo.
    """
    hoy = datetime.now().strftime("%Y%m%d")
    patron = os.path.join(BASE_DIR, "targets", "maxicarrefour", f"output_maxicarrefour_{hoy}_*.json")
    resultado = ""
    for ruta in sorted(glob.glob(patron), reverse=True):
        try:
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        prods = data if isinstance(data, list) else data.get("productos", [])
        con_precio = sum(1 for p in prods if p.get("precio", 0) > 0)
        if prods and con_precio > len(prods) * 0.5:
            resultado = ruta
            break
    return resultado


def _cookies_vigentes() -> bool:
    """Verifica con un request real si las cookies actuales devuelven precios (no 'private')."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    phpsessid    = os.getenv("CARREFOUR_PHPSESSID", "")
    cf_clearance = os.getenv("CARREFOUR_CF_CLEARANCE", "")
    if not phpsessid:
        return False
    try:
        from curl_cffi import requests as cf_requests
        # Mismo impersonate que el scraper_pro.py para que cf_clearance sea valido
        session = cf_requests.Session(impersonate="chrome131")
    except ImportError:
        return True  # Sin curl_cffi no podemos verificar, asumir vigentes

    session.cookies.update({"PHPSESSID": phpsessid, "cf_clearance": cf_clearance})
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Referer": "https://comerciante.carrefour.com.ar/",
    })
    try:
        r = session.get(
            "https://comerciante.carrefour.com.ar/products",
            params={
                "currentUrl": "sec/almacen", "filters": "", "orderBy": "default",
                "currentPage": 1, "itemsPerPage": 1, "method": "productsList"
            },
            timeout=15
        )
        if r.status_code != 200:
            return False
        body = r.text.strip()
        # 'data-price="private"': desde ~21/06/2026 la sesion muerta ya no devuelve
        # item_card_public sino item_card normal con el precio oculto — sin este
        # chequeo, cookies muertas pasan como vigentes y el scraper falla en silencio
        if not body or "item_card_public" in body or 'data-price="private"' in body or len(body) < 50:
            return False
        # Señal POSITIVA obligatoria (fix 10/07/2026): exigir un precio numerico real.
        # Solo descartar señales negativas dejaba pasar cualquier body raro (challenge
        # de Cloudflare, error HTML) como "vigente" — asi la renovacion en falso del
        # 10/07 valido OK y el scrape guardo 3.948 productos con precio 0.
        import re as _re
        if not _re.search(r'data-price="\d', body):
            return False
        return True
    except Exception:
        return False


def main():
    print("=== SCRAPER MAXICARREFOUR ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if "--solo-si-falta-hoy" in sys.argv:
        ya_scrapeado = _output_sano_de_hoy()
        if ya_scrapeado:
            print(f"Ya hay output sano de hoy ({os.path.basename(ya_scrapeado)}) -- nada que hacer.")
            sys.exit(0)
        print("Sin output sano de hoy -- corriendo el rescate.")

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}

    # Siempre verificar cookies antes de scraper — no solo por fecha
    print("\nVerificando cookies MaxiCarrefour...")
    if not _cookies_vigentes():
        # 2 intentos: desde el rediseño MAXI PEDIDO el login falla de forma
        # intermitente y el 2do intento suele prender (ALERTA.md 12/07/2026 —
        # antes ese reintento lo hacia Facu a mano por la tarde).
        for intento in (1, 2):
            print(f"Cookies invalidas o expiradas -- renovando automaticamente (intento {intento}/2)...")
            # --no-auto-scrape: este wrapper ya sigue con el scraping el solo mas abajo,
            # asi el renovador no lo dispara tambien y se scrapea 2 veces seguidas.
            r = subprocess.run(
                ["python", "scripts/renovar_cookies_carrefour.py", "--force", "--no-auto-scrape"],
                cwd=BASE_DIR, env=env
            )
            if r.returncode == 0:
                break
            if intento == 1:
                print("Renovacion fallida -- esperando 60s antes del segundo intento...")
                time.sleep(60)
        if r.returncode != 0:
            print("ERROR: No se pudieron renovar las cookies (2 intentos).")
            print("Renovar manualmente: ver .claude/docs/operaciones.md")
            print("Abortando — no tiene sentido scraper sin cookies validas.")
            sys.exit(1)
        print("Cookies renovadas OK.")
    else:
        print("Cookies vigentes OK.")

    result = subprocess.run(
        ["python", "targets/maxicarrefour/scraper_pro.py"],
        cwd=BASE_DIR, env=env
    )

    if result.returncode == 0:
        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=BASE_DIR, env=env)
        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER MAXICARREFOUR — pipeline detenido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
