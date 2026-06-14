"""
Pipeline LOCAL para Brujula de Precios.

Corre en la PC de Facu (Programador de tareas de Windows) cada manana. Reemplaza al
cron de Railway: aca los 3 scrapers funcionan porque usan la IP de casa (Maxiconsumo
bloquea IPs de datacenter, por eso fallaba en la nube).

Secuencia:
  1. Corre los 3 scrapers via sus wrappers (que ya manejan cookies de MaxiCarrefour
     y el enriquecimiento de Maxiconsumo).
  2. Regenera el catalogo unificado consolidado con los 3.
  3. Chequeo anti-reciclaje: si el total de productos cae mucho o una fuente queda en
     cero, NO pushea y avisa (evita publicar datos rotos/viejos en silencio).
  4. git push -> Vercel redeploy automatico.

No necesita tokens: usa el git local ya configurado de Facu.
Uso manual:  python pipeline_local.py
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Los scrapers imprimen emojis/tildes; en Windows el default cp1252 crashea. Forzar
# UTF-8 en este proceso y en todos los subprocesos que lance (regla code-style).
os.environ["PYTHONUTF8"] = "1"

RAIZ = Path(__file__).resolve().parent
BRUJULA_DIR = RAIZ / "BRUJULA-DE-PRECIOS"
CATALOGO = BRUJULA_DIR / "data" / "processed" / "catalogo_unificado.json"
CAIDA_MAX = 0.15  # si el total de productos cae mas que esto, no se publica


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd, cwd=None):
    # encoding utf-8 + errors=replace: en Windows el default cp1252 crashea con
    # nombres de producto con tildes/simbolos (regla code-style del proyecto).
    return subprocess.run(cmd, shell=True, cwd=cwd, text=True,
                          encoding="utf-8", errors="replace")


def contar_por_fuente():
    """Productos con precio por fuente en el catalogo actual (para anti-reciclaje)."""
    conteo = {"total": 0, "yaguar": 0, "maxicarrefour": 0, "maxiconsumo": 0}
    if not CATALOGO.exists():
        return conteo
    with open(CATALOGO, encoding="utf-8") as f:
        data = json.load(f)
    prods = data if isinstance(data, list) else data.get("productos", [])
    conteo["total"] = len(prods)
    for p in prods:
        precios = p.get("precios", {})
        for may in ("yaguar", "maxicarrefour", "maxiconsumo"):
            if precios.get(may, 0) > 0:
                conteo[may] += 1
    return conteo


def run_scraper(wrapper):
    log(f"Corriendo {wrapper}...")
    inicio = datetime.now()
    ok = run(f"python {wrapper}", cwd=RAIZ).returncode == 0
    seg = int((datetime.now() - inicio).total_seconds())
    log(f"{'OK' if ok else 'FALLO'} {wrapper} ({seg}s)")
    return ok


def hay_cambios():
    r = subprocess.run(
        "git status --porcelain data/processed/catalogo_unificado.json",
        shell=True, cwd=BRUJULA_DIR, text=True, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    return bool(r.stdout.strip())


def main():
    log("=== PIPELINE LOCAL BRUJULA ===")
    antes = contar_por_fuente()
    log(f"Catalogo actual: {antes['total']} prods "
        f"(Y={antes['yaguar']} MC={antes['maxicarrefour']} MCO={antes['maxiconsumo']})")

    ok = {
        "yaguar":        run_scraper("scrape_yaguar.py"),
        "maxicarrefour": run_scraper("scrape_maxicarrefour.py"),
        "maxiconsumo":   run_scraper("scrape_maxiconsumo.py"),
    }
    log(f"Scrapers OK: {sum(ok.values())}/3")
    if sum(ok.values()) == 0:
        log("ERROR: los 3 scrapers fallaron - el catalogo no se toca")
        sys.exit(1)

    # Consolidar con los 3 (los wrappers ya lo regeneran, pero esto deja el estado final)
    log("Regenerando catalogo unificado...")
    if run("python actualizar_catalogo.py", cwd=RAIZ).returncode != 0:
        log("ERROR: actualizar_catalogo.py fallo")
        sys.exit(1)

    # --- Chequeo anti-reciclaje / caida abrupta ---
    despues = contar_por_fuente()
    log(f"Catalogo nuevo: {despues['total']} prods "
        f"(Y={despues['yaguar']} MC={despues['maxicarrefour']} MCO={despues['maxiconsumo']})")

    if antes["total"] > 0:
        caida = (antes["total"] - despues["total"]) / antes["total"]
        if caida > CAIDA_MAX:
            log(f"ALERTA: el total cayo {caida:.0%} (>{CAIDA_MAX:.0%}) - NO se publica. Revisar scrapers.")
            sys.exit(1)
    for may in ("yaguar", "maxicarrefour", "maxiconsumo"):
        if antes[may] > 100 and despues[may] == 0:
            log(f"ALERTA: {may} quedo en 0 precios (antes {antes[may]}) - NO se publica.")
            sys.exit(1)

    # --- Publicar ---
    if not hay_cambios():
        log("Sin cambios en el catalogo - nada que publicar")
        log("=== PIPELINE COMPLETADO ===")
        return

    fecha = datetime.now().strftime("%d/%m/%Y")
    r = run(
        'git add data/processed/catalogo_unificado.json && '
        f'git commit -m "data: actualizacion automatica {fecha} [local]" && '
        'git push',
        cwd=BRUJULA_DIR,
    )
    if r.returncode != 0:
        log("ERROR: git push fallo")
        sys.exit(1)
    log("Push OK -> Vercel redeploy disparado")
    log("=== PIPELINE COMPLETADO ===")


if __name__ == "__main__":
    main()
