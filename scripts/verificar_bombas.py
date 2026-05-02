"""
Verificacion dinamica de precios de las top N bombas del catalogo.
- Yaguar: WooCommerce API con login curl_cffi (HTTP puro, sin browser)
- MaxiCarrefour: busca en output JSON local mas reciente (sin browser, sin cookies)
- Maxiconsumo: curl_cffi con impersonacion Safari (igual que el scraper)

Uso: python scripts/verificar_bombas.py [N]  (default: 10)
Salida: resumen en consola + JSON en data/quality/
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CATALOGO = BASE_DIR / "BRUJULA-DE-PRECIOS" / "data" / "processed" / "catalogo_unificado.json"
TARGETS = BASE_DIR / "targets"
OUTPUT_DIR = BASE_DIR / "data" / "quality"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DIFF_WARN = 0.05
DIFF_ERROR = 0.20


def cargar_catalogo():
    with open(CATALOGO, encoding="utf-8") as f:
        return json.load(f)


def get_bombas(catalogo, n):
    def diferencial(p):
        precios = [v for v in p["precios"].values() if v and v > 0]
        return max(precios) / min(precios) if len(precios) >= 2 else 1.0

    multi = [p for p in catalogo if sum(1 for v in p["precios"].values() if v and v > 0) >= 2]
    return sorted(multi, key=diferencial, reverse=True)[:n]


def verificar_yaguar(nombre):
    try:
        from curl_cffi import requests as curl_requests
        from bs4 import BeautifulSoup

        username = os.getenv("YAGUAR_USERNAME")
        password = os.getenv("YAGUAR_PASSWORD")
        if not username or not password:
            return -1.0

        BASE_URL = "https://yaguar.com.ar"
        LOGIN_URL = f"{BASE_URL}/login/"
        IMPERSONATE = "safari15_3"
        HEADERS = {
            "accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "accept-language": "es-ES,es;q=0.9",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
        }

        session = curl_requests.Session()
        r1 = session.get(LOGIN_URL, headers=HEADERS, impersonate=IMPERSONATE, timeout=15)
        soup = BeautifulSoup(r1.text, "html.parser")
        form = soup.find("form", {"method": "post"})
        if not form:
            return -1.0

        payload = {
            inp.get("name", ""): inp.get("value", "")
            for inp in form.find_all("input")
            if inp.get("name")
        }
        payload["username"] = username
        payload["password"] = password
        payload["login"] = "Ingresar"

        r2 = session.post(
            LOGIN_URL,
            data=payload,
            headers={**HEADERS, "Referer": LOGIN_URL},
            impersonate=IMPERSONATE,
            timeout=15,
        )
        if "wordpress_logged_in" not in str(r2.cookies):
            return -1.0

        # WooCommerce API: primeras 3 palabras del nombre para mejor match
        palabras = "+".join(nombre.split()[:3])
        api_url = f"{BASE_URL}/wp-json/wc/store/v1/products?search={palabras}&per_page=5"
        r3 = session.get(
            api_url,
            headers={**HEADERS, "Referer": BASE_URL + "/"},
            impersonate=IMPERSONATE,
            timeout=15,
        )
        if r3.status_code != 200:
            return -1.0

        for p in r3.json():
            try:
                # WooCommerce con currency_minor_unit=0 devuelve precio en pesos directamente
                precio = float(p.get("prices", {}).get("price", "0"))
                if precio > 10:
                    return precio
            except (ValueError, TypeError):
                continue
        return -1.0
    except Exception:
        return -1.0


def verificar_maxicarrefour_local(nombre, ean):
    carrefour_dir = TARGETS / "maxicarrefour"
    outputs = sorted(carrefour_dir.glob("output_maxicarrefour_*.json"), reverse=True)
    if not outputs:
        return -1.0, "sin_output"

    latest = outputs[0]
    edad_horas = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds() / 3600
    if edad_horas > 48:
        return -1.0, f"output_viejo_{int(edad_horas)}h"

    with open(latest, encoding="utf-8") as f:
        productos = json.load(f)

    if ean:
        for p in productos:
            if p.get("ean") == ean and p.get("precio", 0) > 0:
                return float(p["precio"]), "por_ean"

    palabras = set(nombre.lower().split()[:3])
    for p in productos:
        if not p.get("precio", 0):
            continue
        if len(palabras & set(p.get("nombre", "").lower().split())) >= 2:
            return float(p["precio"]), "por_nombre"

    return -1.0, "no_encontrado"


def verificar_maxiconsumo(nombre):
    try:
        sys.path.insert(0, str(TARGETS / "maxiconsumo"))
        from verificar_precio import buscar_producto

        resultados = buscar_producto(nombre)
        return resultados[0]["precio"] if resultados else -1.0
    except Exception:
        return -1.0


def evaluar_diferencia(precio_catalogo, precio_real):
    if precio_real <= 0:
        return "NO_ENCONTRADO"
    diff = abs(precio_real - precio_catalogo) / precio_catalogo
    if diff <= DIFF_WARN:
        return "OK"
    if diff <= DIFF_ERROR:
        return f"DIFF_{int(diff * 100)}pct"
    return f"ERROR_{int(diff * 100)}pct"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"Verificacion top {n} bombas | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    catalogo = cargar_catalogo()
    bombas = get_bombas(catalogo, n)
    resultados = []
    ok_count = 0

    for i, bomba in enumerate(bombas, 1):
        nombre = bomba["nombre_display"]
        ean = bomba.get("ean", "")
        precios_cat = {k: v for k, v in bomba["precios"].items() if v and v > 0}

        print(f"\n[{i}/{n}] {nombre}")
        print(f"  Catalogo: {' | '.join(f'{k} ${v:,.0f}' for k, v in precios_cat.items())}")

        verificaciones = {}

        if "yaguar" in precios_cat:
            precio_real = verificar_yaguar(nombre)
            estado = evaluar_diferencia(precios_cat["yaguar"], precio_real)
            verificaciones["yaguar"] = {"precio_catalogo": precios_cat["yaguar"], "precio_real": precio_real, "estado": estado}
            precio_str = f"${precio_real:,.0f}" if precio_real > 0 else "N/A"
            print(f"  Yaguar:        ${precios_cat['yaguar']:,.0f} -> {precio_str} | {estado}")
            time.sleep(0.5)

        if "maxicarrefour" in precios_cat:
            precio_real, metodo = verificar_maxicarrefour_local(nombre, ean)
            estado = evaluar_diferencia(precios_cat["maxicarrefour"], precio_real)
            verificaciones["maxicarrefour"] = {"precio_catalogo": precios_cat["maxicarrefour"], "precio_real": precio_real, "estado": estado, "metodo": metodo}
            precio_str = f"${precio_real:,.0f}" if precio_real > 0 else f"N/A ({metodo})"
            print(f"  MaxiCarrefour: ${precios_cat['maxicarrefour']:,.0f} -> {precio_str} | {estado}")

        if "maxiconsumo" in precios_cat:
            precio_real = verificar_maxiconsumo(nombre)
            estado = evaluar_diferencia(precios_cat["maxiconsumo"], precio_real)
            verificaciones["maxiconsumo"] = {"precio_catalogo": precios_cat["maxiconsumo"], "precio_real": precio_real, "estado": estado}
            precio_str = f"${precio_real:,.0f}" if precio_real > 0 else "N/A"
            print(f"  Maxiconsumo:   ${precios_cat['maxiconsumo']:,.0f} -> {precio_str} | {estado}")
            time.sleep(0.3)

        verificadas = [v for v in verificaciones.values() if v["estado"] != "NO_ENCONTRADO"]
        todas_ok = all(v["estado"] == "OK" for v in verificadas)
        if verificadas and todas_ok:
            ok_count += 1

        resultados.append({"nombre": nombre, "ean": ean, "precios_catalogo": precios_cat, "verificaciones": verificaciones})

    print("\n" + "=" * 70)
    print(f"RESUMEN: {ok_count}/{n} bombas sin discrepancias")

    errores = [
        f"  {r['nombre'][:40]} | {fuente} | {v['estado']}"
        for r in resultados
        for fuente, v in r["verificaciones"].items()
        if v["estado"].startswith("DIFF") or v["estado"].startswith("ERROR")
    ]
    if errores:
        print("Diferencias detectadas:")
        for e in errores:
            print(e)
    else:
        print("Sin diferencias significativas. Datos frescos y correctos.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"verificacion_bombas_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {"timestamp": timestamp, "total": n, "ok": ok_count, "resultados": resultados},
            f, ensure_ascii=False, indent=2
        )
    print(f"Reporte guardado: {output_file}")

    return ok_count >= int(n * 0.8)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
