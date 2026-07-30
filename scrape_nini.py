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
        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=os.getcwd(), env=env)
        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER NINI")
        sys.exit(1)

if __name__ == "__main__":
    main()
