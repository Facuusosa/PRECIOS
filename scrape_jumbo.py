#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=== SCRAPER JUMBO (retail) ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}

    # Jumbo no requiere cookies ni credenciales: API VTEX Intelligent Search
    # publica, sin anti-bot detectado (mismo trato que Coto/Carrefour/Dia/
    # Masonline, fuente cadena)
    result = subprocess.run(
        ["python", "targets/jumbo/scraper_pro.py"],
        cwd=BASE_DIR, env=env
    )

    if result.returncode == 0:
        if env.get("PIPELINE_SKIP_CATALOGO"):
            # pipeline_local.py encadena los 9 scrapers y reconstruye el catalogo
            # una sola vez al final -- reconstruirlo aca tambien es trabajo repetido
            # (fuzzy matching sobre 25k+ productos, ~3-5 min tirados por corrida).
            print("\n(catalogo se reconstruye al final del pipeline, no aca)")
        else:
            print("\n=== UNIFICANDO DATOS ===")
            subprocess.run(["python", "actualizar_catalogo.py"], cwd=BASE_DIR, env=env)
            print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER JUMBO - pipeline detenido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
