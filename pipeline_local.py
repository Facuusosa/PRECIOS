"""
Pipeline LOCAL para Brujula de Precios.

Corre en la PC de Facu (Programador de tareas de Windows) cada manana. Reemplaza al
cron de Railway: aca los scrapers funcionan porque usan la IP de casa (Maxiconsumo
bloquea IPs de datacenter, por eso fallaba en la nube).

Secuencia:
  1. Corre los 8 scrapers (3 mayoristas + 5 cadenas) via sus wrappers (que ya
     manejan cookies de MaxiCarrefour y el enriquecimiento de Maxiconsumo).
  2. Regenera el catalogo unificado consolidado con todas las fuentes.
  3. Chequeo anti-reciclaje: si el total de productos cae mucho o una fuente queda en
     cero, NO pushea y avisa (evita publicar datos rotos/viejos en silencio).
  4. Gate de verificacion en vivo (top 20 ABC=A vs la web de cada mayorista).
  5. git push -> Vercel redeploy automatico.

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
# Sin PYTHONUNBUFFERED, un crash duro de un scraper (curl_cffi es extension C)
# pierde el buffer entero de la pipe: 8 dias de "ERROR EN SCRAPER MAXICONSUMO"
# sin una sola linea de causa en el log (incidente 02-09/07/2026).
os.environ["PYTHONUNBUFFERED"] = "1"

RAIZ = Path(__file__).resolve().parent
BRUJULA_DIR = RAIZ / "BRUJULA-DE-PRECIOS"
CATALOGO = BRUJULA_DIR / "data" / "processed" / "catalogo_unificado.json"
CAIDA_MAX = 0.15  # si el total de productos cae mas que esto, no se publica

# NTFY_TOPIC (push al celular) vive en .env, no en el ambiente del task scheduler
try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except ImportError:
    pass


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


ALERTAS_MD = RAIZ / "data" / "quality" / "ALERTA.md"
VEREDICTO_MD = RAIZ / "data" / "quality" / "VEREDICTO.md"
HISTORIAL_CSV = RAIZ / "data" / "quality" / "historial_corridas.csv"
FUENTES = ("yaguar", "maxicarrefour", "maxiconsumo", "nini", "coto", "carrefour", "dia", "masonline", "jumbo")

# Estado de la corrida para el veredicto final (se escribe SIEMPRE via atexit,
# incluso si un sys.exit() corta el pipeline a mitad de camino)
_corrida = {"fase": "inicio", "scrapers": {}, "alertas": [], "notas": []}


def _toast(titulo, msg):
    """Notificacion nativa de Windows (sin dependencias). Best-effort: si falla,
    quedan el beep y ALERTA.md."""
    guion = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime] | Out-Null; "
        "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$n = $t.GetElementsByTagName('text'); "
        f"$n.Item(0).AppendChild($t.CreateTextNode('{titulo}')) | Out-Null; "
        f"$n.Item(1).AppendChild($t.CreateTextNode('{msg}')) | Out-Null; "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'Brujula Pipeline').Show([Windows.UI.Notifications.ToastNotification]::new($t))"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-Command", guion],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _ntfy(msg, accion=""):
    """Push al celular via ntfy.sh. Opt-in: sin NTFY_TOPIC en .env no hace nada.
    Gratis y sin cuenta — resuelve que el toast/beep de las 10am nadie los ve.
    Best-effort igual que el toast."""
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic:
        return
    try:
        import urllib.request
        cuerpo = msg + (f"\nAccion: {accion}" if accion else "")
        req = urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=cuerpo.encode("utf-8"),
            headers={"Title": "Brujula: pipeline con problemas",
                     "Priority": "high", "Tags": "warning"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def alertar(msg, accion=""):
    """Alerta visible: ALERTA.md (lo lee Claude en /inicio-sesion) + toast +
    push ntfy (opt-in) + beep + log. Punto unico de notificacion.
    """
    log(f"ALERTA: {msg}")
    _corrida["alertas"].append(msg)
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    entrada = f"\n## {ts} — {msg}\n"
    if accion:
        entrada += f"Accion sugerida: {accion}\n"
    # Insertar ANTES de '## Resueltas': con append al final, las alertas nuevas
    # quedaban debajo de las resueltas (paso del 13 al 15/07/2026). Si el read
    # falla (lock transitorio de OneDrive), caer al append viejo — reescribir el
    # archivo con contenido vacio borraria todo el historial de alertas.
    try:
        contenido = ALERTAS_MD.read_text(encoding="utf-8")
        marca = "\n## Resueltas"
        if marca in contenido:
            contenido = contenido.replace(marca, entrada + marca, 1)
        else:
            contenido += entrada
        ALERTAS_MD.write_text(contenido, encoding="utf-8")
    except OSError:
        try:
            with open(ALERTAS_MD, "a", encoding="utf-8") as f:
                f.write(entrada)
        except OSError:
            pass
    _toast("Brujula: pipeline con problemas", msg.replace("'", ""))
    _ntfy(msg, accion)
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


def sanidad_outputs():
    """Registros vs unicos del output mas reciente de cada fuente.

    El bug de Yaguar del 25/06-10/07 (34.886 registros = 5.137 unicos por paginas
    repetidas del rate-limit) fue invisible 2 semanas porque nadie comparaba
    registros contra unicos. Este check lo atrapa en la primera corrida."""
    resultados = {}
    for may in ("yaguar", "maxicarrefour", "maxiconsumo", "nini", "coto", "carrefour", "dia", "masonline", "jumbo"):
        carpeta = RAIZ / "targets" / may
        outputs = [f for f in sorted(carpeta.glob(f"output_{may}_*.json"))
                   if "raw" not in f.stem and "enriched" not in f.stem]
        if not outputs:
            continue
        ultimo = outputs[-1]
        try:
            with open(ultimo, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            alertar(f"Output de {may} ilegible ({ultimo.name}): {e}",
                    "posible doble scraper concurrente (regla 07) — revisar procesos")
            continue
        prods = data if isinstance(data, list) else data.get("productos", [])
        claves = set()
        for p in prods:
            clave = str(p.get("sku") or p.get("ean") or p.get("nombre") or "").strip()
            if clave:
                claves.add(clave)
        registros, unicos = len(prods), len(claves)
        con_precio = sum(1 for p in prods if p.get("precio", 0) > 0)
        resultados[may] = {"archivo": ultimo.name, "registros": registros,
                           "unicos": unicos, "con_precio": con_precio}
        if registros > 0 and unicos < registros * 0.95:
            alertar(f"Output de {may} con {registros - unicos} duplicados "
                    f"({registros} registros vs {unicos} unicos) — scraper repitiendo paginas",
                    "misma firma que el bug Yaguar 25/06-10/07: revisar paginacion/rate-limit")
        if registros > 0 and con_precio < registros * 0.5:
            alertar(f"Output de {may} con solo {con_precio}/{registros} precios > 0 — "
                    f"sesion sin acceso a precios (firma data-price private, 10/07)",
                    "renovar cookies con click MANUAL: python scripts/renovar_cookies_carrefour.py --force")
    return resultados


def registrar_historial():
    """Una fila por corrida -> historial_corridas.csv (append, nunca se pisa).

    VEREDICTO.md se sobreescribe en cada corrida: sin esto no hay forma barata de
    ver rachas ("MCF fallo 3 corridas seguidas") ni degradacion lenta de conteos.
    """
    ok = _corrida.get("scrapers", {})
    conteos = _corrida.get("conteos_dict", {})
    fila = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        _corrida["fase"],
        ";".join(m for m, v in ok.items() if v),
        ";".join(m for m, v in ok.items() if not v),
        str(conteos.get("total", "")),
    ] + [str(conteos.get(m, "")) for m in FUENTES] + [str(len(_corrida["alertas"]))]
    try:
        nuevo = not HISTORIAL_CSV.exists()
        with open(HISTORIAL_CSV, "a", encoding="utf-8") as f:
            if nuevo:
                f.write("timestamp,fase,scrapers_ok,scrapers_fallo,total,"
                        + ",".join(FUENTES) + ",n_alertas\n")
            f.write(",".join(fila) + "\n")
    except OSError:
        pass


def fallos_consecutivos(may):
    """Corridas consecutivas hacia atras en que 'may' fallo, segun el historial.
    La corrida actual todavia no esta en el CSV (se escribe via atexit)."""
    try:
        lineas = HISTORIAL_CSV.read_text(encoding="utf-8").strip().splitlines()[1:]
    except OSError:
        return 0
    racha = 0
    for linea in reversed(lineas):
        campos = linea.split(",")
        if len(campos) < 4:
            break
        if may in campos[3].split(";"):
            racha += 1
        else:
            break
    return racha


def escribir_veredicto():
    """Estado compacto de la ultima corrida -> VEREDICTO.md. Registrado via atexit:
    se escribe SIEMPRE, incluso si un sys.exit() corta el pipeline a mitad de camino.
    Lo lee Claude automaticamente al inicio de cada sesion (hook SessionStart)."""
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = [f"# VEREDICTO ultima corrida — {ts}", ""]
    lineas.append(f"**Fase alcanzada:** {_corrida['fase']}")
    if _corrida["fase"] != "completado":
        lineas.append("(la corrida NO llego al final — ver alertas y log)")
    lineas.append("")
    if _corrida["scrapers"]:
        lineas.append("**Scrapers:** " + " | ".join(
            f"{m}: {'OK' if v else 'FALLO'}" for m, v in _corrida["scrapers"].items()))
    if _corrida.get("conteos"):
        lineas.append(f"**Catalogo:** {_corrida['conteos']}")
    if _corrida.get("sanidad"):
        lineas.append("")
        lineas.append("**Sanidad de outputs (registros/unicos/con precio):**")
        for may, s in _corrida["sanidad"].items():
            marca = " <- DUPLICADOS" if s["unicos"] < s["registros"] * 0.95 else ""
            if s.get("con_precio", s["registros"]) < s["registros"] * 0.5:
                marca += " <- SIN PRECIOS (sesion muerta)"
            lineas.append(f"- {may}: {s['registros']}/{s['unicos']}/{s.get('con_precio','?')} ({s['archivo']}){marca}")
    lineas.append("")
    if _corrida["alertas"]:
        lineas.append("**Alertas de esta corrida:**")
        for a in _corrida["alertas"]:
            lineas.append(f"- {a}")
    else:
        lineas.append("Sin alertas en esta corrida.")
    for n in _corrida["notas"]:
        lineas.append(f"- {n}")
    try:
        VEREDICTO_MD.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    except OSError:
        pass
    registrar_historial()


def contar_por_fuente():
    """Productos con precio por fuente en el catalogo actual (para anti-reciclaje)."""
    conteo = {"total": 0, "yaguar": 0, "maxicarrefour": 0, "maxiconsumo": 0, "nini": 0,
              "coto": 0, "carrefour": 0, "dia": 0, "masonline": 0, "jumbo": 0}
    if not CATALOGO.exists():
        return conteo
    with open(CATALOGO, encoding="utf-8") as f:
        data = json.load(f)
    prods = data if isinstance(data, list) else data.get("productos", [])
    conteo["total"] = len(prods)
    for p in prods:
        precios = p.get("precios", {})
        for may in ("yaguar", "maxicarrefour", "maxiconsumo", "nini", "coto", "carrefour", "dia", "masonline", "jumbo"):
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
    for mayorista in ("yaguar", "maxicarrefour", "maxiconsumo", "nini", "coto", "carrefour", "dia", "masonline", "jumbo"):
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
    import atexit
    atexit.register(escribir_veredicto)
    log("=== PIPELINE LOCAL BRUJULA ===")
    antes = contar_por_fuente()
    log(f"Catalogo actual: {antes['total']} prods "
        f"(Y={antes['yaguar']} MC={antes['maxicarrefour']} MCO={antes['maxiconsumo']} NI={antes['nini']} "
        f"C={antes['coto']} CF={antes['carrefour']} D={antes['dia']} "
        f"MAS={antes['masonline']} JUM={antes['jumbo']})")

    ok = {
        # MaxiCarrefour primero: es el unico que puede pedir un click manual
        # (renovacion de cookies) — asi Facu lo resuelve al toque y deja el resto
        # de los scrapers (sin intervencion humana) corriendo desatendido.
        "maxicarrefour": run_scraper("scrape_maxicarrefour.py"),
        "yaguar":        run_scraper("scrape_yaguar.py"),
        "maxiconsumo":   run_scraper("scrape_maxiconsumo.py"),
        # Nini: cuenta PRESTADA por un tercero (ver .claude/rules/02-scrapers.md) --
        # scraper de SOLO LECTURA, nunca confirma/anula pedidos.
        "nini":          run_scraper("scrape_nini.py"),
        "coto":          run_scraper("scrape_coto.py"),
        "carrefour":     run_scraper("scrape_carrefour.py"),
        "dia":           run_scraper("scrape_dia.py"),
        "masonline":     run_scraper("scrape_masonline.py"),
        "jumbo":         run_scraper("scrape_jumbo.py"),
    }
    log(f"Scrapers OK: {sum(ok.values())}/{len(ok)}")
    _corrida["fase"] = "scrapers"
    _corrida["scrapers"] = dict(ok)
    for may, exito in ok.items():
        if not exito:
            racha = fallos_consecutivos(may) + 1  # +1: la corrida actual
            if racha >= 3:
                alertar(f"Scraper {may} FALLO -- {racha} corridas seguidas (CRONICO)",
                        "no es un fallo puntual: revisar el patron en data/quality/historial_corridas.csv y pipeline_local.log")
            else:
                alertar(f"Scraper {may} FALLO hoy",
                        "revisar data/quality/pipeline_local.log — si es MCF, probar scripts/renovar_cookies_carrefour.py --force")
    if sum(ok.values()) == 0:
        log(f"ERROR: fallaron los {len(ok)} scrapers - el catalogo no se toca")
        sys.exit(1)

    # Sanidad de outputs: duplicados masivos = scraper repitiendo paginas
    _corrida["sanidad"] = sanidad_outputs()

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
        f"(Y={despues['yaguar']} MC={despues['maxicarrefour']} MCO={despues['maxiconsumo']} NI={despues['nini']} "
        f"C={despues['coto']} CF={despues['carrefour']} D={despues['dia']} "
        f"MAS={despues['masonline']} JUM={despues['jumbo']})")
    _corrida["fase"] = "catalogo regenerado"
    _corrida["conteos_dict"] = despues
    _corrida["conteos"] = (f"{despues['total']} prods (Y={despues['yaguar']} "
                           f"MC={despues['maxicarrefour']} MCO={despues['maxiconsumo']} NI={despues['nini']} "
                           f"C={despues['coto']} CF={despues['carrefour']} D={despues['dia']} "
                           f"MAS={despues['masonline']} JUM={despues['jumbo']})")

    if antes["total"] > 0:
        caida = (antes["total"] - despues["total"]) / antes["total"]
        if caida > CAIDA_MAX:
            alertar(f"El total de productos cayo {caida:.0%} (>{CAIDA_MAX:.0%}) - NO se publica",
                    "revisar scrapers en data/quality/pipeline_local.log")
            sys.exit(1)
    # Minimos historicos por fuente: si cae por debajo, algo salio mal.
    # coto/carrefour/dia: son matches EAN contra el catalogo (coto 4.116, dia 1.832
    # medidos el 06/07/2026), NO el total scrapeado — el minimo va sobre lo que entra al catalogo
    # masonline/jumbo: medido 20/07/2026 (primera corrida real) - 2.726 y 3.381
    # matches EAN contra el catalogo respectivamente, mismo margen ~65% que dia
    # nini: SIN CALIBRAR a proposito -- no tiene EAN propio (matching por
    # aprendizaje fuzzy, arranque en frio), el numero de matches crece con cada
    # corrida. Agregar un minimo aca recien cuando el conteo real se estabilice
    # (ver con_nini en el log de actualizar_catalogo.py de varias corridas).
    minimos_fuente = {"yaguar": 4000, "maxicarrefour": 3000, "maxiconsumo": 3000,
                      "coto": 3000, "carrefour": 3000, "dia": 1200,
                      "masonline": 1800, "jumbo": 2200}
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
    _corrida["fase"] = "completado"
    log("=== PIPELINE COMPLETADO ===")


if __name__ == "__main__":
    main()
