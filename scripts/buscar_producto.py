"""
Busca productos en el catalogo por palabra clave y muestra el ahorro entre mayoristas.
Usado en el flujo de outreach para encontrar ejemplos de ahorro REALES y reconocibles
en productos que un comercio concreto vende.

Uso: python scripts/buscar_producto.py coca
     python scripts/buscar_producto.py "paladini" "san cor" ades
"""
import json
import sys

CATALOGO = "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"
NOMBRE_MAYORISTA = {"yaguar": "Yaguar", "maxicarrefour": "MaxiCarrefour", "maxiconsumo": "Maxiconsumo"}


def ahorro(precios: dict):
    activos = {k: v for k, v in precios.items() if v and v > 0}
    if len(activos) < 2:
        return None
    caro = max(activos, key=activos.get)
    barato = min(activos, key=activos.get)
    pmax, pmin = activos[caro], activos[barato]
    return {"barato": NOMBRE_MAYORISTA.get(barato, barato), "pmin": pmin,
            "caro": NOMBRE_MAYORISTA.get(caro, caro), "pmax": pmax,
            "ahorro": pmax - pmin, "pct": (pmax - pmin) / pmax * 100, "n": len(activos)}


def buscar(terminos: list) -> list:
    with open(CATALOGO, encoding="utf-8") as f:
        data = json.load(f)
    prods = data if isinstance(data, list) else data.get("productos", [])
    out = []
    for p in prods:
        nombre = (p.get("nombre_display") or "").lower()
        if not any(t.lower() in nombre for t in terminos):
            continue
        info = ahorro(p.get("precios", {}))
        if info is None:
            continue
        out.append({"nombre": p.get("nombre_display"), "sector": p.get("sector", ""), **info})
    out.sort(key=lambda x: (x["n"], x["pct"]), reverse=True)
    return out


if __name__ == "__main__":
    terminos = sys.argv[1:] or ["coca"]
    res = buscar(terminos)
    print(f"\n{len(res)} productos con 2+ precios para {terminos}:\n")
    for r in res[:25]:
        print(f"  * {r['nombre']}  [{r['sector']}]  ({r['n']} precios)")
        print(f"    {r['barato']}: ${r['pmin']:,.0f}  |  {r['caro']}: ${r['pmax']:,.0f}"
              f"  => ahorro ${r['ahorro']:,.0f} ({r['pct']:.0f}%)")
    print()
