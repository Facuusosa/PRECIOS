"""
Devuelve un ejemplo de ahorro VALIDADO para el mensaje de outreach.
Cada vez que se corre lee el catalogo del dia, asi el ejemplo esta conectado en tiempo real
con la data y nunca mandamos un precio viejo, outlier o sin validar al comerciante.

Validaciones aplicadas (reglas 08 y 09):
- El producto debe tener 2+ precios > 0.
- Ninguna fuente usada puede estar stale (precio_stale) ni marcada precio_sospechoso.
- Todas las fuentes usadas deben ser frescas (dias_desde_scraping <= MAX_DIAS).
- El ahorro debe estar en rango robusto (MIN_PCT..MAX_PCT): grande para ser innegable aunque
  haya +-3% de variacion por percepciones IIBB segun CUIT, pero no tan grande que parezca mentira.

Uso:
  python scripts/ejemplo_mensaje.py aceite            # mejor ejemplo validado para "aceite"
  python scripts/ejemplo_mensaje.py --tipo almacen    # mejor ejemplo para un tipo de comercio
  python scripts/ejemplo_mensaje.py aceite --frase     # solo la frase lista para el mensaje
"""
import json
import sys

CATALOGO = "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"
NOMBRE = {"yaguar": "Yaguar", "maxicarrefour": "MaxiCarrefour", "maxiconsumo": "Maxiconsumo"}

MAX_DIAS = 7      # frescura: precio de los ultimos 7 dias
MIN_PCT = 20      # ahorro minimo para que valga como gancho
MAX_PCT = 55      # ahorro maximo: arriba de esto sospechamos error y NO lo usamos

SECTORES_POR_TIPO = {
    "kiosco": ["Bebidas", "Kiosco", "Almacen", "Limpieza"],
    "almacen": ["Almacen", "Bebidas", "Limpieza", "Cuidado Personal", "Frescos"],
    "minimercado": ["Almacen", "Bebidas", "Limpieza", "Cuidado Personal", "Frescos", "Congelados"],
}


def fuente_valida(f: dict) -> bool:
    if not isinstance(f, dict):
        return False
    if f.get("precio_stale") or f.get("precio_sospechoso"):
        return False
    d = f.get("dias_desde_scraping")
    return isinstance(d, (int, float)) and d <= MAX_DIAS


def evaluar(p: dict):
    precios = {k: v for k, v in p.get("precios", {}).items() if v and v > 0}
    if len(precios) < 2:
        return None
    fuentes = p.get("fuentes", {})
    # todas las fuentes con precio usado deben estar validadas
    if not all(fuente_valida(fuentes.get(k, {})) for k in precios):
        return None
    caro = max(precios, key=precios.get)
    barato = min(precios, key=precios.get)
    pmax, pmin = round(precios[caro]), round(precios[barato])
    pct = (pmax - pmin) / pmax * 100
    if not (MIN_PCT <= pct <= MAX_PCT):
        return None
    return {
        "nombre": p.get("nombre_display"),
        "sector": p.get("sector", ""),
        "abc": p.get("abc"),
        "n_precios": len(precios),
        "caro": NOMBRE.get(caro, caro), "pmax": pmax,
        "barato": NOMBRE.get(barato, barato), "pmin": pmin,
        "ahorro": pmax - pmin, "pct": round(pct),
        "fecha_caro": fuentes[caro].get("fecha_scraping"),
        "fecha_barato": fuentes[barato].get("fecha_scraping"),
        "link_caro": fuentes[caro].get("link"),
        "link_barato": fuentes[barato].get("link"),
    }


def buscar(terminos=None, tipo=None):
    data = json.load(open(CATALOGO, encoding="utf-8"))
    prods = data if isinstance(data, list) else data.get("productos", [])
    sectores = SECTORES_POR_TIPO.get((tipo or "").lower()) if tipo else None
    out = []
    for p in prods:
        nombre = (p.get("nombre_display") or "").lower()
        if terminos and not any(t.lower() in nombre for t in terminos):
            continue
        if sectores and not any(s.lower() in (p.get("sector", "").lower()) for s in sectores):
            continue
        ev = evaluar(p)
        if ev:
            out.append(ev)
    # priorizar: 3 precios > 2, ABC=A, mayor ahorro dentro del rango robusto
    out.sort(key=lambda x: (x["n_precios"], x["abc"] == "A", x["pct"]), reverse=True)
    return out


def frase(e: dict) -> str:
    # ancla: el precio caro primero, despues el barato
    return (f"el {e['nombre']} figura a ${e['pmax']:,.0f} en {e['caro']} y a ${e['pmin']:,.0f} "
            f"en {e['barato']}: una diferencia de ${e['ahorro']:,.0f} por unidad ({e['pct']}%)"
            ).replace(",", ".")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    solo_frase = "--frase" in sys.argv
    tipo = None
    if "--tipo" in sys.argv:
        i = sys.argv.index("--tipo")
        tipo = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
        args = [a for a in args if a != tipo]
    res = buscar(args or None, tipo)
    if not res:
        print("SIN EJEMPLO VALIDADO para esos criterios (probar otro termino o subir MAX_DIAS).")
        sys.exit(1)
    if solo_frase:
        print(frase(res[0]))
        sys.exit(0)
    print(f"\n{len(res)} ejemplos VALIDADOS (frescos<= {MAX_DIAS}d, sin flags, ahorro {MIN_PCT}-{MAX_PCT}%):\n")
    for e in res[:10]:
        print(f"  * {e['nombre']}  [{e['sector']}, ABC={e['abc']}, {e['n_precios']} precios]")
        print(f"    {frase(e)}")
        print(f"    fechas: {e['barato']} {e['fecha_barato']} | {e['caro']} {e['fecha_caro']}")
        print(f"    verificar: {e['link_barato']}")
        print()
