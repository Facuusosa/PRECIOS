"""
Genera el PANEL DE OUTREACH: un HTML autocontenido para que Facu revise, edite, apruebe
y envie los mensajes a cada comercio, con control total.

Que muestra por comercio:
- Foto del LOCAL (de Google Maps, guardada en data/outreach/fotos/) + nombre + datos.
- Direccion, logo de Maps clickeable, redes y telefono.
- Selector de MATERIAL con buscador autocompletado sobre todos los productos VALIDADOS
  (fresco <=7d, sin outliers, ahorro 20-55%). Al elegir, el mensaje, el ahorro y los links
  de los 3 mayoristas se actualizan solos.
- Links de Yaguar / Maxiconsumo / MaxiCarrefour del material para verificar el precio en vivo.
- Boton "Reportar precio" para marcar un dato sospechoso (queda en el export para revisarlo).
- Mensaje editable + acciones: Aprobar / Copiar / Abrir canal (wa.me con texto, ig.me, m.me)
  / Marcar enviado / Cancelar.

Estado, material elegido, ediciones y reportes se guardan en el navegador (localStorage).
Boton "Exportar" baja un JSON de respaldo (estado + reportes).

Uso:
  python scripts/generar_panel_outreach.py                       # ultima base de comercios
  python scripts/generar_panel_outreach.py data/outreach/x.json  # base especifica
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ejemplo_mensaje import NOMBRE, MAX_DIAS, MIN_PCT, MAX_PCT  # noqa: E402

CATALOGO = "BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json"
LINK_APP = "https://v0-brujula-de-precios.vercel.app"
SALIDA = "data/outreach/panel_outreach.html"
SALIDA_WEB = "BRUJULA-DE-PRECIOS/public/outreach.html"
SALUDO = "Buenos días"

# Materiales sugeridos por comercio (chips de atajo). Facu igual puede buscar cualquier validado.
SUGERIDOS_POR_COMERCIO = {
    "HLY Supermercado": ["vino", "fernet", "cerveza", "coca", "aceite", "whisky"],
    "Autoservicio San Cayetano": ["aceite cocinero", "aceite", "lavandina", "yerba", "fideos", "coca"],
    "Urquiza Market": ["lavandina", "aceite", "yerba", "fideos", "coca", "arroz", "cerveza"],
}
SUGERIDOS_DEFAULT = ["aceite", "lavandina", "yerba", "fideos", "coca"]


def prefijo() -> str:
    return (
        f"{SALUDO}. Mi nombre es Facundo Sosa, trabajo como analista de precios y desarrollé "
        f"una herramienta web, Brújula de Precios, que compara los precios de Yaguar, "
        f"Maxiconsumo y MaxiCarrefour para ver en cuál conviene comprar cada producto antes "
        f"de hacer el pedido.\n\n"
        f"La herramienta revisa automáticamente, todos los días, los precios publicados "
        f"por los tres mayoristas en sus sitios web y los reúne en una sola pantalla. Es un "
        f"comparador independiente: no vende productos ni reemplaza a ningún mayorista, "
        f"únicamente indica dónde conviene comprar.\n\n"
        f"Pensé que podía resultarle útil. Por ejemplo, "
    )


def sufijo() -> str:
    return (
        f". Tiene más de 18.000 productos e incluye una calculadora que sugiere el precio de "
        f"venta según el margen que desee y la opción de armar listas de compra, entre otras "
        f"funciones.\n\n"
        f"Por el momento está en fase de prueba, así que cualquier comentario suyo me "
        f"sería de mucha utilidad. Le dejo el enlace por si desea probarla: {LINK_APP}\n\n"
        f"Quedo a disposición por cualquier consulta. Saludos cordiales, Facundo Sosa."
    )


def cargar_prods() -> list:
    data = json.load(open(CATALOGO, encoding="utf-8"))
    return data if isinstance(data, list) else data.get("productos", [])


def imagen_producto(p: dict) -> str:
    if p.get("imagen"):
        return p["imagen"]
    for f in p.get("fuentes", {}).values():
        if f.get("imagen"):
            return f["imagen"]
    return ""


def frase_de(e: dict) -> str:
    return (f"el {e['producto']} figura a ${e['pmax']:,.0f} en {e['caro']} y a ${e['pmin']:,.0f} "
            f"en {e['barato']}: una diferencia de ${e['ahorro']:,.0f} por unidad ({e['pct']}%)"
            ).replace(",", ".")


def construir_pool(prods: list) -> list:
    """Todo el catalogo comparable (2+ precios). Los ABC=A van primero; los datos dudosos
    (fuera del rango robusto 20-55% o con flags stale/sospechoso) se marcan warn, NO se descartan:
    Facu elige cualquier material y ve la senal."""
    pool = []
    for p in prods:
        precios = {k: v for k, v in p.get("precios", {}).items() if v and v > 0}
        if len(precios) < 2:
            continue
        fuentes = p.get("fuentes", {})
        caro = max(precios, key=precios.get)
        barato = min(precios, key=precios.get)
        pmax, pmin = round(precios[caro]), round(precios[barato])
        pct = (pmax - pmin) / pmax * 100 if pmax else 0
        flag_fuente = any(fuentes.get(k, {}).get("precio_stale") or fuentes.get(k, {}).get("precio_sospechoso")
                          for k in precios)
        warn = flag_fuente or not (MIN_PCT <= pct <= MAX_PCT)
        fsrc = [{"may": NOMBRE.get(k, k), "precio": round(v), "link": fuentes.get(k, {}).get("link", "")}
                for k, v in sorted(precios.items(), key=lambda kv: kv[1])]
        e = {
            "producto": p.get("nombre_display"), "sector": p.get("sector", ""),
            "imagen": imagen_producto(p), "abc": p.get("abc"), "warn": warn,
            "caro": NOMBRE.get(caro, caro), "pmax": pmax,
            "barato": NOMBRE.get(barato, barato), "pmin": pmin,
            "ahorro": pmax - pmin, "pct": round(pct), "n": len(precios), "fuentes": fsrc,
        }
        e["frase"] = frase_de(e)
        pool.append(e)
    # A primero, luego sin warn, mas mayoristas, mayor ahorro -> los buenos arriba en el autocomplete
    pool.sort(key=lambda x: (x["abc"] == "A", not x["warn"], x["n"], x["pct"]), reverse=True)
    return pool


def sugeridos_para(nombre_comercio: str, pool: list, n: int = 8) -> list:
    """Atajos por comercio: solo ABC=A y sin warn (los mas confiables para mostrar)."""
    terminos = SUGERIDOS_POR_COMERCIO.get(nombre_comercio, SUGERIDOS_DEFAULT)
    vistos, out = set(), []
    for solo_a in (True, False):  # primero llena con A confiables; si faltan, completa
        for t in terminos + SUGERIDOS_DEFAULT:
            for e in pool:
                if solo_a and (e["abc"] != "A" or e["warn"]):
                    continue
                if t.lower() in e["producto"].lower() and e["producto"] not in vistos:
                    vistos.add(e["producto"])
                    out.append(e["producto"])
                    if len(out) >= n:
                        return out
    return out


def construir_registros(comercios: list, pool: list) -> list:
    registros = []
    for c in comercios:
        if c.get("estado") != "contacto_confirmado":
            continue
        sug = sugeridos_para(c["nombre"], pool)
        if not sug:
            continue
        wa = (c.get("whatsapp") or "").replace("+", "").replace(" ", "").replace("-", "")
        registros.append({
            "nombre": c["nombre"], "tipo": c.get("tipo", ""), "direccion": c.get("direccion", ""),
            "zona": c.get("zona", ""), "rating": c.get("rating"), "canal": c.get("canal", ""),
            "whatsapp": wa, "instagram": c.get("instagram"), "facebook": c.get("facebook"),
            "telefono": c.get("telefono", ""), "nota": c.get("nota", ""),
            "foto_local": c.get("foto_local", ""), "sugeridos": sug, "default": sug[0],
        })
    return registros


def render(registros: list, pool: list) -> str:
    return (_PLANTILLA
            .replace("/*DATOS*/", json.dumps(registros, ensure_ascii=False))
            .replace("/*POOL*/", json.dumps(pool, ensure_ascii=False))
            .replace("/*PREFIJO*/", json.dumps(prefijo(), ensure_ascii=False))
            .replace("/*SUFIJO*/", json.dumps(sufijo(), ensure_ascii=False))
            .replace("/*META*/", f"frescura &le;{MAX_DIAS}d &middot; ahorro {MIN_PCT}-{MAX_PCT}% &middot; sin outliers"))


_PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outreach &mdash; Br&uacute;jula de Precios</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --ink:#111; --gray:#6b7280; --line:#e2e2e2; --card-border:#c8c8c8; --bg:#fff; --plate:#f4f3f1;
    --gold:#c89055; --green:#15803d; --red:#b91c1c; --wa:#0f7a3d; --ig:#c1306c; --fb:#1d4ed8;
    --fs-xs:10.5px; --fs-sm:12px; --fs-body:15px; --fs-prod:20px; --fs-name:22px; --fs-h1:26px;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html{-webkit-text-size-adjust:100%}
  body{background:#f0efed;color:var(--ink);
    font-family:"Poppins",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    font-size:var(--fs-body);line-height:1.5;-webkit-font-smoothing:antialiased}
  a{color:inherit;text-decoration:none}

  /* ---- Header ---- */
  header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.95);
    backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line);padding:18px 24px 14px}
  .wrap{max-width:1280px;margin:0 auto}
  header h1{font-size:var(--fs-h1);font-weight:700;letter-spacing:-.5px}
  header .sub{font-size:var(--fs-sm);color:var(--gray);margin-top:2px}
  .bar{display:flex;gap:10px;align-items:center;margin-top:14px}
  .bar input{flex:1;padding:12px 16px;border:1px solid var(--line);border-radius:12px;
    font-size:var(--fs-body);font-family:inherit;background:var(--bg)}
  .bar input:focus{outline:none;border-color:var(--ink)}
  .btn-export{font-size:var(--fs-sm);padding:10px 14px;border-radius:10px;background:var(--bg);
    color:var(--ink);border:1px solid var(--line);cursor:pointer;font-family:inherit;white-space:nowrap}
  .chips{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;align-items:center}
  .chip{font-size:var(--fs-sm);padding:6px 14px;border-radius:999px;background:var(--bg);
    color:var(--gray);cursor:pointer;border:1px solid var(--line);font-weight:500}
  .chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
  .counts{margin-left:auto;font-size:var(--fs-sm);color:var(--gray)}
  .counts b{color:var(--ink);font-weight:600}

  /* ---- Cards container ---- */
  main{max-width:1280px;margin:0 auto;padding:28px 24px;display:flex;flex-direction:column;gap:28px}

  /* ---- Card: no padding, overflow:hidden so right bg fills to edges ---- */
  .card{background:var(--bg);border:2px solid var(--card-border);border-radius:20px;
    overflow:hidden;transition:border-color .2s;
    box-shadow:0 2px 12px rgba(0,0,0,.07),0 1px 3px rgba(0,0,0,.04)}
  .card.aprobado{border-color:var(--green)}
  .card.enviado{opacity:.55}
  .card.cancelado{opacity:.34}

  /* ---- Two-column grid ---- */
  .card-grid{display:grid;grid-template-columns:1fr 320px;align-items:stretch;min-height:0}
  .card-left{padding:28px 32px 28px 28px;border-right:2px solid var(--card-border)}
  .card-right{background:var(--plate);padding:28px 24px;display:flex;flex-direction:column;gap:0}

  /* ---- Right column: client card ---- */
  .local{width:100%;height:220px;border-radius:12px;background:#e8e6e2;overflow:hidden;
    display:flex;align-items:center;justify-content:center;margin-bottom:18px;flex-none}
  .local img{width:100%;height:100%;object-fit:cover}
  .local .ph{font-size:var(--fs-sm);color:var(--gray);text-align:center;padding:8px}

  .cr-name{font-size:var(--fs-name);font-weight:700;letter-spacing:-.4px;line-height:1.2}
  .cr-sub{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-top:8px}
  .cr-tipo{font-size:var(--fs-sm);color:var(--gray);font-weight:500}
  .cr-rating{font-size:var(--fs-sm);font-weight:600;color:var(--gold)}
  .cr-canal{font-size:var(--fs-xs);font-weight:700;padding:3px 9px;border-radius:999px}
  .cr-canal.wa{color:var(--wa);background:#e7f6ec}
  .cr-canal.ig{color:var(--ig);background:#fde7f0}
  .cr-canal.fb{color:var(--fb);background:#e8efff}

  .cr-divider{height:1px;background:var(--line);margin:16px 0}

  .cr-lbl{font-size:var(--fs-xs);font-weight:700;color:var(--gray);text-transform:uppercase;
    letter-spacing:.8px;margin-bottom:9px}

  /* Contact rows */
  .cr-rows{display:flex;flex-direction:column;gap:6px}
  .cr-row{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;
    background:var(--bg);border:1px solid var(--line);color:var(--ink);font-size:var(--fs-sm);
    font-weight:500;transition:border-color .15s;cursor:pointer}
  .cr-row:hover{border-color:#999}
  a.cr-row{text-decoration:none}
  .cr-row-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;
    justify-content:center;flex-none}
  .cr-row-icon svg{width:16px;height:16px}
  .cr-row-icon.c-wa{background:#e7f6ec;color:var(--wa)}
  .cr-row-icon.c-ig{background:#fde7f0;color:var(--ig)}
  .cr-row-icon.c-fb{background:#e8efff;color:var(--fb)}
  .cr-row-icon.c-tel{background:#f3f4f6;color:#374151}
  .cr-row-icon.c-map{background:#f3f4f6;color:#374151}
  .cr-row-body{flex:1;min-width:0}
  .cr-row-title{font-weight:600;font-size:var(--fs-sm);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .cr-row-desc{font-size:var(--fs-xs);color:var(--gray);margin-top:1px}
  .cr-row-tag{font-size:var(--fs-xs);font-weight:700;padding:2px 7px;border-radius:999px;flex-none}
  .cr-row-tag.ppal{background:#e7f6ec;color:var(--green)}
  .cr-row-tag.cel{background:#f0f9ff;color:#0369a1}
  .cr-row-tag.fijo{background:#f9f9f9;color:var(--gray)}

  .cr-nota{margin-top:14px;font-size:var(--fs-sm);color:var(--gray);
    padding:10px 12px;background:#eceae7;border-radius:10px;line-height:1.5;font-style:italic}

  .estado{display:none;font-size:var(--fs-sm);font-weight:600;padding:3px 10px;border-radius:999px;margin-left:8px;vertical-align:middle}
  .card.aprobado .estado{display:inline-block;background:#e8f3ec;color:var(--green)}
  .card.enviado .estado{display:inline-block;background:#eef;color:#3730a3}

  /* ---- Left column: work area ---- */
  .abadge{font-size:10px;font-weight:700;color:#9a6a2e;background:#f6ecdd;padding:1px 6px;border-radius:5px;margin-left:7px;vertical-align:middle;letter-spacing:.3px}
  .warn{display:inline-flex;align-items:center;gap:4px;font-size:var(--fs-sm);font-weight:600;color:#b45309;background:#fef3e2;padding:3px 10px;border-radius:999px}
  .ahpill{display:inline-block;background:#e7f6ec;color:var(--green);font-weight:600;font-size:var(--fs-sm);padding:3px 11px;border-radius:999px}
  .tag{font-size:var(--fs-sm);color:var(--gray);font-weight:500}

  .lab{font-size:var(--fs-xs);color:var(--gray);font-weight:700;text-transform:uppercase;letter-spacing:.7px}
  .ac{position:relative;margin-top:8px}
  .ac input{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:12px;
    font-size:var(--fs-body);font-family:inherit;background:var(--bg);color:var(--ink)}
  .ac input:focus{outline:none;border-color:var(--ink)}
  .ac-list{position:absolute;z-index:15;left:0;right:0;top:calc(100% + 4px);background:#fff;
    border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.12);
    max-height:260px;overflow:auto;display:none}
  .ac-list.show{display:block}
  .ac-item{padding:10px 14px;cursor:pointer;font-size:var(--fs-body);border-bottom:1px solid var(--line)}
  .ac-item:last-child{border-bottom:none}
  .ac-item:hover{background:var(--plate)}
  .ac-item small{font-weight:600;margin-left:6px}
  .ac-item small.pg{color:var(--green)} .ac-item small.pw{color:#b45309}
  .sugs{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}
  .sug{font-size:var(--fs-sm);padding:5px 11px;border-radius:999px;background:var(--plate);
    color:var(--ink);cursor:pointer;border:1px solid transparent}
  .sug:hover{border-color:var(--line)}

  .ejbox{display:flex;gap:14px;align-items:center;margin-top:16px;padding:14px;background:var(--plate);border-radius:12px}
  .ejthumb{width:48px;height:48px;border-radius:10px;background:#fff;flex:none;overflow:hidden;display:flex;align-items:center;justify-content:center}
  .ejthumb img{width:100%;height:100%;object-fit:contain;mix-blend-mode:multiply}
  .ejinfo{flex:1;min-width:0}
  .ejprod{font-weight:600;font-size:var(--fs-body);line-height:1.25}
  .links{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
  .lk{display:inline-flex;align-items:center;gap:5px;font-size:var(--fs-sm);padding:7px 11px;border-radius:9px;
    background:#fff;border:1px solid var(--line);text-decoration:none;color:var(--ink);font-weight:500}
  .lk:hover{border-color:var(--ink)}
  .lk b{font-weight:600}
  .lk.best{border-color:var(--green);color:var(--green)}
  .report{font-size:var(--fs-sm);color:var(--gray);background:none;border:none;cursor:pointer;
    text-decoration:underline;padding:0;margin-top:10px;font-family:inherit}
  .report:hover{color:var(--red)}

  .msg{margin-top:20px}
  textarea{width:100%;min-height:220px;margin-top:8px;padding:16px;border:1px solid var(--line);
    border-radius:14px;font-size:var(--fs-body);line-height:1.65;resize:vertical;font-family:inherit;
    color:var(--ink);background:var(--plate)}
  textarea:focus{outline:none;border-color:var(--ink);background:var(--bg)}

  .acciones{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px;align-items:center}
  .b{font-size:var(--fs-body);font-weight:500;padding:12px 20px;border-radius:999px;
    border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer;font-family:inherit;text-decoration:none}
  .b:hover{border-color:var(--ink)}
  .b.prim{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
  .b.ok.on{background:var(--green);color:#fff;border-color:var(--green)}
  .b.x{margin-left:auto;color:var(--red);border:none;background:none;font-size:var(--fs-sm)}
  .b.x:hover{text-decoration:underline}
  .b:active{transform:translateY(1px)}
  .empty{text-align:center;color:var(--gray);padding:60px 20px}
  .copied{font-size:var(--fs-sm);color:var(--green);font-weight:600}

  /* ---- Mobile ---- */
  @media(max-width:720px){
    body{background:var(--bg)}
    main{padding:16px;gap:20px}
    header{padding:14px 16px 12px}
    .card{border-radius:16px;border-width:1.5px}
    .card-grid{display:flex;flex-direction:column}
    /* client card goes first on mobile */
    .card-right{order:-1;background:var(--plate);padding:16px;
      flex-direction:row;gap:14px;align-items:flex-start;
      border-bottom:1.5px solid var(--card-border)}
    .card-left{padding:18px 16px}
    /* compact photo on mobile */
    .local{width:88px;height:70px;border-radius:10px;margin-bottom:0;flex:none}
    .cr-name{font-size:var(--fs-body);font-weight:700}
    .cr-sub{margin-top:4px;gap:5px}
    .cr-divider{display:none}
    .cr-lbl{display:none}
    .cr-rows{gap:5px}
    .cr-row{padding:8px 10px}
    .cr-row-icon{width:28px;height:28px}
    .cr-nota{margin-top:8px;font-size:var(--fs-xs)}
    /* Bigger tap targets */
    .b{padding:14px 18px}
    .b.prim{display:flex;align-items:center;justify-content:center;width:100%}
    .acciones{flex-direction:column;gap:8px}
    .acciones .b.x{margin-left:0}
  }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>Outreach</h1>
    <div class="sub">/*META*/ &mdash; eleg&iacute; material &middot; verific&aacute; precio en vivo &middot; envi&aacute; el mensaje</div>
    <div class="bar">
      <input id="q" placeholder="Buscar comercio, zona o canal&hellip;">
      <button class="btn-export" onclick="exportar()">Exportar respaldo</button>
    </div>
    <div class="chips" id="filtros">
      <span class="chip on" data-f="todos">Todos</span>
      <span class="chip" data-f="pendiente">Pendientes</span>
      <span class="chip" data-f="aprobado">Aprobados</span>
      <span class="chip" data-f="enviado">Enviados</span>
      <span class="counts" id="counts"></span>
    </div>
  </div>
</header>
<main id="lista"></main>

<script>
const COMERCIOS = /*DATOS*/;
const POOL = /*POOL*/;
const PREFIJO = /*PREFIJO*/;
const SUFIJO  = /*SUFIJO*/;
const BYNAME = {}; POOL.forEach(p => BYNAME[p.producto] = p);
const KEY = "outreach_brujula_v3", RKEY = "outreach_reportes_v3";
let estado = JSON.parse(localStorage.getItem(KEY) || "{}");
let reportes = JSON.parse(localStorage.getItem(RKEY) || "[]");
let filtro = "todos";
let _saveTimer = null;

// Extraer ?pw= de la URL actual para pasarlo a la API
const PW = new URLSearchParams(location.search).get("pw") || "";
const API = "/api/outreach?pw=" + encodeURIComponent(PW);

async function cargarDesdeNube() {
  try {
    const res = await fetch(API);
    if (!res.ok) return; // sin pw o error: usa localStorage
    const data = await res.json();
    if (data.estado && Object.keys(data.estado).length > 0) {
      estado = data.estado;
      reportes = data.reportes || [];
      localStorage.setItem(KEY, JSON.stringify(estado));
      localStorage.setItem(RKEY, JSON.stringify(reportes));
    }
  } catch { /* offline: usa localStorage */ }
}

function guardar() {
  localStorage.setItem(KEY, JSON.stringify(estado));
  localStorage.setItem(RKEY, JSON.stringify(reportes));
  // Debounce: espera 800ms antes de guardar en nube para no saturar
  clearTimeout(_saveTimer);
  _saveTimer = setTimeout(async () => {
    try { await fetch(API, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({estado, reportes}) }); }
    catch { /* offline: quedó en localStorage */ }
  }, 800);
}
function st(n){ if(!estado[n]) estado[n]={status:"pendiente", material:null, mensaje:null}; return estado[n]; }
function materialDe(c){ const s=st(c.nombre); return (s.material && BYNAME[s.material]) ? s.material : c.default; }
function mensajeDe(c){ const m=BYNAME[materialDe(c)]; return PREFIJO + (m?m.frase:"") + SUFIJO; }
function mapsUrl(c){ return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(`${c.nombre} ${c.direccion} CABA`); }
function plata(n){ return "$" + (n||0).toLocaleString("es-AR"); }
function jq(s){ return (s||"").replace(/'/g,"\\'").replace(/"/g,"&quot;"); }

const ICO_WA   = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M11.998 2.003C6.477 2.003 2 6.479 2 12c0 1.847.483 3.58 1.332 5.086L2 22l5.049-1.317A9.946 9.946 0 0 0 12 22c5.521 0 9.998-4.477 9.998-9.997S17.519 2.003 11.998 2.003z" fill-opacity=".15"/><path d="M11.998 4.003c-4.411 0-7.997 3.586-7.997 7.997 0 1.75.564 3.37 1.52 4.685l-.995 2.882 2.976-.977A7.944 7.944 0 0 0 12 20c4.411 0 7.998-3.587 7.998-7.997 0-4.41-3.587-7.997-7.998-7.997z" fill="none" stroke="currentColor" stroke-width=".5"/></svg>';
const ICO_IG   = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>';
const ICO_FB   = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>';
const ICO_TEL  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.07 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3 1.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.09 8.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21 16h1z"/></svg>';
const ICO_MAP  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-5.5-7-11a7 7 0 0 1 14 0c0 5.5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>';

function canalCls(canal){ return canal.includes("WhatsApp")?"wa":canal.includes("Instagram")?"ig":canal.includes("Facebook")?"fb":""; }

function botonEnvio(c, msg){
  const t = encodeURIComponent(msg);
  if(c.canal.includes("WhatsApp") && c.whatsapp)
    return `<a class="b prim" target="_blank" href="https://wa.me/${c.whatsapp}?text=${t}">Abrir WhatsApp &rarr;</a>`;
  if(c.canal.includes("Instagram") && c.instagram)
    return `<a class="b prim" target="_blank" href="https://ig.me/m/${c.instagram}">Abrir Instagram DM &rarr;</a>`;
  if(c.canal.includes("Facebook") && c.facebook)
    return `<a class="b prim" target="_blank" href="https://m.me/${c.facebook}">Abrir Messenger &rarr;</a>`;
  return "";
}

function bloqueMaterial(c, i){
  const m = BYNAME[materialDe(c)];
  if(!m) return "";
  const thumb = m.imagen ? `<img src="${m.imagen}" onerror="this.style.display='none'">` : "";
  const links = m.fuentes.map(f => {
    const best = f.precio === m.pmin ? " best" : "";
    return f.link ? `<a class="lk${best}" target="_blank" href="${f.link}">${f.may} <b>${plata(f.precio)}</b> &nearr;</a>`
                  : `<span class="lk">${f.may} <b>${plata(f.precio)}</b></span>`;
  }).join("");
  const sugs = c.sugeridos.map(s => `<span class="sug" onclick="setMat('${jq(c.nombre)}','${jq(s)}')">${s.split(" ").slice(0,3).join(" ")}</span>`).join("");
  return `
    <div class="lab">Material del mensaje &mdash; escrib&iacute; cualquier producto</div>
    <div class="ac">
      <input id="inp${i}" autocomplete="off" placeholder="${jq(m.producto)}"
        oninput="ac(${i},'${jq(c.nombre)}')" onfocus="ac(${i},'${jq(c.nombre)}')" onblur="setTimeout(()=>cerrarAc(${i}),150)">
      <div class="ac-list" id="acl${i}"></div>
    </div>
    <div class="sugs">${sugs}</div>
    <div class="ejbox">
      <div class="ejthumb">${thumb}</div>
      <div class="ejinfo">
        <div class="ejprod">${m.producto}${m.abc==="A"?'<span class="abadge">TOP A</span>':""}</div>
        <div style="margin-top:7px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <span class="ahpill">Ahorro ${plata(m.ahorro)} &middot; ${m.pct}%</span>
          <span class="tag">${m.n} mayoristas</span>
          ${m.warn?'<span class="warn">&#9888; revisar precio</span>':""}
        </div>
        <div class="links">${links}</div>
        <button class="report" onclick="reportar('${jq(c.nombre)}','${jq(m.producto)}')">&#9873; Reportar precio incorrecto</button>
      </div>
    </div>`;
}

function clientCard(c, s){
  const fl = c.foto_local ? `<img src="${c.foto_local}" onerror="this.parentNode.innerHTML='<div class=ph>sin foto</div>'">` : `<div class="ph">sin foto</div>`;
  const estadoHtml = s.status==="aprobado"
    ? `<span class="estado">Aprobado</span>`
    : s.status==="enviado" ? `<span class="estado">Enviado</span>` : "";

  const ccls = canalCls(c.canal);
  const canalLabel = c.canal.includes("WhatsApp")?"WhatsApp":c.canal.includes("Instagram")?"Instagram DM":c.canal.includes("Facebook")?"Facebook":c.canal;

  const rowWa = c.whatsapp ? `
    <a class="cr-row" href="https://wa.me/${c.whatsapp}" target="_blank">
      <div class="cr-row-icon c-wa">${ICO_WA}</div>
      <div class="cr-row-body">
        <div class="cr-row-title">+${c.whatsapp}</div>
        <div class="cr-row-desc">WhatsApp</div>
      </div>
      ${c.canal.includes("WhatsApp")?'<span class="cr-row-tag ppal">principal</span>':''}
    </a>` : "";

  const rowIg = c.instagram ? `
    <a class="cr-row" href="https://instagram.com/${c.instagram}" target="_blank">
      <div class="cr-row-icon c-ig">${ICO_IG}</div>
      <div class="cr-row-body">
        <div class="cr-row-title">@${c.instagram}</div>
        <div class="cr-row-desc">Instagram</div>
      </div>
      ${c.canal.includes("Instagram")?'<span class="cr-row-tag ppal">principal</span>':''}
    </a>` : "";

  const rowFb = c.facebook ? `
    <a class="cr-row" href="https://facebook.com/${c.facebook}" target="_blank">
      <div class="cr-row-icon c-fb">${ICO_FB}</div>
      <div class="cr-row-body">
        <div class="cr-row-title">${c.facebook}</div>
        <div class="cr-row-desc">Facebook</div>
      </div>
      ${c.canal.includes("Facebook")?'<span class="cr-row-tag ppal">principal</span>':''}
    </a>` : "";

  const celTag = c.es_celular===true ? `<span class="cr-row-tag cel">celular</span>`
               : c.es_celular===false ? `<span class="cr-row-tag fijo">fijo</span>` : "";
  const rowTel = c.telefono ? `
    <a class="cr-row" href="tel:${c.telefono.replace(/\s/g,'')}">
      <div class="cr-row-icon c-tel">${ICO_TEL}</div>
      <div class="cr-row-body">
        <div class="cr-row-title">${c.telefono}</div>
        <div class="cr-row-desc">Llamar</div>
      </div>
      ${celTag}
    </a>` : "";

  const rowMap = `
    <a class="cr-row" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(c.nombre+' '+c.direccion+' CABA')}" target="_blank">
      <div class="cr-row-icon c-map">${ICO_MAP}</div>
      <div class="cr-row-body">
        <div class="cr-row-title">${c.direccion}</div>
        <div class="cr-row-desc">${c.zona}</div>
      </div>
    </a>`;

  const notaHtml = c.nota ? `<div class="cr-nota">${c.nota}</div>` : "";

  return `
    <div class="local">${fl}</div>
    <div class="cr-name">${c.nombre}${estadoHtml}</div>
    <div class="cr-sub">
      <span class="cr-tipo">${c.tipo}</span>
      ${c.rating?`<span class="cr-rating">&#9733; ${c.rating}</span>`:""}
      <span class="cr-canal ${ccls}">${canalLabel}</span>
    </div>
    <div class="cr-divider"></div>
    <div class="cr-lbl">Contacto</div>
    <div class="cr-rows">${rowWa}${rowIg}${rowFb}${rowTel}</div>
    <div class="cr-divider"></div>
    <div class="cr-lbl">Ubicaci&oacute;n</div>
    <div class="cr-rows">${rowMap}</div>
    ${notaHtml}`;
}

function render(){
  const q = (document.getElementById("q").value || "").toLowerCase();
  const cont = document.getElementById("lista");
  cont.innerHTML = "";
  let vis = 0;
  COMERCIOS.forEach((c, i) => {
    const s = st(c.nombre);
    if(q && !`${c.nombre} ${c.zona} ${c.canal} ${c.tipo}`.toLowerCase().includes(q)) return;
    if(filtro !== "todos" && s.status !== filtro) return;
    vis++;
    const msg = s.mensaje !== null ? s.mensaje : mensajeDe(c);

    const card = document.createElement("div");
    card.className = "card " + (s.status==="pendiente"?"":s.status);
    card.innerHTML = `
      <div class="card-grid">
        <div class="card-left">
          <div id="mat${i}">${bloqueMaterial(c,i)}</div>
          <div class="msg">
            <div class="lab">Mensaje &mdash; edit&aacute;lo libremente</div>
            <textarea id="ta${i}">${msg.replace(/</g,"&lt;")}</textarea>
          </div>
          <div class="acciones">
            <button class="b ok ${s.status==="aprobado"?"on":""}" onclick="aprobar('${jq(c.nombre)}',${i})">${s.status==="aprobado"?"&#10003; Aprobado":"Aprobar"}</button>
            <button class="b" onclick="copiar(${i},this)">Copiar</button>
            <span id="envio${i}"></span>
            <button class="b" onclick="enviado('${jq(c.nombre)}')">Marcar enviado</button>
            <button class="b x" onclick="cancelar('${jq(c.nombre)}')">Cancelar</button>
          </div>
        </div>
        <div class="card-right">${clientCard(c,s)}</div>
      </div>`;
    cont.appendChild(card);
    const slot = card.querySelector(`#envio${i}`);
    slot.innerHTML = botonEnvio(c, msg);
    const ta = card.querySelector(`#ta${i}`);
    ta.addEventListener("input", () => { st(c.nombre).mensaje = ta.value; guardar(); slot.innerHTML = botonEnvio(c, ta.value); });
  });
  if(!vis) cont.innerHTML = `<div class="empty">No hay comercios para este filtro.</div>`;
  contadores();
}

function ac(i, n){
  const q = (document.getElementById("inp"+i).value || "").toLowerCase().trim();
  const box = document.getElementById("acl"+i);
  if(q.length < 2){ box.classList.remove("show"); return; }
  const res = POOL.filter(p => p.producto.toLowerCase().includes(q)).slice(0, 10);
  box.innerHTML = res.length
    ? res.map(p => `<div class="ac-item" onmousedown="setMat('${jq(n)}','${jq(p.producto)}')">${p.producto}${p.abc==="A"?'<span class="abadge">A</span>':""}<small class="${p.warn?'pw':'pg'}">${p.pct}%</small></div>`).join("")
    : `<div class="ac-item" style="color:#808080">Sin resultados &mdash; prob&aacute; otra palabra</div>`;
  box.classList.add("show");
}
function cerrarAc(i){ const b=document.getElementById("acl"+i); if(b) b.classList.remove("show"); }
function setMat(n, prod){ const s=st(n); s.material=prod; s.mensaje=null; guardar(); render(); }

function aprobar(n,i){ const ta=document.getElementById("ta"+i); st(n).mensaje=ta.value; st(n).status=(st(n).status==="aprobado"?"pendiente":"aprobado"); guardar(); render(); }
function enviado(n){ st(n).status="enviado"; st(n).fecha=new Date().toISOString(); guardar(); render(); }
function cancelar(n){ if(confirm("Cancelar este comercio?")){ st(n).status="cancelado"; guardar(); render(); } }
function copiar(i,b){ const ta=document.getElementById("ta"+i); ta.select(); navigator.clipboard.writeText(ta.value); b.outerHTML=`<span class="copied">&#10003; Copiado</span>`; setTimeout(render,1100); }
function reportar(n, prod){
  const nota = prompt("Reportar precio incorrecto de:\n"+prod+"\n\nQue viste mal? (opcional)");
  if(nota===null) return;
  reportes.push({comercio:n, producto:prod, nota, fecha:new Date().toISOString(), fuentes:BYNAME[prod]?.fuentes});
  localStorage.setItem(RKEY, JSON.stringify(reportes));
  alert("Reportado. Queda en el export para revisar.");
}

function contadores(){
  let p=0,a=0,e=0;
  COMERCIOS.forEach(c=>{ const s=st(c.nombre).status; if(s==="pendiente")p++; else if(s==="aprobado")a++; else if(s==="enviado")e++; });
  let r = reportes.length ? ` &middot; Reportes <b>${reportes.length}</b>` : "";
  document.getElementById("counts").innerHTML = `Pend. <b>${p}</b> &middot; Aprob. <b>${a}</b> &middot; Env. <b>${e}</b>${r}`;
}
function exportar(){
  const out = {fecha:new Date().toISOString(),comercios:COMERCIOS.map(c=>({nombre:c.nombre,canal:c.canal,material:materialDe(c),...st(c.nombre)})),reportes};
  const blob = new Blob([JSON.stringify(out,null,2)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "estado_outreach_" + new Date().toISOString().slice(0,10) + ".json"; a.click();
}

// Bloquear sin contraseña
if (!PW) {
  document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:system-ui;color:#666">Acceso restringido. Necesitás la URL con la clave.</div>';
} else {
  document.getElementById("q").addEventListener("input", render);
  document.querySelectorAll("#filtros .chip").forEach(ch=>ch.addEventListener("click", ()=>{
    document.querySelectorAll("#filtros .chip").forEach(x=>x.classList.remove("on"));
    ch.classList.add("on"); filtro = ch.dataset.f; render();
  }));
  // Cargar estado de la nube primero, luego renderizar
  cargarDesdeNube().then(render);
}
</script>
</body>
</html>"""


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else None
    if not base:
        if os.path.exists("data/outreach/comercios_consolidado.json"):
            base = "data/outreach/comercios_consolidado.json"
        else:
            candidatos = sorted(glob.glob("data/outreach/comercios_*.json"))
            if not candidatos:
                print("No hay base de comercios en data/outreach/comercios_*.json")
                sys.exit(1)
            base = candidatos[-1]
    print(f"Base de comercios: {base}")
    comercios = json.load(open(base, encoding="utf-8")).get("comercios", [])
    pool = construir_pool(cargar_prods())
    registros = construir_registros(comercios, pool)
    if not registros:
        print("No se generaron registros (sin comercios 'contacto_confirmado' o sin ejemplo validado).")
        sys.exit(1)
    html = render(registros, pool)
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(html)
    os.makedirs(os.path.dirname(SALIDA_WEB), exist_ok=True)
    with open(SALIDA_WEB, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Panel generado: {SALIDA}  ({len(registros)} comercios, pool de {len(pool)} materiales validados)")
    print(f"Panel web:      {SALIDA_WEB}  (listo para deploy a Vercel)")
    for r in registros:
        foto = "con foto" if r["foto_local"] else "SIN foto"
        print(f"  - {r['nombre']:28} | {r['canal']:18} | {foto:9} | default: {r['default'][:30]}")
    import webbrowser
    webbrowser.open("file://" + os.path.abspath(SALIDA))


if __name__ == "__main__":
    main()
