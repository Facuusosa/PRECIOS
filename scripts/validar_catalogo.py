"""
Validador de calidad del catalogo unificado.
Corre automaticamente post-scraping via hook PostToolUse.
Exit code 1 si hay >50 productos con ratio de precio sospechoso.
"""
import json
import sys
from pathlib import Path

CATALOGO = Path("BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json")
RATIO_CRITICO = 2.5
UMBRAL_CRITICOS = 50
PRECIO_MIN_ANALIZAR = 500


def main():
    if not CATALOGO.exists():
        print(f"[VALIDADOR] No se encontro catalogo en {CATALOGO}")
        sys.exit(0)

    with open(CATALOGO, encoding="utf-8") as f:
        data = json.load(f)

    prods = data if isinstance(data, list) else data.get("productos", [])
    total = len(prods)
    con_2_precios = sum(
        1 for p in prods
        if sum(1 for v in p.get("precios", {}).values() if v and v > 0) >= 2
    )
    con_3_precios = sum(
        1 for p in prods
        if sum(1 for v in p.get("precios", {}).values() if v and v > 0) == 3
    )

    criticos = []
    for p in prods:
        precios = {k: v for k, v in p.get("precios", {}).items() if v and v > PRECIO_MIN_ANALIZAR}
        if len(precios) < 2:
            continue
        vmax = max(precios.values())
        vmin = min(precios.values())
        if vmin > 0 and vmax / vmin > RATIO_CRITICO:
            criticos.append({
                "nombre": p.get("nombre_display", "?"),
                "ratio": round(vmax / vmin, 1),
                "precios": precios,
            })

    criticos.sort(key=lambda x: x["ratio"], reverse=True)

    # Metricas de cobertura por fuente
    con_yaguar   = sum(1 for p in prods if p.get("precios", {}).get("yaguar", 0) > 0)
    con_maxicarr = sum(1 for p in prods if p.get("precios", {}).get("maxicarrefour", 0) > 0)
    con_maxicons = sum(1 for p in prods if p.get("precios", {}).get("maxiconsumo", 0) > 0)
    sin_imagen   = sum(
        1 for p in prods
        if not p.get("imagen") or any(ph in p.get("imagen", "") for ph in ["base.png", "/0000-", "noimage"])
    )
    con_link_yag = sum(1 for p in prods if p.get("fuentes", {}).get("yaguar", {}).get("link"))
    con_link_mco = sum(1 for p in prods if p.get("fuentes", {}).get("maxiconsumo", {}).get("link"))

    print(f"\n[VALIDADOR CATALOGO]")
    print(f"  Total productos:       {total:,}")
    print(f"  ---- Cobertura por fuente ----")
    print(f"  Yaguar:                {con_yaguar:,} ({con_yaguar/total*100:.1f}%)")
    print(f"  MaxiCarrefour:         {con_maxicarr:,} ({con_maxicarr/total*100:.1f}%)")
    print(f"  Maxiconsumo:           {con_maxicons:,} ({con_maxicons/total*100:.1f}%)")
    print(f"  ---- Comparabilidad ----")
    print(f"  Con 2+ precios:        {con_2_precios:,} ({con_2_precios/total*100:.1f}%)")
    print(f"  Con 3 precios:         {con_3_precios:,} ({con_3_precios/total*100:.1f}%)")
    print(f"  ---- Calidad ----")
    print(f"  Sin imagen valida:     {sin_imagen:,} ({sin_imagen/total*100:.1f}%)")
    print(f"  Con link Yaguar:       {con_link_yag:,}")
    print(f"  Con link Maxiconsumo:  {con_link_mco:,}")
    print(f"  Ratio sospechoso >{RATIO_CRITICO}x: {len(criticos)}")

    if criticos:
        print(f"\n  Top 10 ratios sospechosos:")
        for c in criticos[:10]:
            precios_str = " | ".join(f"{k}: ${v:,.0f}" for k, v in c["precios"].items())
            print(f"    [{c['ratio']}x] {c['nombre'][:50]} -> {precios_str}")

    if len(criticos) > UMBRAL_CRITICOS:
        print(f"\n  [ALERTA] {len(criticos)} productos criticos superan el umbral ({UMBRAL_CRITICOS}).")
        print(f"  Revisar threshold en actualizar_catalogo.py (paso 6e).")
        sys.exit(1)
    else:
        print(f"\n  [OK] Calidad dentro de parametros.")
        sys.exit(0)


if __name__ == "__main__":
    main()
