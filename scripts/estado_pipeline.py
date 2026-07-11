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
import re
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEREDICTO = os.path.join(BASE, "data", "quality", "VEREDICTO.md")
ALERTA = os.path.join(BASE, "data", "quality", "ALERTA.md")

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
