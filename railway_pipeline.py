"""
Pipeline automatico para Railway cron.
Horario: 0 9 * * * (9 AM UTC = 6 AM Argentina)

Variables de entorno requeridas en Railway:
  YAGUAR_USERNAME, YAGUAR_PASSWORD
  CARREFOUR_PHPSESSID, CARREFOUR_CF_CLEARANCE
  GITHUB_TOKEN  (Personal Access Token con scope repo)
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BRUJULA_REPO = "https://github.com/Facuusosa/BRUJULA-DE-PRECIOS.git"
BRUJULA_DIR = Path("BRUJULA-DE-PRECIOS")
LOG: list[str] = []


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.append(line)


def run(cmd: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, cwd=cwd, text=True)


def setup_brujula_repo() -> bool:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log("ERROR: GITHUB_TOKEN no configurado en Railway")
        return False

    repo_url = f"https://{token}@github.com/Facuusosa/BRUJULA-DE-PRECIOS.git"

    if BRUJULA_DIR.exists() and (BRUJULA_DIR / ".git").exists():
        log("Actualizando BRUJULA-DE-PRECIOS (git pull)...")
        result = run(f"git pull {repo_url} main", cwd=BRUJULA_DIR)
        if result.returncode != 0:
            log("WARN: git pull fallo, continuando con version local...")
    else:
        log("Clonando BRUJULA-DE-PRECIOS...")
        result = run(f"git clone {repo_url} {BRUJULA_DIR}")
        if result.returncode != 0:
            log("ERROR: No se pudo clonar el repo")
            return False

    run("git config user.email railway@brujula.app", cwd=BRUJULA_DIR)
    run("git config user.name Railway-Pipeline", cwd=BRUJULA_DIR)
    return True


def run_scraper(script: str) -> bool:
    log(f"Corriendo {script}...")
    start = datetime.now()
    result = run(f"python {script}")
    elapsed = int((datetime.now() - start).total_seconds())

    if result.returncode == 0:
        log(f"OK {script} ({elapsed}s)")
        return True
    log(f"WARN: {script} fallo en {elapsed}s (exit {result.returncode})")
    return False


def count_catalog_products() -> int:
    catalog = BRUJULA_DIR / "data/processed/catalogo_unificado.json"
    if not catalog.exists():
        return 0
    with open(catalog, encoding="utf-8") as f:
        data = json.load(f)
    prods = data if isinstance(data, list) else data.get("productos", [])
    return len(prods)


def push_catalog() -> bool:
    token = os.getenv("GITHUB_TOKEN")
    repo_url = f"https://{token}@github.com/Facuusosa/BRUJULA-DE-PRECIOS.git"
    fecha = datetime.now().strftime("%d/%m/%Y")

    cmd = (
        "git add data/processed/catalogo_unificado.json && "
        f'git commit -m "data: actualizacion automatica {fecha} [Railway]" && '
        f"git push {repo_url} main"
    )
    result = run(cmd, cwd=BRUJULA_DIR)
    if result.returncode == 0:
        log("Push exitoso -> Vercel redeploy activado")
        return True
    log("ERROR: git push fallo")
    return False


def main() -> None:
    log("=== PIPELINE BRUJULA DE PRECIOS ===")

    if not setup_brujula_repo():
        sys.exit(1)

    ok = {"yaguar": False, "maxicarrefour": False, "maxiconsumo": False}
    ok["yaguar"] = run_scraper("scrape_yaguar.py")
    ok["maxicarrefour"] = run_scraper("scrape_maxicarrefour.py")
    ok["maxiconsumo"] = run_scraper("scrape_maxiconsumo.py")

    scrapers_ok = sum(ok.values())
    log(f"Scrapers exitosos: {scrapers_ok}/3")

    if not ok["maxicarrefour"]:
        log("AVISO: MaxiCarrefour fallo. Si lleva >30 dias, renovar cookies en .env")

    if scrapers_ok == 0:
        log("ERROR CRITICO: Todos los scrapers fallaron - abortando")
        sys.exit(1)

    catalog = BRUJULA_DIR / "data/processed/catalogo_unificado.json"
    if not catalog.exists():
        log("Catalogo no encontrado, corriendo actualizar_catalogo.py...")
        run("python actualizar_catalogo.py")

    log("Validando calidad del catalogo...")
    run("python scripts/validar_catalogo.py")

    total = count_catalog_products()
    log(f"Total productos: {total:,}")
    if total < 5000:
        log(f"WARN: {total} productos es menos de lo esperado (normal > 15k)")

    push_catalog()
    log("=== PIPELINE COMPLETADO ===")


if __name__ == "__main__":
    main()
