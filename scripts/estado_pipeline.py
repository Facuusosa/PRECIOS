#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estado compacto del pipeline para el hook SessionStart de Claude Code.

Imprime VEREDICTO.md (ultima corrida) + alertas abiertas de ALERTA.md + frescura
de outputs. Su stdout entra al contexto de Claude en cada sesion nueva — asi
Claude SIEMPRE arranca sabiendo si el pipeline fallo, sin que nadie se lo pida
(pedido de Facu 10/07/2026: "que lo veas de manera automatica").
Mantener la salida CORTA: entra al contexto de todas las sesiones.
"""
import os
import sys
import glob
import json
import re
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEREDICTO = os.path.join(BASE, "data", "quality", "VEREDICTO.md")
ALERTA = os.path.join(BASE, "data", "quality", "ALERTA.md")
MATCHES_PEND = os.path.join(BASE, "data", "quality", "matches_pendientes.json")
MAPEOS_SOSP = os.path.join(BASE, "data", "quality", "mapeos_sospechosos.json")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=== ESTADO DEL PIPELINE (auto, hook SessionStart) ===")

if os.path.exists(VEREDICTO):
    with open(VEREDICTO, encoding="utf-8") as f:
        print(f.read().strip())
else:
    print("Sin VEREDICTO.md todavia (el pipeline nuevo no corrio desde el fix 10/07).")

# Alertas abiertas = encabezados "## dd/mm/aaaa" en cualquier parte del archivo
# (alertar() appendea al final; las manuales van arriba de Resueltas). Las resueltas
# se consolidan como items "- " bajo "## Resueltas", nunca como encabezado ##.
if os.path.exists(ALERTA):
    with open(ALERTA, encoding="utf-8") as f:
        contenido = f.read()
    abiertas = re.findall(r"^## (\d{2}/\d{2}/\d{4}.+)$", contenido, re.MULTILINE)
    if abiertas:
        print(f"\nALERTAS ABIERTAS ({len(abiertas)}):")
        for a in abiertas[-8:]:
            print(f"- {a}")
        print("(mover a 'Resueltas' en data/quality/ALERTA.md cuando se resuelvan)")

# Materiales de matching esperando revision manual de Facu (pedido 14/07/2026:
# "haceme acordar siempre"). Claude debe RECORDARSELO al abrir la sesion.
n_pend = n_sosp = 0
artifact_url = ""
try:
    if os.path.exists(MATCHES_PEND):
        _mp = json.load(open(MATCHES_PEND, encoding="utf-8"))
        n_pend = len(_mp.get("pendientes", []))
        artifact_url = _mp.get("artifact_url", "")
    if os.path.exists(MAPEOS_SOSP):
        n_sosp = len(json.load(open(MAPEOS_SOSP, encoding="utf-8")).get("sospechosos", []))
except (json.JSONDecodeError, OSError):
    pass
if n_pend or n_sosp:
    print(f"\nMATERIALES DE MATCHING A REVISAR CON FACU: {n_pend} matches probables "
          f"(data/quality/matches_pendientes.json) + {n_sosp} mapeos sospechosos "
          f"(data/quality/mapeos_sospechosos.json).")
    if artifact_url:
        print(f"-> Pagina de revision con checkboxes (tildar + 'Copiar resultado' + "
              f"pegar a Claude): {artifact_url}")
    print("-> Recordarselo a Facu al inicio de la sesion; cada aprobado = un comparable mas.")

# Frescura del output mas reciente por fuente
print("\nUltimo output por fuente:")
hoy = datetime.now().date()
for may in ("yaguar", "maxicarrefour", "maxiconsumo", "coto", "carrefour", "dia"):
    outputs = [f for f in sorted(glob.glob(os.path.join(BASE, "targets", may, f"output_{may}_*.json")))
               if "raw" not in f and "enriched" not in f]
    if not outputs:
        print(f"- {may}: SIN OUTPUTS")
        continue
    nombre = os.path.basename(outputs[-1])
    try:
        fecha = datetime.strptime(nombre.split("_")[-2], "%Y%m%d").date()
        dias = (hoy - fecha).days
        marca = "" if dias <= 1 else f"  <- {dias} dias de atraso"
        print(f"- {may}: {nombre}{marca}")
    except (ValueError, IndexError):
        print(f"- {may}: {nombre}")
