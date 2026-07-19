"""
Genera 6 archivos HTML standalone (uno por historia), a full resolucion 1080x1920,
listos para que Puppeteer los screenshotee y queden como PNG para publicar.

Toma el contenido real de plantilla-historia.html (la galeria de revision con las
6 .story dentro de mockups de telefono) y aisla cada .story en su propia pagina,
con zoom:3.6 para escalar el diseño (pensado a 300px) al tamaño real de una historia.
"""
import base64
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
PLANTILLA = BASE_DIR / "plantilla-historia.html"
FUENTES_DIR = BASE_DIR / "fuentes"
FRAMES_DIR = BASE_DIR / "frames-ejemplo"
OUT_DIR = BASE_DIR / "output-historias"

FUENTES = [
    ("poppins-400", "__FONT400__"),
    ("poppins-600", "__FONT600__"),
    ("poppins-700", "__FONT700__"),
    ("poppins-800", "__FONT800__"),
    ("unbounded-700", "__UNBOUNDED700__"),
    ("unbounded-900", "__UNBOUNDED900__"),
]

GIFS = [
    ("historia2.gif", "__RECORRIDO_GIF__"),
    ("historia4.gif", "__H4GIF__"),
    ("historia5.gif", "__H5GIF__"),
]

HISTORIAS = [
    (1, "1-gancho"),
    (2, "2-prueba-real"),
    (3, "3-patron"),
    (4, "4-canasta"),
    (5, "5-remate"),
    (6, "6-cierre"),
]

DIV_OPEN_RE = re.compile(r"<div\b")
DIV_CLOSE = "</div>"


def extraer_story_divs(html: str) -> list[str]:
    """Encuentra cada <div class="story ..."> y devuelve su bloque completo
    balanceando divs anidados (no depende de numeros de linea)."""
    resultados = []
    for m in re.finditer(r'<div class="story\b[^"]*">', html):
        start = m.start()
        pos = m.end()
        depth = 1
        while depth > 0:
            next_open = DIV_OPEN_RE.search(html, pos)
            next_close = html.find(DIV_CLOSE, pos)
            if next_open and next_open.start() < next_close:
                depth += 1
                pos = next_open.end()
            else:
                depth -= 1
                pos = next_close + len(DIV_CLOSE)
        resultados.append(html[start:pos])
    return resultados

EXPORT_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
{style_block}
html, body {{ margin: 0; padding: 0; background: #000; }}
/* 282px = ancho INTERNO real del mockup .phone del artifact (300 - 2x9 de bisel).
   zoom = 1080/282 (fijo, no cambia con la altura del canvas -- convierte px de
   diseno a px reales 1:1 sin importar el alto). Canvas final: 1080x1920 (9:16
   REAL, lo que Instagram usa siempre en su compositor de Historias -- ver nota
   grande mas abajo sobre por que esto reemplazo el 1080x2340 del 19/07). */
.export-wrap {{
  width: 282px;
  height: 501.333px;
  overflow: hidden;
  zoom: 3.8297872;
}}
/* v8 (pedido Facu 19/07): badge y footer mas pegados a los bordes — quedaba mucho
   aire arriba y abajo. OJO: esto come margen de la zona segura de IG (usuario arriba,
   caja de respuesta abajo, ~150-250px reales); si en la historia PUBLICADA la UI de
   IG pisa el badge o el footer, volver a 52/68. */
.export-wrap .story {{ width: 100%; height: 100%; border-radius: 0;
                       padding-top: 36px; padding-bottom: 50px; }}
/* La barra de progreso dibujada solo sirve en la maqueta de revision: publicada,
   Instagram superpone SU barra real y quedan dos (visto en captura del 19/07). */
.export-wrap .progress {{ display: none; }}
/* v10 (decision estetica Facu 19/07): la captura de la app es TARJETA enmarcada
   (margenes laterales + border-radius + borde del CSS base, como en la galeria
   de revision) — el full-bleed v7/v8 le gustaba menos, se mezclaba con el fondo.
   El resto de la v8 (texto ~12% mas grande, paddings 36/50) se mantiene. */
.export-wrap .eyebrow {{ font-size: 11px; align-items: flex-start; }}
/* Con eyebrows de 2-3 lineas el guion centrado quedaba flotando en el medio:
   fijado a la altura optica de la primera linea. */
.export-wrap .eyebrow::before {{ margin-top: 0.62em; }}
.export-wrap .story.c h2.headline {{ font-size: 25px; }}
.export-wrap .story.c .sub2 {{ font-size: 13px; }}
.export-wrap h2.headline.display {{ font-size: 26px; }}
.export-wrap .sub {{ font-size: 15px; }}
/* v12 (19:19.5 -> 9:16 real, canvas 501.3px de diseno en vez de 611px): historia 3
   (patron) media 77px de diseno de overflow con los valores de v10 -- recorte real,
   no cosmetico. Headline mas chico + menos aire entre bloques + filas de precio mas
   compactas; el texto del teaser no se toco (no es copy dictado, pero se dejo intacto
   por las dudas). */
.export-wrap .content.h3-text .headline.display {{ font-size: 16px; margin-bottom: 8px; }}
.export-wrap .content.h3-text .eyebrow {{ margin-bottom: 3px; }}
.export-wrap .price-breakdown {{ gap: 2px; margin-top: 3px; }}
.export-wrap .price-breakdown .row-diff {{ font-size: 13px; padding-bottom: 3px; }}
.export-wrap .price-breakdown .row-diff b {{ font-size: 14px; }}
.export-wrap .content.h3-text .teaser {{ margin-top: 2px; padding-top: 2px; }}
.export-wrap .micro-cta {{ font-size: 14.5px; margin-top: 26px; }}
/* URL a 17px desbordaba la caja del CTA (se cortaba el ".ar"): 16px + menos
   padding lateral entra justo en una linea. */
.export-wrap .cta-final {{ margin-top: 34px; padding-left: 10px; padding-right: 10px; }}
.export-wrap .cta-final .url {{ font-size: 15px; }}
.export-wrap .footer .swipe {{ font-size: 13px; }}
/* v8: los huecos internos entre badge y contenido (H1 y H6) venian del mockup chico.
   H1: fuera el padding-top 22%; H6: el contenido se estira (titulo 28, mas aire
   ENTRE bloques) para consumir el blanco libre en vez de dejarlo arriba. */
.export-wrap .story.b2 .content {{ padding-top: 0; }}
/* v12: historia 1 media un overflow microscopico (3px reales, sub-pixel) en el
   canvas 9:16 real -- de yapa, 1px menos arriba/abajo del band para dejar margen. */
.export-wrap .story.b2 .band {{ padding-top: 13px; padding-bottom: 13px; }}
/* A 28px "cada semana" rompe en dos lineas — 26 es el maximo que entra. El aire
   sobrante se reparte ENTRE bloques (margenes grandes), no arriba del contenido. */
.export-wrap .story.white h2.headline.display {{ font-size: 26px; }}
/* v12: historia 6 (cierre) media 29px de diseno de overflow -- los margenes
   grandes entre bloques (26/44/56, "aire para llenar pantalla" de la v8) se
   recortan lo justo para entrar en el canvas 9:16 real; el texto no se toco. */
.export-wrap .story.white .sub {{ margin-top: 16px; font-size: 16px; }}
.export-wrap .story.white .micro-cta {{ margin-top: 28px; }}
.export-wrap .story.white .cta-final {{ margin-top: 36px; }}
</style>
</head>
<body>
<div class="export-wrap">
{story_html}
</div>
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    html = PLANTILLA.read_text(encoding="utf-8")

    style_block = html.split("<style>", 1)[1].split("</style>", 1)[0]

    for nombre, placeholder in FUENTES:
        b64 = (FUENTES_DIR / f"{nombre}.b64").read_text(encoding="ascii").strip()
        style_block = style_block.replace(placeholder, b64)

    stories = extraer_story_divs(html)
    if len(stories) != len(HISTORIAS):
        raise SystemExit(f"Se esperaban {len(HISTORIAS)} historias, se encontraron {len(stories)}")

    for (idx, slug), story_html in zip(HISTORIAS, stories):
        for gif_name, placeholder in GIFS:
            if placeholder in story_html:
                gif_bytes = (FRAMES_DIR / gif_name).read_bytes()
                b64 = base64.b64encode(gif_bytes).decode("ascii")
                story_html = story_html.replace(placeholder, b64)

        html = EXPORT_TEMPLATE.format(style_block=style_block, story_html=story_html)
        out_path = OUT_DIR / f"v12-historia-{slug}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"OK -> {out_path.name} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
