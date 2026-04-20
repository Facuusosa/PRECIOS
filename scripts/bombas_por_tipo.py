"""
Dado un tipo de comercio, devuelve los top N productos ABC=A con mayor ahorro.
Usado por el skill /investigar-y-contactar para armar el email personalizado.

Uso: python scripts/bombas_por_tipo.py kiosco
     python scripts/bombas_por_tipo.py almacen
     python scripts/bombas_por_tipo.py minimercado
"""
import json
import sys

CATALOGO = "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"

SECTORES_POR_TIPO = {
    "kiosco": ["Kiosco", "Bebidas", "Almacen", "Limpieza"],
    "almacen": ["Almacen", "Bebidas", "Limpieza", "Cuidado Personal", "Frescos", "Kiosco"],
    "minimercado": ["Almacen", "Bebidas", "Limpieza", "Cuidado Personal", "Frescos", "Kiosco", "Congelados"],
}

NOMBRE_MAYORISTA = {
    "yaguar": "Yaguar",
    "maxicarrefour": "MaxiCarrefour",
    "maxiconsumo": "Maxiconsumo",
}


def calcular_ahorro(precios: dict) -> tuple:
    activos = {k: v for k, v in precios.items() if v and v > 0}
    if len(activos) < 2:
        return None
    mas_caro = max(activos, key=activos.get)
    mas_barato = min(activos, key=activos.get)
    precio_max = activos[mas_caro]
    precio_min = activos[mas_barato]
    ahorro_pesos = precio_max - precio_min
    ahorro_pct = (ahorro_pesos / precio_max) * 100
    return {
        "mas_barato": NOMBRE_MAYORISTA[mas_barato],
        "precio_min": precio_min,
        "mas_caro": NOMBRE_MAYORISTA[mas_caro],
        "precio_max": precio_max,
        "ahorro_pesos": ahorro_pesos,
        "ahorro_pct": ahorro_pct,
    }


def bombas_para_tipo(tipo: str, n: int = 5) -> list:
    tipo = tipo.lower().strip()
    sectores = SECTORES_POR_TIPO.get(tipo, SECTORES_POR_TIPO["almacen"])

    with open(CATALOGO, encoding="utf-8") as f:
        data = json.load(f)
    prods = data if isinstance(data, list) else data.get("productos", [])

    resultados = []
    for p in prods:
        if p.get("abc") != "A":
            continue
        sector = p.get("sector", "")
        if not any(s.lower() in sector.lower() for s in sectores):
            continue
        precios = p.get("precios", {})
        info = calcular_ahorro(precios)
        if info is None:
            continue
        if info["ahorro_pct"] < 5:
            continue
        resultados.append({
            "nombre": p.get("nombre_display"),
            "sector": sector,
            "ean": p.get("ean"),
            **info,
        })

    resultados.sort(key=lambda x: x["ahorro_pct"], reverse=True)
    return resultados[:n]


def formatear_ejemplo(bomba: dict) -> str:
    return (
        f"  * {bomba['nombre']}\n"
        f"    {bomba['mas_barato']}: ${bomba['precio_min']:,.0f}  |  "
        f"{bomba['mas_caro']}: ${bomba['precio_max']:,.0f}  "
        f"=> ahorro ${bomba['ahorro_pesos']:,.0f} ({bomba['ahorro_pct']:.0f}%)"
    )


if __name__ == "__main__":
    tipo = sys.argv[1] if len(sys.argv) > 1 else "almacen"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    bombas = bombas_para_tipo(tipo, n)
    print(f"\nTop {n} bombas ABC=A para tipo '{tipo}':\n")
    for b in bombas:
        print(formatear_ejemplo(b))
    print()
