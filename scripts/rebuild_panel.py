"""
Reconstruye panel_outreach.html con layout master-detail.
Usa placeholders __DATA_X__ para evitar conflicto entre f-string Python y llaves JS.
"""
import re, json as _json

SRC  = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\panel_outreach.html"
OUTS = [
    r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\panel_outreach.html",
    r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\public\outreach.html",
]
JSON_SRC = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\comercios_10km_20260618_enriquecido.json"

with open(SRC, encoding="utf-8-sig") as f:
    src = f.read()

def extract_line(pattern):
    m = re.search(pattern, src)
    return m.group(0).strip() if m else ""

# COMERCIOS: generar fresh del JSON (ensure_ascii=True para evitar chars no-ASCII en el script)
def _to_float(s):
    try: return float(s)
    except: return 0.0

def _ig(url):
    m = re.search(r'instagram\.com/([^/?]+)', url or "")
    return m.group(1) if m else ""

def _fb(url):
    m = re.search(r'facebook\.com/([^/?]+)', url or "")
    p = m.group(1) if m else ""
    return p if p not in ["sharer", "share", "dialog"] else ""

def _wa(url):
    m = re.search(r'wa\.me/(\d+)', url or "")
    return m.group(1) if m else ""

with open(JSON_SRC, encoding="utf-8") as f:
    raw = _json.load(f)

comercios = []
for c in raw["comercios"]:
    comercios.append({
        "nombre":    c.get("nombre", ""),
        "tipo":      c.get("categoria", ""),
        "direccion": c.get("direccion", ""),
        "zona":      c.get("zona", ""),
        "rating":    _to_float(c.get("rating", "0")),
        "reviews":   c.get("reviews", ""),
        "canal":     c.get("canal", "sin_contacto"),
        "telefono":  c.get("telefono", ""),
        "es_celular": c.get("es_celular", False),
        "whatsapp":  _wa(c.get("whatsapp", "")),
        "instagram": _ig(c.get("instagram", "")),
        "facebook":  _fb(c.get("facebook", "")),
        "website":   c.get("website", ""),
        "foto_url":  c.get("foto_url", ""),
        "foto_local": "",
        "url_maps":  c.get("url_maps", ""),
        "horario":   c.get("horario", ""),
        "nota":      "",
    })

CANAL_PRIORITY = {"WhatsApp": 0, "Instagram": 1, "Facebook": 2, "celular": 3, "fijo": 4, "sin_contacto": 5}
comercios.sort(key=lambda c: CANAL_PRIORITY.get(c["canal"], 6))
line_comercios = "const COMERCIOS = " + _json.dumps(comercios, ensure_ascii=True, separators=(',', ':')) + ";"

CATALOGO_PATH = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\data\processed\catalogo_unificado.json"
POOL_BACKUP   = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\pool_backup.json"

MAY_LABEL = {"yaguar": "Yaguar", "maxicarrefour": "MaxiCarrefour", "maxiconsumo": "Maxiconsumo"}
MAY_LINK  = {"yaguar": "yaguar", "maxicarrefour": "maxicarrefour", "maxiconsumo": "maxiconsumo"}

def _fmt(n):
    return f"{int(n):,}".replace(",", ".")

def build_pool():
    with open(CATALOGO_PATH, encoding="utf-8") as f:
        cat = _json.load(f)
    prods = cat if isinstance(cat, list) else cat.get("productos", [])
    pool = []
    for p in prods:
        prs = {k: v for k, v in p.get("precios", {}).items() if v and v > 0}
        if len(prs) < 2:
            continue
        sorted_prs = sorted(prs.items(), key=lambda x: x[1])
        k_min, p_min = sorted_prs[0]
        k_max, p_max = sorted_prs[-1]
        ahorro = int(p_max - p_min)
        pct    = int(round(ahorro / p_max * 100))
        if pct < 5:  # diferencia menor al 5% no es interesante para el mensaje
            continue
        fuentes = []
        for k, v in sorted_prs:
            src = p.get("fuentes", {}).get(k, {})
            link = src.get("link", "")
            fuentes.append({"may": MAY_LABEL[k], "precio": int(v), "link": link})
        # marcar stale si alguna fuente tiene precio_stale
        warn = any(
            p.get("fuentes", {}).get(k, {}).get("precio_stale", False)
            for k in prs
        )
        frase = (
            f"el {p['nombre_display']} figura a ${_fmt(p_max)} en "
            f"{MAY_LABEL[k_max]} y a ${_fmt(p_min)} en {MAY_LABEL[k_min]}: "
            f"una diferencia de ${_fmt(ahorro)} por unidad ({pct}%)"
        )
        pool.append({
            "producto": p["nombre_display"],
            "sector":   p.get("sector", ""),
            "imagen":   p.get("imagen", ""),
            "abc":      p.get("abc", "C"),
            "warn":     warn,
            "caro":     MAY_LABEL[k_max],
            "pmax":     int(p_max),
            "barato":   MAY_LABEL[k_min],
            "pmin":     int(p_min),
            "ahorro":   ahorro,
            "pct":      pct,
            "n":        len(prs),
            "fuentes":  fuentes,
            "frase":    frase,
        })
    # ordenar por ABC desc, luego por pct desc
    abc_order = {"A": 0, "B": 1, "C": 2}
    pool.sort(key=lambda x: (abc_order.get(x["abc"], 3), -x["pct"]))
    return pool

pool = build_pool()
# guardar pool_backup actualizado
with open(POOL_BACKUP, "w", encoding="utf-8") as f:
    _json.dump(pool, f, ensure_ascii=False, indent=2)
pool_json = _json.dumps(pool, ensure_ascii=True, separators=(',', ':'))
print(f"  POOL generado: {len(pool)} productos desde catalogo (backup actualizado)")
print(f"  COMERCIOS: {len(line_comercios)} chars")
print(f"  POOL json: {len(pool_json)} chars")

line_prefijo = (
    'const PREFIJO = "Buenos dias, __NOMBRE__. Mi nombre es Facundo Sosa, trabajo'
    ' como analista de precios y desarrolle una herramienta web, Brujula de Precios,'
    ' que compara los precios de Yaguar, Maxiconsumo y MaxiCarrefour para ver en cual'
    ' conviene comprar cada producto antes de hacer el pedido.\\n\\nLa herramienta'
    ' revisa automaticamente, todos los dias, los precios publicados por los tres'
    ' mayoristas en sus sitios web y los reune en una sola pantalla.\\n\\nPense que'
    ' le podia resultar util. Por ejemplo, ";'
)
line_sufijo = (
    'const SUFIJO  = ". Tiene mas de 18.000 productos e incluye una calculadora'
    ' que sugiere el precio de venta segun el margen que desee y la opcion de armar'
    ' listas de compra, entre otras funciones.\\n\\nPor ahora es gratuita.'
    ' Le dejo el enlace por si desea probarla: https://v0-brujula-de-precios.vercel.app'
    '\\n\\nSi lo prueba y tiene algun comentario, lo escucho con gusto.'
    ' Saludos, Facundo Sosa.";'
)

# El HTML usa __DATA_COMERCIOS__ etc. como placeholders — sin f-string
HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outreach - Brujula de Precios</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --ink:#111; --gray:#6b7280; --line:#e2e2e2; --bg:#fff; --plate:#f4f3f1;
  --gold:#c89055; --green:#15803d; --red:#b91c1c; --wa:#0f7a3d; --ig:#c1306c; --fb:#1d4ed8;
  --purple:#3730a3; --amber:#b45309; --teal:#0f766e;
  --fs-xs:10.5px; --fs-sm:12px; --fs-body:14px; --fs-lg:16px; --fs-xl:20px;
}
* { box-sizing:border-box; margin:0; padding:0 }
html, body { height:100% }
body { background:#f0efed; color:var(--ink);
  font-family:"Poppins",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:var(--fs-body); line-height:1.5; -webkit-font-smoothing:antialiased;
  display:flex; flex-direction:column; overflow:hidden }
a { color:inherit; text-decoration:none }

/* HEADER */
header { flex:none; background:rgba(255,255,255,.96); backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line); padding:12px 20px 10px; z-index:30 }
.h-top { display:flex; align-items:baseline; gap:10px }
header h1 { font-size:var(--fs-xl); font-weight:700; letter-spacing:-.4px }
.h-sub { font-size:var(--fs-xs); color:var(--gray) }
.stats { display:flex; gap:12px; flex-wrap:wrap; margin-top:5px; font-size:var(--fs-xs); color:var(--gray) }
.stats b { color:var(--ink) }
.stat-rep { color:var(--amber); cursor:pointer; font-weight:600 }
.stat-rep:hover { text-decoration:underline }
.bar { display:flex; gap:8px; align-items:center; margin-top:8px }
.bar input { flex:1; padding:8px 13px; border:1px solid var(--line); border-radius:9px;
  font-size:var(--fs-sm); font-family:inherit; background:var(--bg) }
.bar input:focus { outline:none; border-color:var(--ink) }
.btn-sm { font-size:var(--fs-xs); padding:7px 12px; border-radius:8px; background:var(--bg);
  color:var(--ink); border:1px solid var(--line); cursor:pointer; font-family:inherit; white-space:nowrap }
.btn-sm:hover { border-color:var(--ink) }
.chips { display:flex; gap:5px; margin-top:8px; flex-wrap:wrap }
.chip { font-size:var(--fs-xs); padding:4px 11px; border-radius:999px; background:var(--bg);
  color:var(--gray); cursor:pointer; border:1px solid var(--line); font-weight:500; white-space:nowrap }
.chip.on { background:var(--ink); color:#fff; border-color:var(--ink) }
.chip.c-green.on { background:var(--green); border-color:var(--green) }
.chip.c-purple.on { background:var(--purple); border-color:var(--purple) }
.chip.c-red.on { background:var(--red); border-color:var(--red) }
.chip.c-amber.on { background:var(--amber); border-color:var(--amber) }
.chip.c-teal.on { background:var(--teal); border-color:var(--teal) }

/* LAYOUT */
.layout { flex:1; display:flex; overflow:hidden }
.sidebar { width:320px; flex:none; overflow-y:auto; border-right:1px solid var(--line); background:var(--bg) }
.detail { flex:1; overflow-y:auto; background:#f0efed }

/* SIDEBAR ROWS */
.s-row { display:flex; align-items:center; gap:9px; padding:10px 13px;
  border-bottom:1px solid var(--line); cursor:pointer; transition:background .1s }
.s-row:hover { background:#f7f6f5 }
.s-row.sel { background:#f0efed; border-left:3px solid var(--ink) }
.s-row.sel.st-aprobado { border-left-color:var(--green) }
.s-row.sel.st-enviado { border-left-color:var(--purple) }
.s-row.sel.st-respondio { border-left-color:var(--teal) }
.s-row.sel.st-no_respondio { border-left-color:var(--gray) }
.s-row.sel.st-cancelado { border-left-color:var(--red) }
.s-icon { width:30px; height:30px; border-radius:8px; background:var(--plate); flex:none;
  display:flex; align-items:center; justify-content:center; font-size:14px }
.s-body { flex:1; min-width:0 }
.s-name { font-weight:600; font-size:var(--fs-sm); white-space:nowrap; overflow:hidden; text-overflow:ellipsis }
.s-meta { font-size:10px; color:var(--gray); white-space:nowrap; overflow:hidden; text-overflow:ellipsis }
.s-badge { font-size:10px; font-weight:700; padding:2px 6px; border-radius:999px; flex:none; white-space:nowrap }
.s-badge.aprobado { background:#e8f3ec; color:var(--green) }
.s-badge.enviado { background:#eef; color:var(--purple) }
.s-badge.cancelado { background:#fee2e2; color:var(--red) }
.s-badge.respondio { background:#f0fdf4; color:var(--teal) }
.s-badge.no_respondio { background:#f3f4f6; color:var(--gray) }
.s-empty { padding:40px 16px; text-align:center; color:var(--gray); font-size:var(--fs-sm) }

/* DETAIL */
.detail-inner { padding:18px; display:grid; grid-template-columns:1fr 290px; gap:16px; max-width:960px }
.detail-empty { display:flex; align-items:center; justify-content:center; height:70vh;
  color:var(--gray); font-size:var(--fs-sm); text-align:center }

/* WORK AREA */
.work { background:var(--bg); border:1.5px solid #d4d4d4; border-radius:14px; padding:20px }
.lab { font-size:var(--fs-xs); color:var(--gray); font-weight:700; text-transform:uppercase; letter-spacing:.7px }
.ac { position:relative; margin-top:7px }
.ac input { width:100%; padding:9px 12px; border:1px solid var(--line); border-radius:9px;
  font-size:var(--fs-body); font-family:inherit; background:var(--bg); color:var(--ink) }
.ac input:focus { outline:none; border-color:var(--ink) }
.ac-list { position:absolute; z-index:20; left:0; right:0; top:calc(100% + 4px); background:#fff;
  border:1px solid var(--line); border-radius:10px; box-shadow:0 8px 24px rgba(0,0,0,.12);
  max-height:220px; overflow:auto; display:none }
.ac-list.show { display:block }
.ac-item { padding:8px 12px; cursor:pointer; font-size:var(--fs-sm); border-bottom:1px solid var(--line) }
.ac-item:last-child { border-bottom:none }
.ac-item:hover { background:var(--plate) }
.ac-item small { font-weight:600; margin-left:5px }
.ac-item small.pg { color:var(--green) } .ac-item small.pw { color:var(--amber) }
.sugs { display:flex; gap:5px; flex-wrap:wrap; margin-top:8px }
.sug { font-size:10px; padding:3px 9px; border-radius:999px; background:var(--plate);
  color:var(--ink); cursor:pointer; border:1px solid transparent }
.sug:hover { border-color:var(--line) }
.ejbox { display:flex; gap:11px; align-items:center; margin-top:12px; padding:11px; background:var(--plate); border-radius:10px }
.ejthumb { width:40px; height:40px; border-radius:8px; background:#fff; flex:none; overflow:hidden;
  display:flex; align-items:center; justify-content:center }
.ejthumb img { width:100%; height:100%; object-fit:contain; mix-blend-mode:multiply }
.ejinfo { flex:1; min-width:0 }
.ejprod { font-weight:600; font-size:var(--fs-sm); line-height:1.25 }
.abadge { font-size:10px; font-weight:700; color:#9a6a2e; background:#f6ecdd; padding:1px 5px; border-radius:4px; margin-left:5px }
.links { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px }
.lk { display:inline-flex; align-items:center; gap:4px; font-size:10px; padding:5px 9px; border-radius:7px;
  background:#fff; border:1px solid var(--line); text-decoration:none; color:var(--ink); font-weight:500 }
.lk:hover { border-color:var(--ink) }
.lk.best { border-color:var(--green); color:var(--green) }
.report { font-size:10px; color:var(--gray); background:none; border:none; cursor:pointer;
  text-decoration:underline; padding:0; margin-top:7px; font-family:inherit }
.report:hover { color:var(--red) }
.ahpill { display:inline-block; background:#e7f6ec; color:var(--green); font-weight:600; font-size:10px; padding:2px 8px; border-radius:999px }
.msg { margin-top:14px }
textarea { width:100%; min-height:180px; margin-top:6px; padding:12px; border:1px solid var(--line);
  border-radius:10px; font-size:var(--fs-sm); line-height:1.65; resize:vertical; font-family:inherit;
  color:var(--ink); background:var(--plate) }
textarea:focus { outline:none; border-color:var(--ink); background:var(--bg) }
.acciones { display:flex; gap:7px; flex-wrap:wrap; margin-top:12px; align-items:center }
.b { font-size:var(--fs-sm); font-weight:500; padding:9px 16px; border-radius:999px;
  border:1px solid var(--line); background:var(--bg); color:var(--ink); cursor:pointer; font-family:inherit }
.b:hover { border-color:var(--ink) }
.b.prim { background:var(--ink); color:#fff; border-color:var(--ink); font-weight:600 }
.b.ok.on { background:var(--green); color:#fff; border-color:var(--green) }
.b.resp.on { background:var(--teal); color:#fff; border-color:var(--teal) }
.b.noresp.on { background:var(--gray); color:#fff; border-color:var(--gray) }
.b.danger { color:var(--red); border-color:transparent; background:none; font-size:var(--fs-xs) }
.b.danger:hover { border-color:var(--red) }
.b:active { transform:translateY(1px) }
.copied { font-size:var(--fs-xs); color:var(--green); font-weight:600 }
.seguim { margin-top:12px; padding:12px; background:var(--plate); border-radius:10px }
.seguim-lbl { font-size:var(--fs-xs); font-weight:700; color:var(--gray); text-transform:uppercase; letter-spacing:.6px; margin-bottom:8px }
.seguim-fecha { font-size:10px; color:var(--gray); margin-top:7px }

/* CLIENT CARD */
.client-card { background:var(--bg); border:1.5px solid #d4d4d4; border-radius:14px; overflow:hidden; align-self:start }
.c-photo { width:100%; height:160px; background:var(--plate); overflow:hidden; display:flex; align-items:center; justify-content:center }
.c-photo img { width:100%; height:100%; object-fit:cover }
.c-photo .ph { font-size:var(--fs-xs); color:var(--gray); text-align:center; padding:8px }
.c-body { padding:14px }
.c-name { font-size:var(--fs-lg); font-weight:700; letter-spacing:-.3px; line-height:1.2 }
.c-sub { display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin-top:6px }
.c-tipo { font-size:var(--fs-xs); color:var(--gray); font-weight:500 }
.c-rating { font-size:var(--fs-xs); font-weight:600; color:var(--gold) }
.c-canal { font-size:10px; font-weight:700; padding:2px 7px; border-radius:999px }
.c-canal.wa { color:var(--wa); background:#e7f6ec }
.c-canal.ig { color:var(--ig); background:#fde7f0 }
.c-canal.fb { color:var(--fb); background:#e8efff }
.c-divider { height:1px; background:var(--line); margin:11px 0 }
.c-lbl { font-size:var(--fs-xs); font-weight:700; color:var(--gray); text-transform:uppercase; letter-spacing:.7px; margin-bottom:7px }
.c-rows { display:flex; flex-direction:column; gap:5px }
.c-row { display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:8px;
  background:var(--plate); border:1px solid transparent; color:var(--ink); font-size:10px; font-weight:500; cursor:pointer }
.c-row:hover { background:var(--bg); border-color:var(--line) }
.c-row-icon { width:26px; height:26px; border-radius:6px; display:flex; align-items:center; justify-content:center; flex:none }
.c-row-icon svg { width:13px; height:13px }
.i-wa { background:#e7f6ec; color:var(--wa) }
.i-ig { background:#fde7f0; color:var(--ig) }
.i-fb { background:#e8efff; color:var(--fb) }
.i-tel, .i-map { background:#f3f4f6; color:#374151 }
.c-row-body { flex:1; min-width:0 }
.c-row-title { font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis }
.c-row-desc { font-size:10px; color:var(--gray); margin-top:1px }
.c-row-tag { font-size:10px; font-weight:700; padding:1px 5px; border-radius:999px; flex:none }
.c-row-tag.cel { background:#f0f9ff; color:#0369a1 }
.c-row-tag.fijo { background:#f9f9f9; color:var(--gray) }

/* REPORTES */
.rep-view { padding:18px; max-width:760px }
.rep-view h2 { font-size:var(--fs-lg); font-weight:700; margin-bottom:14px }
.rep-item { background:var(--bg); border:1px solid var(--line); border-radius:10px; padding:12px 14px; margin-bottom:9px }
.rep-producto { font-weight:600; font-size:var(--fs-body) }
.rep-comercio { font-size:var(--fs-xs); color:var(--gray); margin-top:2px }
.rep-nota { margin-top:5px; font-size:var(--fs-sm); font-style:italic }
.rep-precios { display:flex; gap:7px; flex-wrap:wrap; margin-top:7px }
.rep-f { font-size:var(--fs-xs); padding:2px 8px; border-radius:999px; background:var(--plate); border:1px solid var(--line) }
.rep-fecha { font-size:10px; color:var(--gray); margin-top:6px }
.rep-empty { color:var(--gray); text-align:center; padding:60px 20px; font-size:var(--fs-sm) }

/* BARRA DE PROGRESO */
.prog-bar-wrap { width:100%; height:4px; background:var(--line); border-radius:999px; margin-bottom:6px; overflow:hidden }
.prog-bar { height:100%; background:var(--green); border-radius:999px; transition:width .4s ease }

/* MODO RAPIDO */
.s-row-rapido { padding:8px 13px }
.btn-rapido { font-size:11px; font-weight:700; padding:6px 12px; border-radius:7px;
  cursor:pointer; font-family:inherit; border:none; white-space:nowrap; flex:none }
.btn-wa { background:#e7f6ec; color:var(--wa) }
.btn-wa:hover { background:var(--wa); color:#fff }
.btn-ig { background:#fde7f0; color:var(--ig); text-decoration:none; display:inline-flex; align-items:center }
.btn-ig:hover { background:var(--ig); color:#fff }
.btn-fb { background:#e8efff; color:var(--fb); text-decoration:none; display:inline-flex; align-items:center }
.btn-fb:hover { background:var(--fb); color:#fff }

/* PW GATE */
#pw-gate { position:fixed; inset:0; background:#111; display:flex; align-items:center; justify-content:center; z-index:100 }
.pw-box { background:#fff; border-radius:14px; padding:28px; max-width:340px; width:100%; text-align:center }
.pw-box h2 { font-size:var(--fs-lg); font-weight:700; margin-bottom:5px }
.pw-box p { font-size:var(--fs-sm); color:var(--gray); margin-bottom:16px }
.pw-box input { width:100%; padding:10px 13px; border:1px solid var(--line); border-radius:9px;
  font-size:var(--fs-body); font-family:inherit; text-align:center; margin-bottom:10px }
.pw-box button { width:100%; padding:11px; border-radius:9px; background:var(--ink); color:#fff;
  border:none; font-size:var(--fs-body); font-weight:600; cursor:pointer; font-family:inherit }
.pw-err { color:var(--red); font-size:var(--fs-xs); margin-top:7px; display:none }

@media(max-width:720px) {
  .layout { flex-direction:column }
  .sidebar { width:100%; max-height:40vh; border-right:none; border-bottom:1px solid var(--line) }
  .detail-inner { grid-template-columns:1fr; padding:12px }
  body { overflow:auto }
}
</style>
</head>
<body>

<div id="pw-gate">
  <div class="pw-box">
    <h2>Brujula de Precios</h2>
    <p>Panel de outreach &mdash; acceso restringido</p>
    <input id="pw-inp" type="password" placeholder="Contrasena" onkeydown="if(event.key==='Enter')checkPw()">
    <button onclick="checkPw()">Ingresar</button>
    <p class="pw-err" id="pw-err">Acceso incorrecto</p>
  </div>
</div>

<div id="app" style="display:none;flex-direction:column;height:100%">
  <header>
    <div class="h-top">
      <h1>Outreach</h1>
      <span class="h-sub" id="h-sub"></span>
    </div>
    <div class="stats" id="stats"></div>
    <div class="bar">
      <input type="text" id="busq" placeholder="Buscar comercio, zona o canal..." oninput="setBusq(this.value)">
      <button class="btn-sm" onclick="exportar()">Exportar</button>
    </div>
    <div class="chips">
      <span class="chip on"       data-f="todos"        onclick="setFiltro('todos',this)">Todos</span>
      <span class="chip"          data-f="pendiente"    onclick="setFiltro('pendiente',this)">Pendiente</span>
      <span class="chip c-green"  data-f="aprobado"     onclick="setFiltro('aprobado',this)">Aprobado</span>
      <span class="chip c-purple" data-f="enviado"      onclick="setFiltro('enviado',this)">Enviado</span>
      <span class="chip c-teal"   data-f="respondio"    onclick="setFiltro('respondio',this)">Respondio</span>
      <span class="chip"          data-f="no_respondio" onclick="setFiltro('no_respondio',this)">No respondio</span>
      <span class="chip c-red"    data-f="cancelado"    onclick="setFiltro('cancelado',this)">Cancelado</span>
      <span class="chip c-amber"  data-f="reportes"     onclick="setFiltro('reportes',this)">Reportes de precios</span>
    </div>
    <div class="chips" style="margin-top:4px">
      <span style="font-size:10px;color:var(--gray);align-self:center;margin-right:2px">Canal:</span>
      <span class="chip chip-canal on" data-canal="todos" onclick="setCanal('todos',this)">Todos</span>
      <span class="chip chip-canal c-green" data-canal="WhatsApp" onclick="setCanal('WhatsApp',this)">WhatsApp</span>
      <span class="chip chip-canal c-teal" data-canal="Instagram" onclick="setCanal('Instagram',this)">Instagram</span>
      <span class="chip chip-canal c-purple" data-canal="Facebook" onclick="setCanal('Facebook',this)">Facebook</span>
      <span class="chip chip-canal" data-canal="digital" onclick="setCanal('digital',this)">Solo digitales</span>
      <span class="chip chip-rapido" onclick="toggleRapido(this)" style="margin-left:auto">&#9889; Modo rapido</span>
    </div>
  </header>
  <div class="layout">
    <div class="sidebar" id="sidebar"></div>
    <div class="detail"  id="detail"></div>
  </div>
</div>

<script type="application/json" id="pool-data">__POOL_JSON__</script>
<script>
__MAIN_JS__
</script>
</body>
</html>'''

JS_FILE = r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\scripts\panel_outreach_app.js"
with open(JS_FILE, encoding="utf-8") as f:
    main_js = f.read()
HTML = HTML.replace("__MAIN_JS__",        main_js)

# Inyectar datos
HTML = HTML.replace("__POOL_JSON__",      pool_json)
HTML = HTML.replace("__DATA_COMERCIOS__", line_comercios)
HTML = HTML.replace("__DATA_PREFIJO__",   line_prefijo)
HTML = HTML.replace("__DATA_SUFIJO__",    line_sufijo)

for out_path in OUTS:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(HTML)
    print(f"OK: {out_path.split(chr(92))[-1]}")
print("Rebuild completo.")
