#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _cookies_necesitan_renovacion() -> bool:
    from dotenv import load_dotenv
    load_dotenv()
    fecha_str = os.getenv("CARREFOUR_COOKIE_DATE", "")
    if not fecha_str:
        return True
    try:
        dias = (date.today() - date.fromisoformat(fecha_str)).days
        return dias > 25
    except ValueError:
        return True


def main():
    print("=== SCRAPER MAXICARREFOUR ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    env = {**os.environ, "PYTHONUTF8": "1"}

    # Auto-renovar cookies si tienen >25 días
    if _cookies_necesitan_renovacion():
        print("\nCookies próximas a vencer o sin fecha — intentando renovar...")
        r = subprocess.run(
            ["python", "scripts/renovar_cookies_carrefour.py"],
            cwd=BASE_DIR, env=env
        )
        if r.returncode != 0:
            print("AVISO: Renovación automática falló — continuando con cookies actuales.")
            print("Si el scraper falla, renovar manualmente (ver .claude/docs/operaciones.md).")

    result = subprocess.run(
        ["python", "targets/maxicarrefour/scraper_pro.py"],
        cwd=BASE_DIR, env=env
    )

    if result.returncode == 0:
        print("\n=== ENRIQUECIENDO LINKS MAXICARREFOUR ===")
        subprocess.run(
            ["python", "scripts/enriquecer_links_maxicarrefour.py"],
            cwd=BASE_DIR, env=env
        )

        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=BASE_DIR, env=env)
        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER MAXICARREFOUR — pipeline detenido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
