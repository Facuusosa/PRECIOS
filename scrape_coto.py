#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=== SCRAPER COTO ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}

    # Coto no requiere cookies ni credenciales: API publica de Constructor.io
    result = subprocess.run(
        ["python", "targets/coto/scraper_pro.py"],
        cwd=BASE_DIR, env=env
    )

    if result.returncode == 0:
        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=BASE_DIR, env=env)
        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER COTO — pipeline detenido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
