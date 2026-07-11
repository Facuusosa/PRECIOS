#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}

    # Siempre verificar cookies antes de scraper — no solo por fecha
    print("\nVerificando cookies MaxiCarrefour...")
    if not _cookies_vigentes():
        print("Cookies invalidas o expiradas — renovando automaticamente...")
        # --no-auto-scrape: este wrapper ya sigue con el scraping el solo mas abajo,
        # asi el renovador no lo dispara tambien y se scrapea 2 veces seguidas.
        r = subprocess.run(
            ["python", "scripts/renovar_cookies_carrefour.py", "--force", "--no-auto-scrape"],
            cwd=BASE_DIR, env=env
        )
        if r.returncode != 0:
            print("ERROR: No se pudieron renovar las cookies.")
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
