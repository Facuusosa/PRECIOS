#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renueva automaticamente las cookies de MaxiCarrefour (PHPSESSID + cf_clearance).

Modos en orden de prioridad:
1. CapSolver API (CAPSOLVER_API_KEY en .env) -- 100% automatico, sin presencia humana
2. Chrome real con perfil persistente -- 1 click humano, se guarda por 30 dias
3. Manual -- instrucciones para copiar cookies del browser

Site key reCAPTCHA Enterprise de comerciante.carrefour.com.ar:
  6LdiZHIqAAAAAJO8Gn9RbfC6bMckPmMXgoBrqfmJ

Variables requeridas en .env:
  CARREFOUR_CUIT, CARREFOUR_NOMBRE, CARREFOUR_EMAIL,
  CARREFOUR_TELEFONO, CARREFOUR_PROVINCIA, CARREFOUR_SUCURSAL

Opcional:
  CAPSOLVER_API_KEY -- API key de capsolver.com para 100% automatico
"""

import os
import sys
import re
import subprocess
import time
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
CAPSOLVER_API_KEY   = os.getenv("CAPSOLVER_API_KEY", "")

BASE_URL         = "https://comerciante.carrefour.com.ar"
RECAPTCHA_KEY    = "6LdiZHIqAAAAAJO8Gn9RbfC6bMckPmMXgoBrqfmJ"
CHROME_EXE       = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR      = BASE_DIR / "data" / "carrefour_profile"
DEBUG_SCREENSHOT = BASE_DIR / "data" / "quality" / "carrefour_login_debug.png"

CAMPOS_REQUERIDOS = {
    "CARREFOUR_CUIT":      CARREFOUR_CUIT,
    "CARREFOUR_NOMBRE":    CARREFOUR_NOMBRE,
    "CARREFOUR_EMAIL":     CARREFOUR_EMAIL,
    "CARREFOUR_TELEFONO":  CARREFOUR_TELEFONO,
    "CARREFOUR_PROVINCIA": CARREFOUR_PROVINCIA,
    "CARREFOUR_SUCURSAL":  CARREFOUR_SUCURSAL,
}


# ---------------------------------------------------------------------------
# Helpers de .env
# ---------------------------------------------------------------------------

def _actualizar_env(key: str, value: str):
    contenido = ENV_PATH.read_text(encoding="utf-8")
    patron = rf"^{re.escape(key)}=.*$"
    nueva_linea = f"{key}={value}"
    if re.search(patron, contenido, flags=re.MULTILINE):
        contenido = re.sub(patron, nueva_linea, contenido, flags=re.MULTILINE)
    else:
        contenido = contenido.rstrip("\n") + f"\n{nueva_linea}\n"
    ENV_PATH.write_text(contenido, encoding="utf-8")


def _guardar_cookies(phpsessid: str, cf_clearance: str):
    _actualizar_env("CARREFOUR_PHPSESSID", phpsessid)
    if cf_clearance:
        _actualizar_env("CARREFOUR_CF_CLEARANCE", cf_clearance)
    fecha_hoy = datetime.date.today().isoformat()
    _actualizar_env("CARREFOUR_COOKIE_DATE", fecha_hoy)
    print(f"  OK: PHPSESSID ({phpsessid[:16]}...) guardado.")


def cookies_necesitan_renovacion() -> bool:
    fecha_str = os.getenv("CARREFOUR_COOKIE_DATE", "")
    if not fecha_str:
        return True
    try:
        fecha = datetime.date.fromisoformat(fecha_str)
        dias = (datetime.date.today() - fecha).days
        if dias > 25:
            print(f"Cookies tienen {dias} dias (limite: 25) -- renovando...")
            return True
        print(f"Cookies tienen {dias} dias -- dentro del limite.")
        return False
    except ValueError:
        return True


# ---------------------------------------------------------------------------
# Helpers de Playwright
# ---------------------------------------------------------------------------

def _goto_con_reintentos(page, url: str, intentos: int = 3) -> bool:
    """Un goto unico de 30s mataba el scrape del dia entero (incidente 10/07/2026:
    7 de 8 dias fallidos por timeout transitorio de Cloudflare). Reintenta con
    espera incremental antes de rendirse."""
    esperas = [10, 30]  # segundos entre intentos
    for i in range(1, intentos + 1):
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"  Intento {i}/{intentos} de navegacion fallo: {e}")
            if i < intentos:
                espera = esperas[min(i - 1, len(esperas) - 1)]
                print(f"  Esperando {espera}s antes de reintentar...")
                page.wait_for_timeout(espera * 1000)
    print(f"  Navegacion a {url} fallo tras {intentos} intentos.")
    return False


def _esta_autenticado(page) -> bool:
    """XHR en el browser actual para verificar autenticacion.

    Exige señal POSITIVA (data-price con digito), igual que _cookies_vigentes()
    del wrapper: solo descartar señales negativas validaba como "EXITOSO" sesiones
    semi-autenticadas sin precios (incidentes 10/07 y 12/07/2026 — sitio MAXI PEDIDO
    lista productos pero con data-price="private" hasta pasar el reCAPTCHA)."""
    try:
        result = page.evaluate("""
            async () => {
                try {
                    const r = await fetch(
                        '/products?currentUrl=sec/bebidas&filters=&orderBy=default&currentPage=1&itemsPerPage=1&method=productsList',
                        {headers: {'X-Requested-With': 'XMLHttpRequest'}}
                    );
                    return (await r.text()).substring(0, 5000);
                } catch(e) { return 'ERROR:' + e.message; }
            }
        """)
        if not result or result.startswith("ERROR:") or "item_card_public" in result:
            return False
        return bool(re.search(r'data-price="\d', result))
    except Exception:
        return False


def _rellenar_form(page, PWTimeout):
    """Autocompleta el formulario de login (sitio rediseñado MAXI PEDIDO).

    Dos particularidades del form nuevo (verificadas con inspeccion de DOM y
    computed styles el 15/07/2026 — causa de los fallos cronicos 03-15/07):
    1. El step2 arranca pidiendo la modalidad de entrega (#checkbox_retiro);
       sin ese click los selects de Provincia/Sucursal no se montan.
    2. Los selects e inputs tienen bounding box 0x0 (widget custom del CSS)
       aunque computedStyle diga visible — para Playwright son invisibles y
       select_option()/fill() mueren SIEMPRE por timeout, aunque el form se
       vea perfecto en pantalla. Por eso se usa force=True: saltea el chequeo
       de visibilidad pero mantiene eventos confiables via CDP (isTrusted=true).
       NO reemplazar por dispatchEvent de JS puro: isTrusted=false hace que el
       reCAPTCHA Enterprise bloquee el submit (probado el 15/07/2026).
    """
    page.locator("[onclick='openDerivator()']").first.click(timeout=10000)
    page.wait_for_selector("#step1", state="visible", timeout=8000)
    page.locator("#business").click(timeout=8000)
    page.wait_for_selector("#step2", state="visible", timeout=8000)
    page.wait_for_timeout(500)

    try:
        if page.locator("#checkbox_retiro").is_visible():
            page.locator("#checkbox_retiro").click(timeout=5000)
            page.wait_for_timeout(1500)
    except Exception:
        pass  # variante vieja del form, sin paso de modalidad

    page.locator("#region").select_option(CARREFOUR_PROVINCIA, force=True, timeout=8000)
    page.wait_for_timeout(2500)

    page.wait_for_function(
        "document.querySelector('#seller').options.length > 1", timeout=8000
    )
    # Lookup del value por texto (solo lectura — la interaccion va con force)
    valor_sucursal = page.evaluate("""
        (suc) => {
            const opt = Array.from(document.querySelector('#seller').options)
                .find(o => o.text.toLowerCase().includes(suc.toLowerCase()));
            return opt ? {value: opt.value, texto: opt.text.trim()} : null;
        }
    """, CARREFOUR_SUCURSAL)
    if not valor_sucursal:
        raise Exception(f"Sucursal '{CARREFOUR_SUCURSAL}' no encontrada en el dropdown")
    print(f"  Match sucursal: '{valor_sucursal['texto']}'")
    page.locator("#seller").select_option(value=valor_sucursal["value"], force=True, timeout=5000)
    page.wait_for_timeout(500)

    page.locator("#user-name").fill(CARREFOUR_NOMBRE, force=True)
    page.locator("#user-cuit").fill(CARREFOUR_CUIT, force=True)
    page.locator("#user-phone").fill(CARREFOUR_TELEFONO, force=True)
    page.locator("#user-email").fill(CARREFOUR_EMAIL, force=True)
    page.wait_for_timeout(400)

    try:
        checkbox = page.locator("#remember")
        if not checkbox.is_checked():
            checkbox.check(force=True, timeout=3000)
    except Exception:
        pass


def _screenshot_debug(page, etiqueta=""):
    try:
        DEBUG_SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(DEBUG_SCREENSHOT))
        print(f"  Screenshot de debug{etiqueta}: {DEBUG_SCREENSHOT}")
    except Exception:
        pass


def _autocompletar_con_reset(page, context, PWTimeout) -> bool:
    """_rellenar_form() con recuperacion del estado 'semi-adentro'.

    Desde el rediseño MAXI PEDIDO (07/2026), el perfil persistente recuerda la
    sucursal: la home carga con el toast de bienvenida y SIN el formulario de
    login (#region queda en el DOM pero invisible), aunque la sesion PHP del
    server ya este muerta. En ese estado _rellenar_form() falla siempre y el
    click posterior va a ciegas — causa de ~12 corridas de las 10:00 fallidas
    (03-15/07/2026). El fix: si el form no aparece, limpiar cookies + storage
    del sitio y recargar para forzar el flujo de primera visita, donde el form
    conocido vuelve a existir. El historial del perfil (score reCAPTCHA) no se
    pierde: clear_cookies() no toca historial de navegacion.
    """
    print("  Autocompletando formulario...")
    try:
        _rellenar_form(page, PWTimeout)
        print("  Formulario completo.")
        return True
    except Exception as e:
        print(f"  Form no disponible ({str(e)[:120]})")
        _screenshot_debug(page, " (1er intento)")

    print("  Estado semi-autenticado detectado: limpiando sesion local y recargando...")
    try:
        context.clear_cookies()
        page.evaluate("localStorage.clear(); sessionStorage.clear()")
    except Exception as e:
        print(f"  No se pudo limpiar la sesion local ({str(e)[:80]})")
    if not _goto_con_reintentos(page, BASE_URL):
        return False
    page.wait_for_timeout(5000)

    print("  Reintentando formulario con sitio en primera visita...")
    try:
        _rellenar_form(page, PWTimeout)
        print("  Formulario completo (2do intento).")
        return True
    except Exception as e:
        print(f"  No se pudo autocompletar tras el reset ({str(e)[:120]}). Completalo manualmente.")
        _screenshot_debug(page, " (2do intento)")
        return False


def _extraer_y_guardar_cookies(context) -> bool:
    cookies = context.cookies()
    phpsessid    = next((c["value"] for c in cookies if c["name"] == "PHPSESSID"), "")
    cf_clearance = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")
    if not phpsessid:
        print("  No se obtuvo PHPSESSID.")
        return False
    _guardar_cookies(phpsessid, cf_clearance)
    return True


# ---------------------------------------------------------------------------
# MODO 1: CapSolver API (100% automatico)
# ---------------------------------------------------------------------------

def _resolver_capsolver(api_key: str) -> str:
    """Envia el reCAPTCHA Enterprise a CapSolver y retorna el token."""
    import urllib.request, json as _json

    print("  Enviando reCAPTCHA Enterprise a CapSolver...")
    payload = _json.dumps({
        "clientKey": api_key,
        "task": {
            "type": "ReCaptchaV3EnterpriseTaskProxyLess",
            "websiteURL": BASE_URL,
            "websiteKey": RECAPTCHA_KEY,
            "pageAction": "login",
        }
    }).encode()
    req = urllib.request.Request(
        "https://api.capsolver.com/createTask", data=payload,
        headers={"Content-Type": "application/json"},
    )
    result = _json.loads(urllib.request.urlopen(req, timeout=15).read())
    task_id = result.get("taskId")
    if not task_id:
        raise Exception(f"CapSolver createTask fallo: {result}")

    for _ in range(40):
        time.sleep(3)
        payload = _json.dumps({"clientKey": api_key, "taskId": task_id}).encode()
        req = urllib.request.Request(
            "https://api.capsolver.com/getTaskResult", data=payload,
            headers={"Content-Type": "application/json"},
        )
        result = _json.loads(urllib.request.urlopen(req, timeout=15).read())
        status = result.get("status")
        if status == "ready":
            token = result["solution"]["gRecaptchaResponse"]
            print(f"  Token CapSolver: {token[:30]}...")
            return token
        if status == "failed":
            raise Exception(f"CapSolver fallo: {result}")

    raise Exception("CapSolver timeout (120s)")


def renovar_con_capsolver() -> bool:
    """Login 100% automatico usando CapSolver para resolver el reCAPTCHA Enterprise."""
    try:
        from patchright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    print("Modo: CapSolver API (100% automatico)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Visible mejora el score de reCAPTCHA
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="es-AR",
            timezone_id="America/Argentina/Buenos_Aires",
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print("  Navegando al sitio...")
            if not _goto_con_reintentos(page, BASE_URL):
                browser.close()
                return False
            page.wait_for_timeout(3000)

            print("  Llenando formulario...")
            _rellenar_form(page, PWTimeout)
            print("  Formulario completo.")

            # Obtener token de CapSolver
            token = _resolver_capsolver(CAPSOLVER_API_KEY)

            # Inyectar token: override grecaptcha.enterprise.execute ANTES de hacer click
            page.evaluate("""
                (t) => {
                    window.__capsolver_token = t;
                    function patchGrecaptcha() {
                        var ge = window.grecaptcha && window.grecaptcha.enterprise;
                        if (ge && ge.execute) {
                            ge.execute = function() { return Promise.resolve(window.__capsolver_token); };
                            console.log('[capsolver] grecaptcha.enterprise.execute patched');
                        } else {
                            setTimeout(patchGrecaptcha, 100);
                        }
                    }
                    patchGrecaptcha();
                }
            """, token)
            page.wait_for_timeout(500)

            print("  Enviando formulario con token CapSolver...")
            page.locator("#btn_step2, button.btn-blue-filled").first.click(timeout=8000)
            page.wait_for_timeout(5000)

            print("  Verificando autenticacion...")
            if not _esta_autenticado(page):
                print("  Login fallido — token CapSolver no funciono.")
                try:
                    page.screenshot(path=str(DEBUG_SCREENSHOT))
                except Exception:
                    pass
                browser.close()
                return False

            print("  Autenticacion confirmada.")
            ok = _extraer_y_guardar_cookies(context)
            browser.close()
            return ok

        except Exception as e:
            print(f"  Error en CapSolver: {e}")
            try:
                page.screenshot(path=str(DEBUG_SCREENSHOT))
            except Exception:
                pass
            browser.close()
            return False


# ---------------------------------------------------------------------------
# MODO 2: Chrome real con perfil persistente (1 click por mes)
# ---------------------------------------------------------------------------

def _traer_chrome_al_frente():
    """Intenta traer la ventana de Chrome al primer plano."""
    import ctypes
    import subprocess

    # PowerShell AppActivate
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-command",
         "Add-Type -AssemblyName Microsoft.VisualBasic; "
         "[Microsoft.VisualBasic.Interaction]::AppActivate('Google Chrome')"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(1)

    # ctypes SetForegroundWindow como respaldo
    try:
        result_hwnd = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

        def callback(hwnd, _):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                buf = ctypes.create_unicode_buffer(256)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
                title = buf.value.lower()
                if "carrefour" in title or "maxi" in title or ("chrome" in title and "google" in title):
                    result_hwnd.append(hwnd)
            return True

        ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), 0)
        if result_hwnd:
            ctypes.windll.user32.ShowWindow(result_hwnd[0], 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(result_hwnd[0])
    except Exception:
        pass


def renovar_con_chrome() -> bool:
    """
    Chrome real con perfil persistente.
    - Primera vez: form autocompleto + Facu hace 1 click en 'Ingresar'.
    - Veces siguientes (30 dias): ya autenticado, extrae cookies sin interaccion.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        from patchright.sync_api import sync_playwright, TimeoutError as PWTimeout

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print("Modo: Chrome real con perfil persistente...")

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                str(PROFILE_DIR),
                headless=False,
                executable_path=CHROME_EXE,
                args=["--disable-blink-features=AutomationControlled"],
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768},
                locale="es-AR",
                timezone_id="America/Argentina/Buenos_Aires",
            )
        except Exception as e:
            print(f"  Error abriendo Chrome: {e}")
            return False

        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print("  Navegando a comerciante.carrefour.com.ar...")
            if not _goto_con_reintentos(page, BASE_URL):
                context.close()
                return False
            page.wait_for_timeout(5000)  # Esperar que la sesion del perfil cargue

            if _esta_autenticado(page):
                print("  Perfil ya autenticado -- extrayendo cookies.")
            else:
                _autocompletar_con_reset(page, context, PWTimeout)

                # --- Intento automatico: click con Chrome real + delays humanos ---
                print("  Intentando click automatico (Chrome real)...")
                page.wait_for_timeout(4000)  # Dar tiempo al reCAPTCHA para scoring

                # Simular movimiento humano hacia el boton
                try:
                    btn = page.locator("#btn_step2, button.btn-blue-filled").first
                    box = btn.bounding_box()
                    if box:
                        # Mover el mouse desde el centro del form hacia el boton
                        page.mouse.move(box["x"] - 100, box["y"] - 50)
                        page.wait_for_timeout(300)
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        page.wait_for_timeout(500)
                    btn.click(timeout=5000)
                    print("  Click enviado. Esperando respuesta del servidor...")
                    page.wait_for_timeout(6000)
                    # Sitio rediseñado (15/07/2026): tras "Siguiente" puede
                    # aparecer #step3 con el boton final "Ingresar" — sin ese
                    # segundo click el login queda a mitad de camino. Solo se
                    # busca DENTRO de #step3 (el header tiene otro "Ingresar").
                    try:
                        btn_final = page.locator('#step3 button:has-text("Ingresar")').first
                        if btn_final.is_visible():
                            btn_final.click(timeout=5000)
                            print("  Click en 'Ingresar' (paso final) enviado.")
                            page.wait_for_timeout(6000)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"  Click automatico fallido: {e}")

                # Verificar si el click automatico funciono
                autenticado = _esta_autenticado(page)
                if autenticado:
                    print("  Click automatico EXITOSO - reCAPTCHA aceptado.")
                else:
                    # Verificar si hubo error de captcha
                    try:
                        error_visible = page.locator("text=captcha").is_visible(timeout=1000)
                    except Exception:
                        error_visible = False

                    if error_visible:
                        print("  reCAPTCHA bloqueo el click automatico.")
                    else:
                        print("  Click automatico sin respuesta definitiva.")

                    # Alertar para click manual como respaldo
                    try:
                        import winsound
                        for _ in range(5):
                            winsound.Beep(880, 250)
                            winsound.Beep(1100, 250)
                    except Exception:
                        pass

                    _traer_chrome_al_frente()

                    print("")
                    print("  ================================================")
                    print("  Click automatico no funciono.")
                    print("  Hace click en 'Ingresar' manualmente en Chrome.")
                    print("  Tenes 90 segundos.")
                    print("  ------------------------------------------------")
                    print("  Para 100% automatico: CAPSOLVER_API_KEY en .env")
                    print("  ================================================")
                    print("")

                    for intento in range(45):
                        page.wait_for_timeout(2000)
                        if _esta_autenticado(page):
                            autenticado = True
                            print(f"  Login detectado ({(intento + 1) * 2}s).")
                            break

                if not autenticado:
                    print("  Timeout — no se logro autenticacion.")
                    try:
                        page.screenshot(path=str(DEBUG_SCREENSHOT))
                        print(f"  Screenshot: {DEBUG_SCREENSHOT}")
                    except Exception:
                        pass
                    context.close()
                    return False

            ok = _extraer_y_guardar_cookies(context)
            context.close()
            return ok

        except Exception as e:
            print(f"  Error: {e}")
            try:
                page.screenshot(path=str(DEBUG_SCREENSHOT))
            except Exception:
                pass
            context.close()
            return False


# ---------------------------------------------------------------------------
# Disparo automatico del scraper tras renovar
# ---------------------------------------------------------------------------

def _disparar_scraper_si_corresponde(no_auto_scrape: bool):
    """La sesion de MaxiCarrefour muere en HORAS por inactividad (ver 02-scrapers.md).
    Si nadie la usa apenas se renueva, se pierde igual -- paso el 09/07/2026 con un
    login manual de Facu que nunca disparo el scraper y se desperdicio. Por eso, salvo
    que quien nos llamo (scrape_maxicarrefour.py) ya vaya a scrapear el solo, disparamos
    el scraping ahora mismo mientras la sesion esta viva."""
    if no_auto_scrape:
        return
    print("\nDisparando scrape_maxicarrefour.py para aprovechar la sesion mientras esta viva...")
    r = subprocess.run(["python", "scrape_maxicarrefour.py"], cwd=BASE_DIR)
    sys.exit(r.returncode)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    force = "--force" in sys.argv
    no_auto_scrape = "--no-auto-scrape" in sys.argv

    print("=" * 55)
    print("RENOVACION DE COOKIES MAXICARREFOUR")
    print("=" * 55)

    faltantes = [k for k, v in CAMPOS_REQUERIDOS.items() if not v]
    if faltantes:
        print("ERROR: Faltan estas variables en .env:")
        for f in faltantes:
            print(f"  {f}=")
        sys.exit(1)

    if not force and not cookies_necesitan_renovacion():
        print("OK: Cookies vigentes, no es necesario renovar.")
        sys.exit(0)
    elif force:
        print("Modo --force: renovando sin verificar fecha.")

    # Modo 1: CapSolver (completamente automatico)
    if CAPSOLVER_API_KEY:
        if renovar_con_capsolver():
            print("\nCookies renovadas con CapSolver.")
            print(f"Fecha: {datetime.date.today().isoformat()}")
            _disparar_scraper_si_corresponde(no_auto_scrape)
            sys.exit(0)
        print("CapSolver fallo -- intentando con Chrome real...")

    # Modo 2: Chrome real (semi-automatico, 1 click)
    if renovar_con_chrome():
        print("\nCookies renovadas con Chrome real.")
        print(f"Fecha: {datetime.date.today().isoformat()}")
        _disparar_scraper_si_corresponde(no_auto_scrape)
        sys.exit(0)

    # Modo 3: Manual
    print("\nNo se pudo renovar automaticamente.")
    print("Pasos manuales:")
    print("  1. Loguearse en comerciante.carrefour.com.ar")
    print("  2. F12 -> Application -> Cookies")
    print("  3. Copiar PHPSESSID y cf_clearance al .env")
    print("")
    print("Para automatizacion total (sin interaccion humana):")
    print("  1. Crear cuenta en capsolver.com")
    print("  2. Agregar CAPSOLVER_API_KEY=tu_key al .env")
    sys.exit(1)


if __name__ == "__main__":
    main()
