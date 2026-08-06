#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from datetime import datetime

def main():
    print("=== SCRAPER NINI ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(["python", "targets/nini/scraper_pro.py"], cwd=os.getcwd(), env=env)

    if result.returncode == 0:
        if env.get("PIPELINE_SKIP_CATALOGO"):
            # pipeline_local.py encadena los 9 scrapers y reconstruye el catalogo
            # una sola vez al final -- reconstruirlo aca tambien es trabajo repetido
            # (fuzzy matching sobre 25k+ productos, ~3-5 min tirados por corrida).
            print("\n(catalogo se reconstruye al final del pipeline, no aca)")
        else:
            print("\n=== UNIFICANDO DATOS ===")
            subprocess.run(["python", "actualizar_catalogo.py"], cwd=os.getcwd(), env=env)
            print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER NINI")
        sys.exit(1)

if __name__ == "__main__":
    main()
