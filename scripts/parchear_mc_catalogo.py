#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parche quirurgico: actualiza SOLO los precios de MaxiCarrefour del catalogo
con un output fresco del scraper, sin tocar Yaguar/Maxiconsumo.

Caso de uso (11/06/2026): el scraper MC fallo 14 dias en Railway y el fallback
reciclo precios viejos con fecha de hoy. Yaguar/MCO del catalogo de produccion
estan frescos (Railway los scrapea bien) pero MC no — y regenerar todo local
pisaria Yaguar/MCO frescos con outputs locales viejos.

Uso: python scripts/parchear_mc_catalogo.py targets/maxicarrefour/output_maxicarrefour_YYYYMMDD_HHMMSS.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CATALOGO = BASE_DIR / "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"
FECHA_REAL_VIEJA = "2026-05-28"  # ultimo scraping MC real antes del parche
OUTLIER_MC_RATIO = 2.5

output_path = Path(sys.argv[1])
hoy = datetime.now().strftime("%Y-%m-%d")

with open(output_path, encoding="utf-8") as f:
    frescos = json.load(f)
por_ean = {p["ean"]: p for p in frescos if p.get("ean") and p.get("precio", 0) > 0}
print(f"Output fresco: {len(por_ean)} productos MC con precio")

with open(CATALOGO, encoding="utf-8") as f:
    catalogo = json.load(f)

actualizados = sin_refrescar = descartados_outlier = 0
for p in catalogo:
    fuente_mc = p.get("fuentes", {}).get("maxicarrefour")
    precio_mc = p["precios"].get("maxicarrefour", 0)
    if not fuente_mc and precio_mc <= 0:
        continue
    ean = p.get("ean", "")
    fresco = por_ean.get(ean)
    if fresco:
        p["precios"]["maxicarrefour"] = fresco["precio"]
        if fuente_mc is None:
            fuente_mc = p.setdefault("fuentes", {}).setdefault("maxicarrefour", {})
        fuente_mc["fecha_scraping"] = hoy
        if fresco.get("nombre"):
            fuente_mc["nombre"] = fresco["nombre"]
        if fresco.get("link"):
            fuente_mc["link"] = fresco["link"]
        actualizados += 1
    else:
        # No recapturado hoy: la fecha vuelve a ser la REAL (28/05), sin maquillaje
        if fuente_mc is not None:
            fuente_mc["fecha_scraping"] = FECHA_REAL_VIEJA
        sin_refrescar += 1

# Re-aplicar filtro outlier MC (paso 6f del pipeline)
for p in catalogo:
    precio_mc = p["precios"].get("maxicarrefour", 0)
    if precio_mc <= 0:
        continue
    otras = [v for k, v in p["precios"].items() if k != "maxicarrefour" and v > 0]
    if not otras:
        continue
    mediana = sorted(otras)[len(otras) // 2]
    if mediana > 0 and precio_mc > mediana * OUTLIER_MC_RATIO:
        p["precios"]["maxicarrefour"] = 0
        p["fuentes"].pop("maxicarrefour", None)
        descartados_outlier += 1

# Recalcular flag precio_sospechoso (paso 6g) con los precios nuevos
sospechosos = 0
for p in catalogo:
    vals = [v for v in p["precios"].values() if v > 0]
    if len(vals) >= 2 and min(vals) < max(vals) * 0.4:
        p["precio_sospechoso"] = True
        sospechosos += 1
    else:
        p.pop("precio_sospechoso", None)

with open(CATALOGO, "w", encoding="utf-8") as f:
    json.dump(catalogo, f, ensure_ascii=False, indent=2)

comparables = sum(1 for p in catalogo if sum(1 for v in p["precios"].values() if v > 0) >= 2)
print(f"MC actualizados a hoy: {actualizados}")
print(f"MC sin refrescar (fecha real {FECHA_REAL_VIEJA}): {sin_refrescar}")
print(f"Outliers MC descartados: {descartados_outlier}")
print(f"Flageados sospechosos: {sospechosos}")
print(f"Comparables (2+ precios): {comparables}")
print(f"Total productos: {len(catalogo)}")
