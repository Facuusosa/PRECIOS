"""
Consolida todas las fuentes de comercios de outreach en una sola base maestra, sin duplicados.

Fuentes (las que existan en data/outreach/):
- comercios_zonanorte_20260615.json  (base original, 10 comercios)
- candidatos_web1.json               (directorios: tel fijo)
- candidatos_maps.json               (Google Maps: celulares + fijos)
- candidatos_web2.json               (redes: Instagram / Facebook)

Dedup/merge por (nombre normalizado + zona). Si un comercio aparece en varias fuentes, combina
los campos no vacíos (ej.: el directorio aporta dirección+tel, las redes aportan Instagram).

Canal por prioridad: WhatsApp > Instagram DM > Facebook Messenger > Telefono > Sin contacto.
estado: 'contacto_confirmado' si tiene canal digital (whatsapp/instagram/facebook); si solo tel
fijo -> 'solo_fijo'; si nada -> 'sin_contacto'.

Salida: data/outreach/comercios_consolidado.json  (la que usa el panel).

Uso: python scripts/consolidar_candidatos.py
"""
import glob
import json
import os
import re
import unicodedata

DIR = "data/outreach"
SALIDA = f"{DIR}/comercios_consolidado.json"
FUENTES = [
    f"{DIR}/comercios_zonanorte_20260615.json",
    f"{DIR}/candidatos_web1.json",
    f"{DIR}/candidatos_maps.json",
    f"{DIR}/candidatos_web2.json",
]
GENERICOS = {"supermercado", "autoservicio", "almacen", "despensa", "mercado", "minimercado",
             "super", "el", "la", "los", "las", "de", "del", "y", "mi", "maxikiosco", "tienda"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def clave(c: dict) -> str:
    palabras = [w for w in norm(c.get("nombre", "")).split() if w not in GENERICOS]
    nombre = " ".join(palabras) or norm(c.get("nombre", ""))
    return f"{nombre}|{norm(c.get('zona',''))}"


def dir_clave(c: dict) -> str:
    """Calle + altura normalizada, para cazar el mismo local con nombre/zona distintos."""
    d = norm(c.get("direccion", ""))
    d = re.sub(r"\b(av|avenida|calle|gral|general)\b", " ", d).strip()
    m = re.search(r"([a-z][a-z ]+?)\s+(\d{1,5})", d)
    return f"{m.group(1).strip()} {m.group(2)}" if m else ""


def canal_de(c: dict) -> str:
    if c.get("whatsapp"):
        return "WhatsApp"
    if c.get("instagram"):
        return "Instagram DM"
    if c.get("facebook"):
        return "Facebook Messenger"
    if c.get("telefono"):
        return "Telefono"
    return "Sin contacto"


def estado_de(c: dict) -> str:
    if c.get("whatsapp") or c.get("instagram") or c.get("facebook"):
        return "contacto_confirmado"
    if c.get("telefono"):
        return "solo_fijo"
    return "sin_contacto"


def merge(a: dict, b: dict) -> dict:
    """Completa a con los campos no vacios de b (sin pisar lo que ya hay)."""
    for k, v in b.items():
        if v in (None, "", []):
            continue
        if a.get(k) in (None, "", []):
            a[k] = v
    return a


def main():
    maestro = {}
    fuentes_vistas = []
    for f in FUENTES:
        if not os.path.exists(f):
            continue
        fuentes_vistas.append(os.path.basename(f))
        data = json.load(open(f, encoding="utf-8"))
        for c in data.get("comercios", []):
            k = clave(c)
            if k in maestro:
                merge(maestro[k], c)
            else:
                maestro[k] = dict(c)

    # segundo pase: unir por direccion (mismo local con nombre/zona distintos, ej. HLY)
    por_dir, comercios = {}, []
    for c in maestro.values():
        dk = dir_clave(c)
        if dk and dk in por_dir:
            merge(por_dir[dk], c)
        else:
            comercios.append(c)
            if dk:
                por_dir[dk] = c

    for c in comercios:
        c["canal"] = canal_de(c)
        c["estado"] = estado_de(c)
        c.setdefault("instagram", None)
        c.setdefault("facebook", None)
        r = c.get("rating")
        try:
            c["rating"] = float(str(r).replace(",", ".")) if r not in (None, "") else None
        except ValueError:
            c["rating"] = None

    # ranking: primero los contactables digital, luego por rating
    prioridad = {"contacto_confirmado": 0, "solo_fijo": 1, "sin_contacto": 2}
    comercios.sort(key=lambda c: (prioridad.get(c["estado"], 9), -(c.get("rating") or 0)))

    digital = sum(1 for c in comercios if c["estado"] == "contacto_confirmado")
    fijo = sum(1 for c in comercios if c["estado"] == "solo_fijo")
    sin = sum(1 for c in comercios if c["estado"] == "sin_contacto")

    out = {
        "_meta": {
            "fecha": "2026-06-17", "total": len(comercios),
            "fuentes": fuentes_vistas,
            "contactables_digital": digital, "solo_fijo": fijo, "sin_contacto": sin,
        },
        "comercios": comercios,
    }
    json.dump(out, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Consolidado: {SALIDA}")
    print(f"  Fuentes: {', '.join(fuentes_vistas)}")
    print(f"  Total unicos: {len(comercios)} | digital: {digital} | solo fijo: {fijo} | sin contacto: {sin}")
    print("\n  Contactables digital (los que se mandan por DM):")
    for c in comercios:
        if c["estado"] == "contacto_confirmado":
            via = c.get("whatsapp") or (c.get("instagram") and "@" + c["instagram"]) or c.get("facebook")
            print(f"    - {c['nombre'][:30]:30} | {c['canal']:18} | {via}")


if __name__ == "__main__":
    main()
