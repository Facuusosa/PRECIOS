#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renueva automaticamente las cookies de MaxiCarrefour (PHPSESSID + cf_clearance).
Usa Playwright para navegar el flujo real de login (no hay contrasena — usa CUIT + datos personales).

Flujo real:
  comerciante.carrefour.com.ar -> Ingresar -> COMERCIO o EMPRENDIMIENTO
  -> Seleccionar Provincia -> Seleccionar Sucursal
  -> Llenar Nombre / CUIT / Telefono / Email -> Ingresar

Variables requeridas en .env:
  CARREFOUR_CUIT         CUIT o DNI del comercio
  CARREFOUR_NOMBRE       Nombre y apellido
  CARREFOUR_EMAIL        Email registrado
  CARREFOUR_TELEFONO     Telefono de contacto
  CARREFOUR_PROVINCIA    Label exacto del dropdown (ej: "CABA")
  CARREFOUR_SUCURSAL     Label exacto del dropdown (ej: "CARREFOUR MAXI AVELLANEDA...")

Salida: actualiza CARREFOUR_PHPSESSID, CARREFOUR_CF_CLEARANCE y CARREFOUR_COOKIE_DATE en .env
"""

import os
import sys
import re
import random
import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

CARREFOUR_CUIT      = os.getenv("CARREFOUR_CUIT", "")
CARREFOUR_NOMBRE    = os.getenv("CARREFOUR_NOMBRE", "")
CARREFOUR_EMAIL     = os.getenv("CARREFOUR_EMAIL", "")
CARREFOUR_TELEFONO  = os.getenv("CARREFOUR_TELEFONO", "")
CARREFOUR_PROVINCIA = os.getenv("CARREFOUR_PROVINCIA", "")
CARREFOUR_SUCURSAL  = os.getenv("CARREFOUR_SUCURSAL", "")

BASE_URL = "https://comerciante.carrefour.com.ar"

CAMPOS_REQUERIDOS = {
    "CARREFOUR_CUIT":      CARREFOUR_CUIT,
    "CARREFOUR_NOMBRE":    CARREFOUR_NOMBRE,
    "CARREFOUR_EMAIL":     CARREFOUR_EMAIL,
    "CARREFOUR_TELEFONO":  CARREFOUR_TELEFONO,
    "CARREFOUR_PROVINCIA": CARREFOUR_PROVINCIA,
    "CARREFOUR_SUCURSAL":  CARREFOUR_SUCURSAL,
}


def _actualizar_env(key: str, value: str):
    """Reemplaza o agrega una variable en el .env."""
    contenido = ENV_PATH.read_text(encoding="utf-8")
    patron = rf"^{re.escape(key)}=.*$"
    nueva_linea = f"{key}={value}"
    if re.search(patron, contenido, flags=re.MULTILINE):
        contenido = re.sub(patron, nueva_linea, contenido, flags=re.MULTILINE)
    else:
        contenido = contenido.rstrip("\n") + f"\n{nueva_linea}\n"
    ENV_PATH.write_text(contenido, encoding="utf-8")


def cookies_necesitan_renovacion() -> bool:
    """True si la fecha de las cookies es >25 dias o no existe."""
    fecha_str = os.getenv("CARREFOUR_COOKIE_DATE", "")
    if not fecha_str:
        return True
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
        dias = (datetime.date.today() - fecha).days
        if dias > 25:
            print(f"Cookies tienen {dias} dias de antiguedad (limite: 25) -- renovando...")
            return True
        print(f"Cookies tienen {dias} dias -- dentro del limite.")
        return False
    except ValueError:
        return True


def verificar_cookies_vigentes() -> bool:
    """Verifica si las cookies actuales siguen siendo validas (GET rapido a /products)."""
    try:
        from curl_cffi import requests as cf_requests
    except ImportError:
        try:
            import requests as cf_requests
        except ImportError:
            return False

    phpsessid   = os.getenv("CARREFOUR_PHPSESSID", "")
    cf_clearance = os.getenv("CARREFOUR_CF_CLEARANCE", "")
    if not phpsessid:
        return False

    try:
        session = cf_requests.Session()
        session.cookies.update({"PHPSESSID": phpsessid, "cf_clearance": cf_clearance})
        r = session.get(f"{BASE_URL}/products", params={
            "currentUrl": "sec/almacen", "filters": "", "orderBy": "default",
            "currentPage": 1, "itemsPerPage": 1, "method": "countProducts"
        }, timeout=15)
        if r.status_code in (401, 403) or "/login" in r.url:
            return False
        return r.status_code == 200 and r.text.strip().isdigit()
    except Exception:
        return False


def renovar_con_playwright(headless: bool = True) -> bool:
    """Login real via Playwright. Retorna True si obtuvo cookies validas."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("ERROR: playwright no instalado. Correr: pip install playwright && playwright install chromium")
        return False

    print(f"Iniciando Playwright (headless={headless})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="es-AR",
            timezone_id="America/Argentina/Buenos_Aires",
        )
        page = context.new_page()
        # Ocultar flag de automatizacion — señal principal que detecta Cloudflare
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            # 1. Navegar al sitio
            print("  Navegando a comerciante.carrefour.com.ar...")
            page.goto(BASE_URL, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=20000)

            # 2. Abrir el modal de login (div con onclick="openDerivator()")
            print("  Abriendo modal de login...")
            page.locator("[onclick='openDerivator()']").first.click(timeout=10000)
            page.wait_for_selector("#step1", state="visible", timeout=8000)

            # 3. Elegir COMERCIO o EMPRENDIMIENTO (div#business llama a goToStep2())
            print("  Seleccionando COMERCIO / EMPRENDIMIENTO...")
            page.locator("#business").click(timeout=8000)
            page.wait_for_selector("#step2", state="visible", timeout=8000)
            page.wait_for_timeout(500)

            # 4. Seleccionar Provincia
            print(f"  Seleccionando provincia: {CARREFOUR_PROVINCIA}")
            page.locator("#region").select_option(CARREFOUR_PROVINCIA, timeout=8000)
            # Esperar que carguen las sucursales (AJAX dinamico)
            page.wait_for_timeout(2500)

            # 5. Seleccionar Sucursal (match parcial — el label puede tener dirección extra)
            print(f"  Seleccionando sucursal: {CARREFOUR_SUCURSAL[:50]}...")
            page.wait_for_function(
                "document.querySelector('#seller').options.length > 1",
                timeout=8000
            )
            opciones = page.locator("#seller option").all()
            valor_sucursal = None
            for opt in opciones:
                texto = (opt.text_content() or "").strip()
                if CARREFOUR_SUCURSAL.lower() in texto.lower():
                    valor_sucursal = opt.get_attribute("value")
                    print(f"  Match: '{texto}'")
                    break
            if not valor_sucursal:
                raise Exception(f"No se encontro la sucursal '{CARREFOUR_SUCURSAL}' en el dropdown. Opciones disponibles: {[opt.text_content() for opt in opciones[:5]]}")
            page.locator("#seller").select_option(value=valor_sucursal, timeout=5000)
            page.wait_for_timeout(500)

            # 6. Llenar datos personales con IDs exactos
            print("  Llenando formulario...")
            page.locator("#user-name").fill(CARREFOUR_NOMBRE, timeout=5000)
            page.locator("#user-cuit").fill(CARREFOUR_CUIT, timeout=5000)
            page.locator("#user-phone").fill(CARREFOUR_TELEFONO, timeout=5000)
            page.locator("#user-email").fill(CARREFOUR_EMAIL, timeout=5000)

            # 7. Marcar "Recordarme"
            try:
                checkbox = page.locator("#remember")
                if not checkbox.is_checked():
                    checkbox.check()
            except PWTimeout:
                pass

            # 8. Click Ingresar (submit) — #btn_step2 es el botón exacto del formulario
            print("  Enviando formulario...")
            # Delay humano — evita deteccion por velocidad de llenado
            page.wait_for_timeout(1500 + int(random.random() * 2000))
            page.locator("#btn_step2").click(timeout=8000)
            page.wait_for_load_state("networkidle", timeout=25000)

            # 9. Verificar que se logro ingresar
            current_url = page.url
            print(f"  URL post-login: {current_url}")
            if "login" in current_url.lower():
                print("  WARN: Puede que el login fallo (URL contiene 'login')")

            # 10. Extraer cookies
            cookies = context.cookies()
            phpsessid    = next((c["value"] for c in cookies if c["name"] == "PHPSESSID"), "")
            cf_clearance = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")

            if not phpsessid:
                print("  No se obtuvo PHPSESSID -- login fallido o Cloudflare bloqueo")
                # Tomar screenshot para debug
                screenshot_path = BASE_DIR / "data" / "quality" / "carrefour_login_debug.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                print(f"  Screenshot guardado: {screenshot_path}")
                browser.close()
                return False

            browser.close()

            # 11. Escribir al .env
            _actualizar_env("CARREFOUR_PHPSESSID", phpsessid)
            if cf_clearance:
                _actualizar_env("CARREFOUR_CF_CLEARANCE", cf_clearance)
            fecha_hoy = datetime.date.today().isoformat()
            _actualizar_env("CARREFOUR_COOKIE_DATE", fecha_hoy)
            # Si corre en Railway, persistir env vars via API para que sobrevivan al reinicio del container
            _sincronizar_railway(phpsessid, cf_clearance or "", fecha_hoy)

            print(f"  OK: PHPSESSID obtenido ({phpsessid[:16]}...)")
            return True

        except PWTimeout as e:
            print(f"  Timeout: {e}")
            try:
                screenshot_path = BASE_DIR / "data" / "quality" / "carrefour_login_debug.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                print(f"  Screenshot guardado: {screenshot_path}")
            except Exception:
                pass
            browser.close()
            return False

        except Exception as e:
            print(f"  Error inesperado: {e}")
            try:
                screenshot_path = BASE_DIR / "data" / "quality" / "carrefour_login_debug.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                print(f"  Screenshot guardado: {screenshot_path}")
            except Exception:
                pass
            browser.close()
            return False


def _sincronizar_railway(phpsessid: str, cf_clearance: str, fecha: str):
    """Persiste las cookies renovadas en Railway env vars via API. Solo actua si hay RAILWAY_TOKEN."""
    import urllib.request, json as _json
    token        = os.getenv("RAILWAY_TOKEN", "")
    project_id   = os.getenv("RAILWAY_PROJECT_ID", "")
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID", "")
    if not token or not project_id or not environment_id:
        return
    mutation = "mutation($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }"
    payload = _json.dumps({
        "query": mutation,
        "variables": {"input": {
            "projectId": project_id,
            "environmentId": environment_id,
            "variables": {
                "CARREFOUR_PHPSESSID":    phpsessid,
                "CARREFOUR_CF_CLEARANCE": cf_clearance,
                "CARREFOUR_COOKIE_DATE":  fecha,
            },
        }}
    }).encode()
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print("  Railway: env vars actualizadas correctamente.")
    except Exception as e:
        print(f"  Railway sync (no critico): {e}")



def main():
    print("=" * 55)
    print("RENOVACION DE COOKIES MAXICARREFOUR")
    print("=" * 55)

    # Verificar campos requeridos
    faltantes = [k for k, v in CAMPOS_REQUERIDOS.items() if not v]
    if faltantes:
        print("ERROR: Faltan estas variables en .env:")
        for f in faltantes:
            print(f"  {f}=")
        print("\nAgregalas con los datos reales de tu cuenta de MaxiCarrefour.")
        sys.exit(1)

    # Si las cookies son recientes, verificar que siguen activas
    if not cookies_necesitan_renovacion():
        print("Verificando que las cookies actuales siguen activas...")
        if verificar_cookies_vigentes():
            print("OK: Cookies vigentes, no es necesario renovar.")
            sys.exit(0)
        else:
            print("Cookies actuales invalidas -- renovando de todas formas...")

    # Intento 1: headless
    print("\nIntentando login headless...")
    if renovar_con_playwright(headless=True):
        print("\nCookies renovadas correctamente (headless).")
        print(f"Fecha guardada: {datetime.date.today().isoformat()}")
        sys.exit(0)

    # Intento 2: visible (si Cloudflare bloquea headless)
    print("\nHeadless fallo -- intentando con navegador visible...")
    print("(El navegador se va a abrir, no lo cierres)")
    if renovar_con_playwright(headless=False):
        print("\nCookies renovadas correctamente (modo visible).")
        print(f"Fecha guardada: {datetime.date.today().isoformat()}")
        sys.exit(0)

    print("\nNo se pudo renovar automaticamente.")
    print("Opciones manuales:")
    print("  1. Loguearse en comerciante.carrefour.com.ar")
    print("  2. F12 -> Application -> Cookies -> copiar PHPSESSID y cf_clearance")
    print("  3. Actualizar CARREFOUR_PHPSESSID y CARREFOUR_CF_CLEARANCE en .env")
    print("\nRevisa el screenshot en data/quality/carrefour_login_debug.png para ver que fallo.")
    sys.exit(1)


if __name__ == "__main__":
    main()
