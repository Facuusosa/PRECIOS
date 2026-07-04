import json, re

def extract_ig_handle(url):
    if not url: return ""
    m = re.search(r'instagram\.com/([^/?]+)', url)
    return m.group(1) if m else ""

def extract_fb_page(url):
    if not url: return ""
    m = re.search(r'facebook\.com/([^/?]+)', url)
    page = m.group(1) if m else ""
    return page if page not in ["sharer", "share", "dialog"] else ""

def extract_wa_number(url):
    if not url: return ""
    m = re.search(r'wa\.me/(\d+)', url)
    return m.group(1) if m else ""

def to_float(s):
    try: return float(s)
    except: return 0.0

with open(r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\comercios_10km_20260618_enriquecido.json", encoding="utf-8") as f:
    data = json.load(f)

comercios_panel = []
for c in data["comercios"]:
    comercios_panel.append({
        "nombre": c.get("nombre", ""),
        "tipo": c.get("categoria", ""),
        "direccion": c.get("direccion", ""),
        "zona": c.get("zona", ""),
        "rating": to_float(c.get("rating", "0")),
        "reviews": c.get("reviews", ""),
        "canal": c.get("canal", "sin_contacto"),
        "telefono": c.get("telefono", ""),
        "es_celular": c.get("es_celular", False),
        "whatsapp": extract_wa_number(c.get("whatsapp", "")),
        "instagram": extract_ig_handle(c.get("instagram", "")),
        "facebook": extract_fb_page(c.get("facebook", "")),
        "website": c.get("website", ""),
        "foto_url": c.get("foto_url", ""),
        "foto_local": "",
        "url_maps": c.get("url_maps", ""),
        "horario": c.get("horario", ""),
        "estado": c.get("estado", "pendiente"),
        "nota": ""
    })

nueva_linea = "const COMERCIOS = " + json.dumps(comercios_panel, ensure_ascii=False, separators=(',', ':')) + ";\n"

html_paths = [
    r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\panel_outreach.html",
    r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\public\outreach.html",
]

for html_path in html_paths:
    with open(html_path, encoding="utf-8") as f:
        lines = f.readlines()
    nuevas_lineas = []
    for line in lines:
        if line.strip().startswith("const COMERCIOS = ["):
            nuevas_lineas.append(nueva_linea)
        elif "c.foto_local" in line and "foto_url" not in line:
            nueva = line.replace(
                'c.foto_local ? `<img src="${c.foto_local}"',
                '(c.foto_local || c.foto_url) ? `<img src="${c.foto_local || c.foto_url}"'
            )
            nuevas_lineas.append(nueva)
        else:
            nuevas_lineas.append(line)
    with open(html_path, "w", encoding="utf-8") as f:
        f.writelines(nuevas_lineas)
    print(f"OK: {html_path.split(chr(92))[-1]}")

print(f"Total: {len(comercios_panel)} comercios escritos.")
total_wa = sum(1 for c in comercios_panel if c["whatsapp"])
total_ig = sum(1 for c in comercios_panel if c["instagram"])
total_fb = sum(1 for c in comercios_panel if c["facebook"])
total_tel = sum(1 for c in comercios_panel if c["telefono"])
total_foto = sum(1 for c in comercios_panel if c["foto_url"])
print(f"WhatsApp: {total_wa} | Instagram: {total_ig} | Facebook: {total_fb} | Tel fijo: {total_tel} | Con foto: {total_foto}")
