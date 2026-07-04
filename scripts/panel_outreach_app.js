// panel_outreach_app.js — JS del panel de outreach
// Archivo separado para evitar escaping Python en triple-quoted strings.
// Los placeholders __DATA_COMERCIOS__, __DATA_PREFIJO__, __DATA_SUFIJO__ son inyectados
// por rebuild_panel.py via .replace() antes de embedder este archivo en el HTML.

// ===== DATOS =====
__DATA_COMERCIOS__
const POOL = JSON.parse(document.getElementById('pool-data').textContent);
__DATA_PREFIJO__
__DATA_SUFIJO__
var BYNAME = {};
POOL.forEach(function(p) { BYNAME[p.producto] = p; });

// ===== AUTH =====
var params = new URLSearchParams(location.search);
var CORRECT_PW = "brujula2025";
function checkPw() {
  var v = (document.getElementById("pw-inp") ? document.getElementById("pw-inp").value : "") || params.get("pw") || "";
  if (v === CORRECT_PW) {
    document.getElementById("pw-gate").style.display = "none";
    var app = document.getElementById("app");
    app.style.display = "flex";
    init();
  } else {
    var e = document.getElementById("pw-err");
    if (e) e.style.display = "block";
  }
}
(function() { if (params.get("pw") === CORRECT_PW) checkPw(); })();

// ===== STATE =====
var KEY  = "outreach_brujula_v4";
var RKEY = "outreach_reportes_v4";
var estado   = JSON.parse(localStorage.getItem(KEY)  || "{}");
var reportes = JSON.parse(localStorage.getItem(RKEY) || "[]");
var filtro   = "todos";
var canalFiltro = "todos";
var modoRapido = false;
var busqueda = "";
var selected = -1;
var API = "/api/outreach?pw=" + encodeURIComponent(params.get("pw") || "");

function init() {
  fetch(API).then(function(r) {
    if (!r.ok) return;
    return r.json();
  }).then(function(data) {
    if (!data) return;
    if (data.estado)   { estado   = data.estado;   localStorage.setItem(KEY,  JSON.stringify(estado)); }
    if (data.reportes) { reportes = data.reportes; localStorage.setItem(RKEY, JSON.stringify(reportes)); }
    render();
  }).catch(function() {}).finally(function() { render(); });
}

function guardar() {
  localStorage.setItem(KEY,  JSON.stringify(estado));
  localStorage.setItem(RKEY, JSON.stringify(reportes));
  fetch(API, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({estado:estado, reportes:reportes})}).catch(function(){});
}

function st(n) {
  if (!estado[n]) estado[n] = {status:"pendiente", material:null, mensaje:null};
  return estado[n];
}
function materialDe(c) {
  var s = st(c.nombre);
  if (s.material && BYNAME[s.material]) return s.material;
  if (c.default && BYNAME[c.default]) return c.default;
  // Rotar entre los primeros 10 bombas del pool para que cada comercio muestre un producto distinto
  var topN = Math.min(10, POOL.length);
  var hash = 0;
  for (var i = 0; i < (c.nombre||"").length; i++) hash = (hash * 31 + c.nombre.charCodeAt(i)) & 0xffff;
  var idx = hash % topN;
  return POOL[idx] ? POOL[idx].producto : (POOL[0] ? POOL[0].producto : "");
}
function mensajeDe(c) {
  var m = BYNAME[materialDe(c)];
  var prefijo = PREFIJO.replace("__NOMBRE__", c.nombre || "");
  return prefijo + (m ? m.frase : "") + SUFIJO;
}
function plata(n)  { return "$" + (n||0).toLocaleString("es-AR"); }
function jq(s)     { var o=""; for(var i=0;i<(s||"").length;i++){var c=s[i];if(c==="'")o+="&#39;";else if(c==='"')o+="&quot;";else o+=c;} return o; }
function canalCls(c) { return c && c.indexOf("WhatsApp")>=0?"wa":c && c.indexOf("Instagram")>=0?"ig":c && c.indexOf("Facebook")>=0?"fb":""; }

// ===== FILTRADO =====
function setFiltro(f, el) {
  filtro = f; selected = -1;
  document.querySelectorAll(".chip:not(.chip-canal)").forEach(function(c) { c.classList.remove("on"); });
  if (el) el.classList.add("on");
  render();
}
function setCanal(canal, el) {
  canalFiltro = canal; selected = -1;
  document.querySelectorAll(".chip-canal").forEach(function(c) { c.classList.remove("on"); });
  if (el) el.classList.add("on");
  render();
}
function toggleRapido(el) {
  modoRapido = !modoRapido;
  el.classList.toggle("on", modoRapido);
  // En modo rapido: forzar filtro digital y colapsar detail
  if (modoRapido) {
    document.getElementById("detail").style.display = "none";
    document.querySelector(".sidebar").style.width = "100%";
    document.querySelector(".sidebar").style.borderRight = "none";
  } else {
    document.getElementById("detail").style.display = "";
    document.querySelector(".sidebar").style.width = "";
    document.querySelector(".sidebar").style.borderRight = "";
  }
  render();
}
function setBusq(v) { busqueda = v.toLowerCase(); selected = -1; render(); }

function getFiltrado() {
  var out = [];
  for (var i = 0; i < COMERCIOS.length; i++) {
    var c = COMERCIOS[i];
    var s = st(c.nombre);
    if (filtro !== "todos" && filtro !== "reportes" && s.status !== filtro) continue;
    if (canalFiltro === "digital") {
      var esDigital = c.canal && (c.canal.indexOf("WhatsApp") >= 0 || c.canal.indexOf("Instagram") >= 0 || c.canal.indexOf("Facebook") >= 0);
      if (!esDigital) continue;
    } else if (canalFiltro !== "todos") {
      if (!c.canal || c.canal.indexOf(canalFiltro) < 0) continue;
    }
    if (busqueda) {
      var hay = ((c.nombre||"") + (c.zona||"") + (c.canal||"") + (c.direccion||"")).toLowerCase();
      if (hay.indexOf(busqueda) < 0) continue;
    }
    out.push({c:c, i:i});
  }
  return out;
}

// ===== SIDEBAR =====
function canalEmoji(canal) {
  if (!canal) return "&#128205;";
  if (canal.indexOf("WhatsApp")  >= 0) return "&#128242;";
  if (canal.indexOf("Instagram") >= 0) return "&#128247;";
  if (canal.indexOf("Facebook")  >= 0) return "&#128279;";
  if (canal === "celular" || canal === "fijo") return "&#128222;";
  return "&#128205;";
}

function renderSidebar() {
  var sb = document.getElementById("sidebar");
  if (filtro === "reportes") { sb.innerHTML = ""; return; }
  var lista = getFiltrado();
  if (!lista.length) { sb.innerHTML = '<div class="s-empty">Sin resultados</div>'; return; }
  var html = "";
  for (var k = 0; k < lista.length; k++) {
    var c = lista[k].c;
    var i = lista[k].i;
    var s = st(c.nombre);
    var stcls = s.status !== "pendiente" ? " st-" + s.status : "";
    var actcls = selected === i ? " sel" + stcls : "";
    var badge = s.status !== "pendiente" ? '<span class="s-badge ' + s.status + '">' + s.status + '</span>' : "";
    var rating = c.rating ? " &middot; &#11088;" + c.rating : "";
    if (modoRapido) {
      // Modo rapido: fila expandida con boton WA directo
      var btnR = "";
      if (c.whatsapp) {
        btnR = '<button class="btn-rapido btn-wa" onclick="event.stopPropagation();abrirWA(\'' + jq(c.nombre) + '\',' + i + ')">WA &rarr;</button>';
      } else if (c.instagram) {
        btnR = '<a class="btn-rapido btn-ig" href="https://ig.me/m/' + c.instagram + '" target="_blank" onclick="event.stopPropagation()">IG &rarr;</a>';
      } else if (c.facebook) {
        btnR = '<a class="btn-rapido btn-fb" href="https://m.me/' + c.facebook + '" target="_blank" onclick="event.stopPropagation()">FB &rarr;</a>';
      }
      html += '<div class="s-row s-row-rapido' + actcls + '" onclick="seleccionar(' + i + ')">'
        + '<div class="s-icon">' + canalEmoji(c.canal) + '</div>'
        + '<div class="s-body">'
        + '<div class="s-name">' + (c.nombre||"") + '</div>'
        + '<div class="s-meta">' + (c.zona||"") + rating + '</div>'
        + '</div>'
        + badge + btnR + '</div>';
    } else {
      html += '<div class="s-row' + actcls + '" onclick="seleccionar(' + i + ')">'
        + '<div class="s-icon">' + canalEmoji(c.canal) + '</div>'
        + '<div class="s-body">'
        + '<div class="s-name">' + (c.nombre||"") + '</div>'
        + '<div class="s-meta">' + (c.tipo||"") + (c.zona ? " &middot; " + c.zona : "") + rating + '</div>'
        + '</div>' + badge + '</div>';
    }
  }
  sb.innerHTML = html;
}

// ===== DETAIL =====
function seleccionar(idx) { selected = idx; render(); }

function renderDetail() {
  var det = document.getElementById("detail");
  if (filtro === "reportes") { renderReportes(); return; }
  if (selected < 0 || selected >= COMERCIOS.length) {
    det.innerHTML = '<div class="detail-empty"><div><div style="font-size:2rem;margin-bottom:10px">&#128204;</div>Selecciona un comercio de la lista</div></div>';
    return;
  }
  var c = COMERCIOS[selected];
  var i = selected;
  var s = st(c.nombre);
  det.innerHTML = '<div class="detail-inner">' + buildWork(c, i, s) + buildClientCard(c) + '</div>';
  var inp = document.getElementById("inp" + i);
  if (inp) {
    inp.addEventListener("focus", function() { ac(i, c.nombre); });
    inp.addEventListener("blur",  function() { setTimeout(function() { cerrarAc(i); }, 200); });
    inp.addEventListener("input", function() { ac(i, c.nombre); });
  }
  var ta = document.getElementById("ta" + i);
  if (ta && s.mensaje) ta.value = s.mensaje;
}

function buildWork(c, i, s) {
  var m   = BYNAME[materialDe(c)];
  var sugsHtml = "";
  if (c.sugeridos && c.sugeridos.length) {
    var sugs = c.sugeridos.map(function(sg) {
      return '<span class="sug" onclick="setMat(\'' + jq(c.nombre) + '\',\'' + jq(sg) + '\')">' + sg.split(" ").slice(0,3).join(" ") + '</span>';
    });
    sugsHtml = '<div class="sugs">' + sugs.join("") + '</div>';
  }

  var ejHtml = "";
  if (m) {
    // fuentes puede ser array [{may,precio,link}] o legado objeto {Nombre:precio}
    var fuentesArr = Array.isArray(m.fuentes)
      ? m.fuentes.filter(function(f){ return f.precio > 0; }).slice().sort(function(a,b){ return a.precio-b.precio; })
      : (m.fuentes ? Object.entries(m.fuentes).filter(function(e){ return e[1]>0; }).sort(function(a,b){ return a[1]-b[1]; })
          .map(function(e){ return {may:e[0], precio:e[1], link: m.links&&m.links[e[0]] ? m.links[e[0]] : "#"}; }) : []);
    var ps  = fuentesArr.map(function(f){ return f.precio; });
    var mn  = ps.length ? Math.min.apply(null, ps) : 0;
    var mx  = ps.length ? Math.max.apply(null, ps) : 0;
    var pct = mx ? Math.round((mx - mn) / mx * 100) : 0;
    var ahorroHtml = ps.length >= 2 && pct > 0
      ? '<div style="margin-top:5px"><span class="ahpill">Ahorro ' + plata(mx-mn) + ' &middot; ' + pct + '%</span></div>' : "";

    var linkHtml = "";
    for (var ei = 0; ei < fuentesArr.length; ei++) {
      var f = fuentesArr[ei];
      var href = f.link || "#";
      linkHtml += '<a class="lk' + (ei===0?' best':'') + '" href="' + href + '" target="_blank"><b>' + f.may + '</b> ' + plata(f.precio) + '</a>';
    }

    ejHtml = '<div class="ejbox">'
      + (m.imagen ? '<div class="ejthumb"><img src="' + m.imagen + '" onerror="this.style.display=\'none\'"></div>' : '')
      + '<div class="ejinfo">'
      + '<div class="ejprod">' + m.producto + (m.abc==="A" ? '<span class="abadge">TOP A</span>' : '') + '</div>'
      + ahorroHtml
      + '<div class="links" style="margin-top:7px">' + linkHtml + '</div>'
      + '<button class="report" onclick="reportar(\'' + jq(c.nombre) + '\',\'' + jq(m.producto) + '\')">&#9873; Reportar precio incorrecto</button>'
      + '</div></div>';
  }

  var msgActual = s.mensaje || mensajeDe(c);
  var btnAprob  = '<button class="b ok' + (s.status==='aprobado'?' on':'') + '" onclick="aprobar(\'' + jq(c.nombre) + '\',' + i + ')">' + (s.status==='aprobado'?'&#10003; Aprobado':'Aprobar') + '</button>';
  var btnCopiar = '<button class="b" onclick="copiar(' + i + ',this)">Copiar mensaje</button>';
  var btnEnviar = '<button class="b" onclick="marcarEnviado(\'' + jq(c.nombre) + '\')">' + (s.status==='enviado'||s.status==='respondio'||s.status==='no_respondio'?'&#10003; Marcado enviado':'Marcar enviado') + '</button>';
  var btnWA = c.whatsapp
    ? '<a class="b prim" href="#" onclick="abrirWA(\'' + jq(c.nombre) + '\',' + i + ');return false;" style="text-decoration:none">Abrir WhatsApp &rarr;</a>'
    : (c.instagram
      ? '<a class="b prim" href="https://ig.me/m/' + c.instagram + '" target="_blank" style="text-decoration:none">Abrir Instagram DM &rarr;</a>'
      : (c.facebook
        ? '<a class="b prim" href="https://m.me/' + c.facebook + '" target="_blank" style="text-decoration:none">Abrir Messenger &rarr;</a>'
        : ''));

  var seguimHtml = "";
  if (s.status==='enviado'||s.status==='respondio'||s.status==='no_respondio') {
    var fuHtml = "";
    if (s.fecha_followup) {
      var fuDate = new Date(s.fecha_followup);
      var hoy = new Date(); hoy.setHours(0,0,0,0);
      var diff = Math.ceil((fuDate - hoy) / 86400000);
      var fuLabel = diff > 0 ? "Follow-up en " + diff + " dia" + (diff>1?"s":"")
                  : diff === 0 ? "&#9888; Follow-up HOY"
                  : "&#9888; Follow-up vencido hace " + Math.abs(diff) + " dia" + (Math.abs(diff)>1?"s":"");
      fuHtml = '<div class="seguim-fecha" style="' + (diff<=0?'color:var(--red);font-weight:600':'') + '">' + fuLabel + '</div>';
    }
    seguimHtml = '<div class="seguim">'
      + '<div class="seguim-lbl">Seguimiento</div>'
      + '<div style="display:flex;gap:7px;flex-wrap:wrap">'
      + '<button class="b resp' + (s.status==='respondio'?' on':'') + '" onclick="marcarRespondio(\'' + jq(c.nombre) + '\')">' + (s.status==='respondio'?'&#10003; Respondio':'Respondio') + '</button>'
      + '<button class="b noresp' + (s.status==='no_respondio'?' on':'') + '" onclick="marcarNoRespondio(\'' + jq(c.nombre) + '\')">' + (s.status==='no_respondio'?'&#10003; No respondio':'No respondio') + '</button>'
      + '</div>'
      + (s.fecha ? '<div class="seguim-fecha">Enviado: ' + new Date(s.fecha).toLocaleDateString("es-AR") + '</div>' : '')
      + fuHtml
      + '</div>';
  }

  return '<div class="work">'
    + '<div class="lab">Material del mensaje &mdash; escribi cualquier producto</div>'
    + '<div class="ac"><input id="inp' + i + '" autocomplete="off" placeholder="' + jq(m ? m.producto : "Buscar producto...") + '"></div>'
    + sugsHtml
    + ejHtml
    + '<div class="msg"><div class="lab" style="margin-bottom:6px">Mensaje &mdash; editalo libremente</div>'
    + '<textarea id="ta' + i + '" onchange="guardarMsg(\'' + jq(c.nombre) + '\',' + i + ')">' + msgActual.replace(/</g,"&lt;") + '</textarea>'
    + '</div>'
    + '<div class="acciones">' + btnWA + btnAprob + btnCopiar + btnEnviar + '<button class="b danger" onclick="cancelar(\'' + jq(c.nombre) + '\')">Cancelar</button></div>'
    + seguimHtml
    + '</div>';
}

function buildClientCard(c) {
  var cls  = canalCls(c.canal);
  var foto = c.foto_local || c.foto_url || "";
  var fotoHtml = foto
    ? '<img src="' + foto + '" onerror="this.style.display=\'none\'">'
    : '<div class="ph">Sin foto disponible</div>';

  var rows = "";
  if (c.whatsapp) rows += '<a class="c-row" href="https://wa.me/' + c.whatsapp + '" target="_blank"><div class="c-row-icon i-wa"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></div><div class="c-row-body"><div class="c-row-title">WhatsApp</div><div class="c-row-desc">+' + c.whatsapp + '</div></div><span class="c-row-tag cel">Principal</span></a>';
  if (c.instagram) rows += '<a class="c-row" href="https://instagram.com/' + c.instagram + '" target="_blank"><div class="c-row-icon i-ig"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg></div><div class="c-row-body"><div class="c-row-title">Instagram</div><div class="c-row-desc">@' + c.instagram + '</div></div></a>';
  if (c.facebook)  rows += '<a class="c-row" href="https://facebook.com/' + c.facebook + '" target="_blank"><div class="c-row-icon i-fb"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></div><div class="c-row-body"><div class="c-row-title">Facebook</div><div class="c-row-desc">' + c.facebook + '</div></div></a>';
  if (c.telefono)  rows += '<div class="c-row"><div class="c-row-icon i-tel"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.81a19.79 19.79 0 01-3.07-8.68A2 2 0 012 .84h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.09 8.53a16 16 0 006 6l1.06-1.06a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 15.84l-.08 1.08z"/></svg></div><div class="c-row-body"><div class="c-row-title">' + c.telefono + '</div><div class="c-row-desc">' + (c.es_celular?"Celular":"Fijo") + '</div></div><span class="c-row-tag ' + (c.es_celular?"cel":"fijo") + '">' + (c.es_celular?"Celular":"Fijo") + '</span></div>';
  if (c.website)   rows += '<a class="c-row" href="' + c.website + '" target="_blank"><div class="c-row-icon i-map"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg></div><div class="c-row-body"><div class="c-row-title">Sitio web</div></div></a>';
  rows += '<a class="c-row" href="https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent((c.nombre||"") + " " + (c.direccion||"") + " CABA") + '" target="_blank"><div class="c-row-icon i-map"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg></div><div class="c-row-body"><div class="c-row-title">' + (c.direccion||"Ver en Maps") + '</div><div class="c-row-desc">' + (c.zona||"") + '</div></div></a>';

  return '<div class="client-card">'
    + '<div class="c-photo">' + fotoHtml + '</div>'
    + '<div class="c-body">'
    + '<div class="c-name">' + (c.nombre||"") + '</div>'
    + '<div class="c-sub">'
    + '<span class="c-tipo">' + (c.tipo||"") + '</span>'
    + (c.rating ? '<span class="c-rating">&#11088; ' + c.rating + '</span>' : '')
    + (c.canal && c.canal!=="sin_contacto" ? '<span class="c-canal ' + cls + '">' + c.canal + '</span>' : '')
    + '</div>'
    + '<div class="c-divider"></div>'
    + '<div class="c-lbl">Contacto</div>'
    + '<div class="c-rows">' + (rows || '<div style="font-size:10px;color:var(--gray);padding:6px 0">Sin datos de contacto</div>') + '</div>'
    + (c.horario ? '<div style="margin-top:9px;font-size:10px;color:var(--gray);padding:7px 9px;background:#eceae7;border-radius:7px">&#128337; ' + c.horario + '</div>' : '')
    + '</div></div>';
}

// ===== REPORTES =====
function renderReportes() {
  var det = document.getElementById("detail");
  if (!reportes.length) {
    det.innerHTML = '<div class="rep-view"><div class="rep-empty">No hay reportes de precios todavia</div></div>';
    return;
  }
  var html = '<div class="rep-view"><h2>Reportes de precios (' + reportes.length + ')</h2>';
  var rev = reportes.slice().reverse();
  for (var ri = 0; ri < rev.length; ri++) {
    var r = rev[ri];
    var fuentes = "";
    if (r.fuentes) {
      Object.entries(r.fuentes).forEach(function(e) {
        if (e[1] > 0) fuentes += '<span class="rep-f"><b>' + e[0] + '</b> ' + plata(e[1]) + '</span>';
      });
    }
    html += '<div class="rep-item">'
      + '<div class="rep-producto">' + (r.producto||"") + '</div>'
      + '<div class="rep-comercio">Reportado por: ' + (r.comercio||"") + '</div>'
      + (r.nota ? '<div class="rep-nota">"' + r.nota + '"</div>' : '')
      + (fuentes ? '<div class="rep-precios">' + fuentes + '</div>' : '')
      + '<div class="rep-fecha">' + new Date(r.fecha).toLocaleString("es-AR") + '</div>'
      + '</div>';
  }
  det.innerHTML = html + '</div>';
}

// ===== RENDER =====
function render() {
  actualizarStats();
  renderSidebar();
  renderDetail();
}

function actualizarStats() {
  var counts = {pendiente:0, aprobado:0, enviado:0, respondio:0, no_respondio:0, cancelado:0};
  COMERCIOS.forEach(function(c) {
    var status = st(c.nombre).status;
    if (counts[status] !== undefined) counts[status]++;
  });
  var conContacto = COMERCIOS.filter(function(c) { return c.canal && c.canal !== "sin_contacto"; }).length;
  var totalEnviados = counts.enviado + counts.respondio + counts.no_respondio;
  var pctEnviado = conContacto > 0 ? Math.round(totalEnviados / conContacto * 100) : 0;
  var pctResp = totalEnviados > 0 ? Math.round(counts.respondio / totalEnviados * 100) : 0;

  document.getElementById("h-sub").textContent = COMERCIOS.length + " comercios · " + conContacto + " con contacto digital";

  // Barra de progreso
  var barHtml = '<div class="prog-bar-wrap" title="' + totalEnviados + ' de ' + conContacto + ' contactos digitales enviados">'
    + '<div class="prog-bar" style="width:' + pctEnviado + '%"></div>'
    + '</div>';

  var s = barHtml
    + '<span>Pendiente <b>' + counts.pendiente + '</b></span>'
    + '<span>Enviado <b>' + totalEnviados + '</b></span>'
    + (counts.respondio > 0 ? '<span style="color:var(--green)">Respondio <b>' + counts.respondio + '</b> <b>(' + pctResp + '%)</b></span>' : '')
    + (counts.no_respondio > 0 ? '<span>Sin resp. <b>' + counts.no_respondio + '</b></span>' : '')
    + (counts.aprobado > 0 ? '<span>Aprobado <b>' + counts.aprobado + '</b></span>' : '')
    + (counts.cancelado > 0 ? '<span>Cancelado <b>' + counts.cancelado + '</b></span>' : '');
  if (reportes.length) s += '<span class="stat-rep" onclick="setFiltro(\'reportes\',document.querySelector(\'[data-f=reportes]\'))">&#9873; ' + reportes.length + ' reportes</span>';
  document.getElementById("stats").innerHTML = s;
}

// ===== ACCIONES =====
function guardarMsg(n, i) {
  var ta = document.getElementById("ta" + i);
  if (ta) { st(n).mensaje = ta.value; guardar(); }
}
function aprobar(n, i) {
  var ta = document.getElementById("ta" + i);
  if (ta) st(n).mensaje = ta.value;
  st(n).status = (st(n).status === "aprobado") ? "pendiente" : "aprobado";
  guardar(); render();
}
function abrirWA(n, i) {
  var ta = document.getElementById("ta" + i);
  var c = COMERCIOS[i];
  if (!c || !c.whatsapp) return;
  var txt = ta ? ta.value : mensajeDe(c);
  if (ta) { st(n).mensaje = ta.value; }
  window.open("https://wa.me/" + c.whatsapp + "?text=" + encodeURIComponent(txt), "_blank");
  marcarEnviado(n);
}

function marcarEnviado(n) {
  if (st(n).status !== "enviado" && st(n).status !== "respondio" && st(n).status !== "no_respondio") {
    st(n).status = "enviado";
    st(n).fecha  = new Date().toISOString();
    var fu = new Date(); fu.setDate(fu.getDate() + 3);
    st(n).fecha_followup = fu.toISOString();
    guardar(); render();
  }
}
function marcarRespondio(n) {
  st(n).status = (st(n).status === "respondio") ? "enviado" : "respondio";
  guardar(); render();
}
function marcarNoRespondio(n) {
  st(n).status = (st(n).status === "no_respondio") ? "enviado" : "no_respondio";
  guardar(); render();
}
function cancelar(n) {
  if (confirm("Cancelar este comercio?")) { st(n).status = "cancelado"; guardar(); render(); }
}
function copiar(i, btn) {
  var ta = document.getElementById("ta" + i);
  if (!ta) return;
  ta.select();
  navigator.clipboard.writeText(ta.value).then(function() {
    btn.outerHTML = '<span class="copied">&#10003; Copiado</span>';
    setTimeout(render, 1100);
  }).catch(function() { document.execCommand("copy"); });
}
function reportar(n, prod) {
  var nota = prompt('Precio incorrecto en "' + prod + '"\nDescribi el problema (opcional):');
  if (nota === null) return;
  reportes.push({comercio:n, producto:prod, nota:nota, fecha:new Date().toISOString(), fuentes:BYNAME[prod] ? BYNAME[prod].fuentes : null});
  guardar(); render();
  alert("Reporte guardado.");
}

// ===== AUTOCOMPLETE =====
function ac(i, nombre) {
  var inp = document.getElementById("inp" + i);
  var box = document.getElementById("acl" + i);
  if (!inp || !box) return;
  var q = inp.value.toLowerCase();
  var res = POOL.filter(function(p) { return p.producto.toLowerCase().indexOf(q) >= 0; }).slice(0, 10);
  if (!res.length) { box.classList.remove("show"); return; }
  box.innerHTML = res.map(function(p) {
    var ps  = p.fuentes ? Object.values(p.fuentes).filter(function(v) { return v > 0; }) : [];
    var mn  = ps.length ? Math.min.apply(null, ps) : 0;
    var mx  = ps.length ? Math.max.apply(null, ps) : 0;
    var pct = mx ? Math.round((mx - mn) / mx * 100) : 0;
    var cls = pct >= 25 ? "pg" : pct > 0 ? "pw" : "";
    return '<div class="ac-item" onmousedown="setMat(\'' + jq(nombre) + '\',\'' + jq(p.producto) + '\')">'
      + p.producto + (pct ? '<small class="' + cls + '">' + pct + '% ahorro</small>' : '') + '</div>';
  }).join("");
  box.classList.add("show");
}
function cerrarAc(i) { var b = document.getElementById("acl" + i); if (b) b.classList.remove("show"); }
function setMat(n, prod) {
  var s = st(n); s.material = prod; s.mensaje = null;
  guardar(); render();
}

// ===== EXPORT =====
function exportar() {
  var out = {
    fecha: new Date().toISOString(),
    comercios: COMERCIOS.map(function(c) { return Object.assign({nombre:c.nombre, canal:c.canal, tipo:c.tipo}, st(c.nombre)); }),
    reportes: reportes
  };
  var blob = new Blob([JSON.stringify(out, null, 2)], {type:"application/json"});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "estado_outreach_" + new Date().toISOString().slice(0,10) + ".json";
  a.click();
}
