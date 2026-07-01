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


ALERTAS_MD = RAIZ / "data" / "quality" / "ALERTA.md"


def alertar(msg, accion=""):
    """Alerta visible: ALERTA.md (lo lee Claude en /inicio-sesion) + beep + log.

    Punto unico de notificacion — si algun dia hace falta push al celu (ntfy),
    se agrega aca y llega desde todos los chequeos a la vez.
    """
    log(f"ALERTA: {msg}")
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    with open(ALERTAS_MD, "a", encoding="utf-8") as f:
        f.write(f"\n## {ts} — {msg}\n")
        if accion:
            f.write(f"Accion sugerida: {accion}\n")
    try:
        import winsound
        # Patron grave-grave-agudo, distinto al del renovador de cookies (880/1100)
        for freq in (400, 400, 900):
            winsound.Beep(freq, 300)
    except Exception:
        pass


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


def frescura_por_fuente():
    """Dias desde el dato mas fresco de cada fuente (max fecha_scraping en el catalogo).

    Una fuente congelada con fechas honestas pasa el anti-reciclaje (que cuenta
    precios, no frescura) — asi MCF estuvo 11 dias viejo sin alerta (01/07/2026).
    """
    ultimas = {}
    if not CATALOGO.exists():
        return {}
    with open(CATALOGO, encoding="utf-8") as f:
        data = json.load(f)
    prods = data if isinstance(data, list) else data.get("productos", [])
    for p in prods:
        for may, fuente in p.get("fuentes", {}).items():
            fecha = fuente.get("fecha_scraping", "")
            if fecha > ultimas.get(may, ""):
                ultimas[may] = fecha
    hoy = datetime.now().date()
    dias = {}
    for may, fecha in ultimas.items():
        try:
            dias[may] = (hoy - datetime.strptime(fecha, "%Y-%m-%d").date()).days
        except ValueError:
            continue
    return dias


def run_scraper(wrapper):
    log(f"Corriendo {wrapper}...")
    inicio = datetime.now()
    ok = run(f"python {wrapper}", cwd=RAIZ).returncode == 0
    seg = int((datetime.now() - inicio).total_seconds())
    log(f"{'OK' if ok else 'FALLO'} {wrapper} ({seg}s)")
    return ok


def limpiar_automatico():
    """Limpieza silenciosa post-scrape: pycache + outputs viejos (>30 dias, conserva el ultimo)."""
    import shutil
    from datetime import timedelta

    # __pycache__
    borrados_cache = 0
    for d in RAIZ.rglob("__pycache__"):
        if ".git" not in str(d) and "node_modules" not in str(d) and "BRUJULA-DE-PRECIOS" not in str(d):
            shutil.rmtree(d, ignore_errors=True)
            borrados_cache += 1

    # Outputs viejos de scrapers: conservar el mas reciente de cada mayorista
    limite = datetime.now() - timedelta(days=30)
    borrados_outputs = 0
    mb_liberados = 0.0
    for mayorista in ("yaguar", "maxicarrefour", "maxiconsumo"):
        carpeta = RAIZ / "targets" / mayorista
        if not carpeta.exists():
            continue
        outputs = sorted(carpeta.glob("output_*.json"))
        if len(outputs) <= 1:
            continue
        for f in outputs[:-1]:  # conservar el ultimo siempre
            try:
                ts_str = f.stem.split("_", 2)[-1]  # YYYYMMDD_HHMMSS
                fecha = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            except ValueError:
                continue
            if fecha < limite:
                mb = f.stat().st_size / 1_000_000
                f.unlink()
                borrados_outputs += 1
                mb_liberados += mb

    if borrados_cache or borrados_outputs:
        log(f"Limpieza auto: {borrados_cache} __pycache__ | "
            f"{borrados_outputs} outputs viejos (~{mb_liberados:.1f} MB liberados)")


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
    for may, exito in ok.items():
        if not exito:
            alertar(f"Scraper {may} FALLO hoy",
                    "revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force")
    if sum(ok.values()) == 0:
        log("ERROR: los 3 scrapers fallaron - el catalogo no se toca")
        sys.exit(1)

    # Consolidar con los 3 (los wrappers ya lo regeneran, pero esto deja el estado final)
    log("Regenerando catalogo unificado...")
    if run("python actualizar_catalogo.py", cwd=RAIZ).returncode != 0:
        log("ERROR: actualizar_catalogo.py fallo")
        sys.exit(1)

    log("Enriqueciendo imagenes (URLs Yaguar por SKU)...")
    run("python enriquecer_imagenes.py", cwd=RAIZ)

    # --- Chequeo anti-reciclaje / caida abrupta ---
    despues = contar_por_fuente()
    log(f"Catalogo nuevo: {despues['total']} prods "
        f"(Y={despues['yaguar']} MC={despues['maxicarrefour']} MCO={despues['maxiconsumo']})")

    if antes["total"] > 0:
        caida = (antes["total"] - despues["total"]) / antes["total"]
        if caida > CAIDA_MAX:
            alertar(f"El total de productos cayo {caida:.0%} (>{CAIDA_MAX:.0%}) - NO se publica",
                    "revisar scrapers en data/quality/pipeline_local.log")
            sys.exit(1)
    # Minimos historicos por fuente: si cae por debajo, algo salio mal
    minimos_fuente = {"yaguar": 4000, "maxicarrefour": 3000, "maxiconsumo": 3000}
    for may, minimo in minimos_fuente.items():
        if antes[may] > 100 and despues[may] == 0:
            alertar(f"{may} quedo en 0 precios (antes {antes[may]}) - NO se publica",
                    "revisar scraper y cookies")
            sys.exit(1)
        if despues[may] > 0 and despues[may] < minimo:
            alertar(f"{may} tiene solo {despues[may]} precios (minimo esperado: {minimo}) - NO se publica",
                    "revisar scraper en data/quality/pipeline_local.log")
            sys.exit(1)

    # --- Frescura por fuente: una fuente congelada = scraper roto que nadie ve ---
    FRESCURA_MAX_DIAS = 3
    for may, dias in frescura_por_fuente().items():
        if dias > FRESCURA_MAX_DIAS:
            alertar(f"FUENTE CONGELADA: {may} sin datos frescos hace {dias} dias (se publica igual, fechas honestas)",
                    f"el scraper de {may} viene fallando — revisar data/quality/pipeline_local.log")

    # --- Publicar ---
    if not hay_cambios():
        log("Sin cambios en el catalogo - nada que publicar")
        log("=== PIPELINE COMPLETADO ===")
        return

    # --- Gate final: precios del catalogo vs la web en vivo de cada mayorista ---
    # Corre pegado al scrape a proposito: la sesion PHP de MCF muere en horas,
    # y una divergencia recien scrapeada es señal de bug de matching/parsing.
    log("Verificando precios en vivo (top 20 ABC=A) contra la web de cada mayorista...")
    r_verif = run("python scripts/verificar_precios_real.py 20", cwd=RAIZ)
    if r_verif.returncode == 1:
        alertar("Verificacion en vivo DIVERGENTE: >20% de precios no coinciden con la web - NO se publica",
                "revisar el data/quality/verificacion_precios_*.json mas reciente")
        sys.exit(1)
    if r_verif.returncode == 2:
        alertar("Verificacion en vivo INCONCLUSA (pocas comparaciones efectivas) - se publica igual",
                "ver que fuente quedo sin verificar en data/quality/verificacion_precios_*.json")

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
    limpiar_automatico()
    log("=== PIPELINE COMPLETADO ===")


if __name__ == "__main__":
    main()
