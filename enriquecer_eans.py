#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENRIQUECEDOR DE EANs
Asigna EANs del Listado Maestro a productos de Yaguar y Maxiconsumo
(que no tienen EAN propio) usando fuzzy matching por nombre.

Corre ANTES de actualizar_catalogo.py para maximizar el matching exacto por EAN.
"""

import os
import sys
import json
import glob
import re
import unicodedata
from collections import defaultdict

import pandas as pd

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
RAW_DIR    = os.path.join(BASE_DIR, "data", "raw")
MAESTRO    = os.path.join(RAW_DIR, "Listado Maestro 09-03.xlsx")
THRESHOLD  = 0.60  # Jaccard mínimo para asignar EAN

# ---------------------------------------------------------------------------
# Normalización (igual que actualizar_catalogo.py)
# ---------------------------------------------------------------------------
def clave_nombre(nombre):
    n = (nombre or "").lower().strip()
    n = unicodedata.normalize("NFD", n)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = re.sub(r"(\d),(\d)", r"\1.\2", n)
    n = re.sub(r"[^a-z0-9. ]", " ", n)
    n = re.sub(r"\bx\s*(\d)", r"\1", n)
    n = re.sub(r"(\d+\.?\d*)\s*lts?\b", lambda m: str(int(float(m.group(1))*1000))+"ml", n)
    n = re.sub(r"(\d+\.?\d*)\s*lt\b",   lambda m: str(int(float(m.group(1))*1000))+"ml", n)
    n = re.sub(r"(\d+\.?\d*)\s*l\b",    lambda m: str(int(float(m.group(1))*1000))+"ml", n)
    n = re.sub(r"(\d+)\s*grs?\b",       lambda m: m.group(1)+"gr", n)
    n = re.sub(r"(\d+\.?\d*)\s*kgs?\b", lambda m: str(int(float(m.group(1))*1000))+"gr", n)
    n = re.sub(r"(\d+)\s*(cc|ml|gr|kg|un)\b", r"\1\2", n)
    n = re.sub(r"\.", " ", n)
    return re.sub(r"\s+", " ", n).strip()

STOPWORDS = {"de","la","el","en","y","x","con","por","para","un","una","del","los","las","al","ml","gr","cc","kg","un"}

def palabras(clave):
    return set(w for w in clave.split() if len(w) > 1 and w not in STOPWORDS)

def jaccard(ws_a, ws_b):
    if not ws_a or not ws_b:
        return 0.0
    inter = len(ws_a & ws_b)
    union = len(ws_a | ws_b)
    return inter / union if union else 0.0

# ---------------------------------------------------------------------------
# Cargar Listado Maestro y construir índice
# ---------------------------------------------------------------------------
def cargar_maestro():
    print(f"Cargando Listado Maestro...")
    df = pd.read_excel(MAESTRO)

    # Índice invertido: palabra → [(clave_nombre, ean)]
    word_index = defaultdict(list)
    entries    = []  # (clave, palabras_set, ean)

    for _, row in df.iterrows():
        ean_raw = row.get("Código EAN") or row.get("CODIGO DE BARRAS")
        nombre  = str(row.get("Texto breve material") or "").strip()
        if not nombre or not ean_raw:
            continue
        try:
            ean = str(int(float(str(ean_raw))))
        except (ValueError, TypeError):
            continue

        cl = clave_nombre(nombre)
        ws = palabras(cl)
        if not ws:
            continue

        idx = len(entries)
        entries.append((cl, ws, ean))
        for w in ws:
            word_index[w].append(idx)

    print(f"  {len(entries)} productos en Listado Maestro indexados")
    return entries, word_index

# ---------------------------------------------------------------------------
# Buscar mejor EAN para un nombre dado
# ---------------------------------------------------------------------------
def buscar_ean(nombre_prod, entries, word_index):
    cl   = clave_nombre(nombre_prod)
    ws_p = palabras(cl)
    if not ws_p:
        return None, 0.0

    # Candidatos: solo los que comparten al menos 1 palabra (fast path)
    candidatos = set()
    for w in ws_p:
        for idx in word_index.get(w, []):
            candidatos.add(idx)

    mejor_sim = 0.0
    mejor_ean = None
    for idx in candidatos:
        _, ws_m, ean = entries[idx]
        sim = jaccard(ws_p, ws_m)
        if sim > mejor_sim:
            mejor_sim = sim
            mejor_ean = ean

    return (mejor_ean, mejor_sim) if mejor_sim >= THRESHOLD else (None, mejor_sim)

# ---------------------------------------------------------------------------
# Enriquecer un archivo JSON de scraper
# ---------------------------------------------------------------------------
def enriquecer_archivo(path, entries, word_index, mayorista):
    with open(path, encoding="utf-8") as f:
        productos = json.load(f)

    asignados   = 0
    ya_tenia    = 0
    sin_match   = 0

    for prod in productos:
        ean_actual = str(prod.get("ean", "") or "").strip()
        if ean_actual and ean_actual not in ("", "0", "None", "nan"):
            ya_tenia += 1
            continue

        ean_nuevo, sim = buscar_ean(prod.get("nombre", ""), entries, word_index)
        if ean_nuevo:
            prod["ean"] = ean_nuevo
            asignados += 1
        else:
            sin_match += 1

    # Guardar en el mismo archivo
    with open(path, "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print(f"  {mayorista}: +{asignados} EANs asignados | {ya_tenia} ya tenían | {sin_match} sin match")
    return asignados

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 55)
    print("ENRIQUECEDOR DE EANs — Listado Maestro")
    print("=" * 55)

    if not os.path.isfile(MAESTRO):
        print(f"ERROR: No encontrado {MAESTRO}")
        sys.exit(1)

    entries, word_index = cargar_maestro()

    # Extender con maestro dinamico (EANs de MaxiCarrefour no en el estatico)
    dm_path = os.path.join(BASE_DIR, "data", "raw", "maestro_dinamico.json")
    if os.path.isfile(dm_path):
        with open(dm_path, encoding="utf-8") as _f:
            _dm = json.load(_f)
        _dm_count = 0
        for cl, ean in _dm.get("por_nombre", {}).items():
            ws = palabras(cl)
            if not ws:
                continue
            idx = len(entries)
            entries.append((cl, ws, ean))
            for w in ws:
                word_index[w].append(idx)
            _dm_count += 1
        print(f"  Maestro dinamico: +{_dm_count} entradas adicionales")

    # Yaguar — archivo más reciente
    yaguar_files = sorted(
        glob.glob(os.path.join(BASE_DIR, "targets/yaguar/output_yaguar_*.json")),
        key=os.path.getmtime, reverse=True
    )
    if yaguar_files:
        print(f"\nEnriqueciendo Yaguar: {os.path.basename(yaguar_files[0])}")
        enriquecer_archivo(yaguar_files[0], entries, word_index, "Yaguar")
    else:
        print("  [SKIP] No hay output de Yaguar")

    # Maxiconsumo — archivo más reciente
    maxi_files = sorted(
        glob.glob(os.path.join(BASE_DIR, "targets/maxiconsumo/output_maxiconsumo_*.json")),
        key=os.path.getmtime, reverse=True
    )
    if maxi_files:
        print(f"\nEnriqueciendo Maxiconsumo: {os.path.basename(maxi_files[0])}")
        enriquecer_archivo(maxi_files[0], entries, word_index, "Maxiconsumo")
    else:
        print("  [SKIP] No hay output de Maxiconsumo")

    print("\nListo. Ahora corra: python actualizar_catalogo.py")
    print("=" * 55)

if __name__ == "__main__":
    main()
