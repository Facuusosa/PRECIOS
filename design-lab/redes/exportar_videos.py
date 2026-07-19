"""
Historias 2, 4 y 5 llevan un GIF animado embebido (recorrido real de la app, 3 estados
con pausas distintas). El PNG estatico solo capturaba el primer frame y perdia el
movimiento. Este script arma un MP4 por historia: renderiza cada frame del GIF fuente
como una historia completa (1080x1920, con el header/texto fijo alrededor) via Chrome
headless, y los combina respetando la duracion real de cada frame del GIF original.
"""
import base64
import io
import shutil
import subprocess
import tempfile
from pathlib import Path

from imageio_ffmpeg import get_ffmpeg_exe
from PIL import Image

from exportar_historias import (
    BASE_DIR, PLANTILLA, FUENTES_DIR, FRAMES_DIR, OUT_DIR,
    FUENTES, HISTORIAS, EXPORT_TEMPLATE, extraer_story_divs,
)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FFMPEG = get_ffmpeg_exe()
# Chrome headless (--screenshot) devuelve "Acceso denegado" al escribir dentro de
# OneDrive\Escritorio de forma intermitente (no es Controlled Folder Access, esta
# desactivado -- probablemente un AV heuristico marcando escrituras masivas de un
# headless browser). El workaround real: renderizar TODO a un temp fuera de OneDrive
# y copiar solo el MP4 final con shutil (una copia de archivo normal si funciona).
TMP_ROOT = Path(tempfile.gettempdir()) / "brujula_redes_export"
TMP_DIR = TMP_ROOT / "_tmp_frames"

# La captura completa de la app mide ~2.2 pantallas de historia: no existe frame
# estatico donde entre entera y legible (feedback Facu 19/07). En los frames largos
# del GIF, el video recorre la captura de arriba a abajo via object-position y
# termina quieto en el fondo (la zona de precios/datos).
PAN_MIN_MS = 3000   # solo los frames de 3s o mas recorren; los cortos quedan fijos
PAN_STEPS = 24
PAN_HOLD = 0.12     # fraccion del tiempo quieto al inicio y al final del recorrido

VIDEOS = [
    (2, "historia2.gif", "__RECORRIDO_GIF__"),
    (4, "historia4.gif", "__H4GIF__"),
    (5, "historia5.gif", "__H5GIF__"),
]


def screenshot(html_path: Path, png_path: Path) -> None:
    url = "file:///" + str(html_path.resolve()).replace("\\", "/").replace(" ", "%20")
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         f"--screenshot={png_path.resolve()}",
         "--window-size=1080,1920", "--hide-scrollbars", url],
        capture_output=True, timeout=30,
    )


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    html = PLANTILLA.read_text(encoding="utf-8")
    style_block = html.split("<style>", 1)[1].split("</style>", 1)[0]
    for nombre, placeholder in FUENTES:
        b64 = (FUENTES_DIR / f"{nombre}.b64").read_text(encoding="ascii").strip()
        style_block = style_block.replace(placeholder, b64)

    stories = extraer_story_divs(html)
    story_por_idx = {idx: story_html for (idx, _slug), story_html in zip(HISTORIAS, stories)}

    for idx, gif_name, placeholder in VIDEOS:
        gif = Image.open(FRAMES_DIR / gif_name)
        n_frames = gif.n_frames
        story_html = story_por_idx[idx]

        renders = []  # (png_path, dur_ms) en orden de reproduccion
        for i in range(n_frames):
            gif.seek(i)
            frame = gif.convert("RGBA")
            buf = io.BytesIO()
            frame.save(buf, format="PNG")
            frame_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            dur_ms = gif.info.get("duration", 100)

            frame_html = story_html.replace(placeholder, frame_b64)
            base_html = EXPORT_TEMPLATE.format(style_block=style_block, story_html=frame_html)

            if dur_ms >= PAN_MIN_MS:
                for s in range(PAN_STEPS):
                    t = s / (PAN_STEPS - 1)
                    u = min(1.0, max(0.0, (t - PAN_HOLD) / (1 - 2 * PAN_HOLD)))
                    pct = round(u * 100, 1)
                    sub_html = base_html.replace(
                        "</style>",
                        f".export-wrap .shot-frame img {{ object-position: 50% {pct}% !important; }}\n</style>",
                        1,
                    )
                    html_path = TMP_DIR / f"h{idx}-f{i}s{s:02d}.html"
                    html_path.write_text(sub_html, encoding="utf-8")
                    png_path = TMP_DIR / f"h{idx}-f{i}s{s:02d}.png"
                    screenshot(html_path, png_path)
                    renders.append((png_path, dur_ms / PAN_STEPS))
                print(f"  historia {idx} frame {i+1}/{n_frames}: recorrido de {PAN_STEPS} pasos ({dur_ms}ms)")
            else:
                html_path = TMP_DIR / f"h{idx}-f{i}.html"
                html_path.write_text(base_html, encoding="utf-8")
                png_path = TMP_DIR / f"h{idx}-f{i}.png"
                screenshot(html_path, png_path)
                renders.append((png_path, dur_ms))
                print(f"  historia {idx} frame {i+1}/{n_frames} estatico ({dur_ms}ms)")

        # Secuencia numerada exacta (fps fijo, sin ambiguedad de "duration" del demuxer
        # concat, que redondeaba mal la duracion real - ver feedback de Facu 17/07).
        # Ticks por acumulado (no por frame): con sub-frames de ~200ms el redondeo
        # individual acumulaba hasta +9% de duracion total.
        fps = 30
        seq_dir = TMP_DIR / f"h{idx}-seq"
        seq_dir.mkdir(exist_ok=True)
        n = 0
        t_acum = 0.0
        for png_path, dur_ms in renders:
            t_acum += dur_ms
            objetivo = max(n + 1, round(fps * t_acum / 1000))
            while n < objetivo:
                dest = seq_dir / f"frame_{n:05d}.png"
                if dest.exists():
                    dest.unlink()
                dest.hardlink_to(png_path)
                n += 1

        slug = dict(HISTORIAS)[idx]
        tmp_out = TMP_ROOT / f"v12-historia-{slug}.mp4"
        result = subprocess.run(
            [FFMPEG, "-y", "-framerate", str(fps), "-i", str(seq_dir / "frame_%05d.png"),
             "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "28",
             "-preset", "medium", "-movflags", "+faststart", str(tmp_out)],
            capture_output=True,
        )
        if result.returncode != 0:
            raise SystemExit(result.stderr.decode("utf-8", errors="replace"))
        real_dur = n / fps
        out_path = OUT_DIR / f"v12-historia-{slug}.mp4"
        shutil.copy2(tmp_out, out_path)
        print(f"OK -> {out_path.name} ({real_dur:.2f}s exactos, {out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
