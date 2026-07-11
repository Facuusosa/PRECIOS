#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import glob
import subprocess
import sys
from datetime import datetime

def verificar_output():
    patron = os.path.join("targets", "maxiconsumo", "output_maxiconsumo_*.json")
    archivos = sorted(glob.glob(patron), key=os.path.getmtime, reverse=True)
    if not archivos:
        print("  ⚠️  No se encontró archivo de output")
        return
    ultimo = archivos[0]
    with open(ultimo, encoding="utf-8") as f:
        data = json.load(f)
    productos = data if isinstance(data, list) else data.get("productos", [])
    total = len(productos)
    con_precio = sum(1 for p in productos if p.get("precio", 0) > 0)
    con_ean = sum(1 for p in productos if p.get("ean"))
    print(f"\n=== VERIFICACIÓN POST-SCRAPING ===")
    print(f"  Archivo:   {os.path.basename(ultimo)}")
    print(f"  Productos: {total}")
    print(f"  Con precio: {con_precio} ({con_precio*100//max(total,1)}%)")
    print(f"  Con EAN:    {con_ean} ({con_ean*100//max(total,1)}%)")
    if con_ean * 100 // max(total, 1) < 20:
        print(f"  ⚠️  TASA DE EAN BAJA — el enriquecimiento no obtuvo suficientes EANs")
    if con_precio < total * 0.9:
        print(f"  ⚠️  MÁS DEL 10% SIN PRECIO — revisar scraper")

def encontrar_output_reciente():
    """Busca el output más reciente por timestamp en el nombre, no por mtime."""
    patron = os.path.join("targets", "maxiconsumo", "output_maxiconsumo_*.json")
    archivos = sorted(glob.glob(patron), reverse=True)  # orden lexicográfico = cronológico por timestamp en nombre
    return archivos[0] if archivos else None


def main():
    print("=== SCRAPER MAXICONSUMO ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # PYTHONUNBUFFERED: sin esto, si el scraper crashea duro (curl_cffi es extension C)
    # el buffer de la pipe se pierde y el log queda sin NINGUNA linea del scraper
    # (incidente 02-09/07: 8 dias de "ERROR EN SCRAPER MAXICONSUMO" sin causa visible)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(["python", "targets/maxiconsumo/scraper_pro.py"], cwd=os.getcwd(), env=env)

    if result.returncode == 0:
        # Encontrar el output recién generado por timestamp en el nombre (no mtime — enriquecer_eans lo toca después)
        output_nuevo = encontrar_output_reciente()
        if not output_nuevo:
            print("ERROR: No se encontro archivo output del scraper")
            sys.exit(1)
        print(f"  Output del scraper: {os.path.basename(output_nuevo)}")

        print("\n=== ENRIQUECIENDO PRECIOS Y EANs ===")
        subprocess.run(["python", "targets/maxiconsumo/enriquecer_precios.py", output_nuevo], cwd=os.getcwd(), env=env)

        # Re-buscar: enriquecer_precios escribe un nuevo archivo enriquecido
        output_enriquecido = encontrar_output_reciente()
        print("\n=== ENRIQUECIENDO EANs VÍA MAESTRO ===")
        subprocess.run(["python", "enriquecer_eans.py"], cwd=os.getcwd(), env=env)

        verificar_output()

        print("\n=== UNIFICANDO DATOS ===")
        subprocess.run(["python", "actualizar_catalogo.py"], cwd=os.getcwd(), env=env)

        # La verificacion de precios en vivo corre en pipeline_local.py como gate
        # pre-push (no aca: corria 2 veces y su exit code se ignoraba)

        print("\nPara iniciar el servidor: cd BRUJULA-DE-PRECIOS && npm run dev")
    else:
        print("ERROR EN SCRAPER MAXICONSUMO")
        sys.exit(1)

if __name__ == "__main__":
    main()
