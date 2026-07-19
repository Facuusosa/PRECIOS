# Sistema de historias para redes (Instagram/TikTok)

Generador de piezas 9:16 (formato story) con la identidad real de Brújula — sin depender de Canva para iterar rápido. Se maqueta en HTML/CSS con la tipografía Poppins real incrustada, y las capturas de pantalla son de la app en producción (Puppeteer), no mockups dibujados.

## Identidad usada (sacada de `BRUJULA-DE-PRECIOS/app/globals.css`, no inventada)
- Fondo: `#ffffff`
- Negro (primario): `#1a1a1a`
- Dorado/cobre (acento): `#c89055`
- Tipografía: Poppins (pesos 400/600/700/800 en `fuentes/*.b64`)

## Cómo generar una pieza nueva
1. Copiar `plantilla-historia.html`, editar el contenido/copy de la historia dentro de `.story`.
2. Si la historia lleva una captura real de la app: tomarla con el MCP de Puppeteer (`puppeteer_navigate` a la URL real + `puppeteer_screenshot` con `encoded: true`), guardar el PNG.
3. Correr el build:
   ```
   python build.py mi-plantilla.html salida.html --screenshot "ruta\captura.png|__SCREENSHOT1__"
   ```
4. Publicar `salida.html` como Artifact para revisar, o subirlo directo a Canva/exportar como imagen para publicar.

## FORMATO DEFINITIVO de exportación (revisado 19/07/2026 — usar SIEMPRE este)
Toda la configuración vive en `EXPORT_TEMPLATE` dentro de `exportar_historias.py` (los
overrides `.export-wrap ...`). No tocarla sin releer esta sección. Resumen de qué es y por qué:

- **Lienzo final: 1080×1920 (9:16 REAL)**, no 1080×2340. El 19/07 se había elegido 2340
  para que calzara con el mockup `.phone` de la galería de revisión — pero el compositor
  de Historias de Instagram SIEMPRE usa 9:16 real. Al pegar un archivo 9:19.5 ahí, no lo
  puede llenar sin cortar contenido o dejar franjas de su propio fondo (negro) visibles
  a los costados — confirmado por Facu con captura real del compositor. **El juez final
  (la Historia publicada) manda por sobre el mockup de revisión.** Si en algún momento se
  vuelve a tocar el canvas, verificar primero contra este hecho, no contra el artifact.
- **Ancho de diseño 282px + `zoom: 3.8297872`** (= 1080/282, alto ahora **501.333px**, antes
  611px): 282 es el ancho INTERNO real del mockup (300 − 2×9 de bisel) y el zoom no cambia
  con la altura del canvas (convierte px de diseño a px reales 1:1 sin importar cuánto mida
  el alto). Exportar a otro ancho cambia tamaños relativos y cortes de línea vs. lo aprobado.
- **Paddings de historia: `padding-top: 36px / bottom: 50px`** (≈138/191px reales, sin
  cambios — al ser en px de diseño con el mismo zoom, ya representan el mismo margen real
  de siempre) — badge arriba y footer abajo bien pegados a los bordes. Si al publicar la UI
  de Instagram pisa el badge o el footer, volver a 52/68.
- **El contenido SÍ se recortó** al pasar de 2340→1920 (18% menos alto de diseño disponible):
  historia 3 (patrón) y 6 (cierre) tenían overflow real medido (77px y 29px de diseño) con
  los tamaños de la tanda 2340 — se ajustaron fuentes/márgenes hasta medir overflow negativo
  (margen de sobra) con `getBoundingClientRect` vía Puppeteer, no a ojo. Historia 1 tenía un
  overflow de 3px reales (ruido, no bug real). Ver el detalle de qué se tocó en los
  comentarios `/* v12 ... */` de `EXPORT_TEMPLATE`.
- **La captura de la app va ENMARCADA como tarjeta** (márgenes laterales de `.story`,
  border-radius y borde del CSS base). NO poner full-bleed: se probó (v7/v8) y a Facu le
  gustó menos — "la estética de tarjeta queda mejor".
- **Barra de progreso dibujada: oculta solo en export** (publicada, Instagram pone la suya).
- **Videos (historias con GIF): el frame de ≥3s hace "recorrido"** — la captura de la app
  mide ~2.2 pantallas, ningún frame fijo la muestra entera; `exportar_videos.py` la recorre
  de arriba a abajo (`PAN_STEPS=24`) y termina quieto en la zona de precios.
- **Prefijo de versión OBLIGATORIO en cada tanda con contenido distinto** (`v12-historia-…`,
  `v13-…`): regenerar con el mismo nombre ya causó un falso "sigue igual" (Facu subió el
  archivo viejo de la galería del celu).

```
python exportar_historias.py                     # genera output-historias/vN-historia-*.html
# por cada historia ESTATICA (sin GIF), Chrome headless -> PNG:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --no-sandbox \
  --screenshot="...\output-historias\vN-historia-X.png" --window-size=1080,1920 \
  --hide-scrollbars "file:///.../output-historias/vN-historia-X.html"

# historias con GIF embebido -> MP4 con recorrido (usa el mismo EXPORT_TEMPLATE):
python exportar_videos.py
```

**Bug de entorno (19/07/2026): Chrome headless puede tirar "Acceso denegado" escribiendo
directo dentro de `OneDrive\Escritorio\...` (no es Controlled Folder Access de Windows,
se confirmó desactivado — probablemente un AV heurístico marcando escrituras masivas de
un browser headless). No es intermitente: una vez que empieza a fallar en la sesión, falla
siempre para ese directorio. `exportar_videos.py` ya tiene el workaround aplicado (renderiza
frames y el MP4 a `%TEMP%\brujula_redes_export` y copia el archivo final con `shutil.copy2`,
que sí funciona). Si el Chrome CLI de las estáticas (comando de arriba) tira el mismo error,
apuntar `--screenshot=` a una carpeta temporal fuera de OneDrive y copiar el PNG final a mano.

**Checklist antes de entregar una tanda** (todo pasó de verdad al menos una vez):
1. Mirar el PNG/frame real completo de cada pieza (Chrome CLI, no Puppeteer — su captura
   glitchea con zoom no entero) — cortes de texto tipo URL del CTA solo se ven a ojo.
2. Medir overflow real con Puppeteer (`getBoundingClientRect` del último elemento visible
   vs. `.story`, y `scrollWidth` vs `clientWidth` en textos largos) — no asumir que entra
   solo porque entraba en el canvas anterior.
3. En videos: duración exacta en el log (`OK -> ... (X.XXs exactos)`) y mirar el ÚLTIMO
   frame del recorrido (debe verse la zona de precios completa).
4. Verificar los precios mostrados contra `catalogo_unificado.json` del día (nunca
   publicar datos de más de 1-2 días).
5. Borrar `.html` intermedios, `_tmp_frames/` y las tandas viejas — en `output-historias/`
   quedan SOLO los 6 archivos finales.
6. Regenerar el artifact de revisión con los archivos reales embebidos y republicar en la
   MISMA URL (script `armar_artifact.py` en el scratchpad de la sesión, o rehacerlo: página
   con los 6 como data URIs).

El juez final es la **historia PUBLICADA en Instagram** — no el compositor (su columna de
íconos tapa contenido), no el reproductor del celu (su barra tapa la fila de precios), y
tampoco el mockup `.phone` de la galería de revisión (9:19.5 — solo sirve para maquetar
copy/layout a mano alzada, no para juzgar el tamaño final).

## Tratamiento de color decidido (13/07/2026)
Dos variantes dentro de los mismos 3 colores de marca (no colores nuevos — la razón: si el post usa una paleta distinta a la app, se pierde la continuidad visual cuando el usuario entra a Brújula después de ver el post):
- **A — negro dominante**: fondo `#1a1a1a`, dorado como bloque sólido detrás de la palabra clave. Más "premium/serio".
- **B2 — dorado dominante con negro reforzado**: fondo `#c89055`, el título vive dentro de una franja negra de ancho completo (no solo la palabra clave), la marca vive en una pastilla negra arriba. Más "grita" en el scroll — poco común ver dorado sólido de fondo en Instagram, por eso frena el dedo.

Decisión: abrir la serie con B2 (frena el scroll) y alternar a A para el resto — la alternancia funciona como ritmo visual.

## Guion de la serie fundacional (6 historias — CERRADO 19/07/2026)
1. **Gancho** (B2, foto): "¿Sabés cuánto ahorrarías comprando en un mayorista en vez del
   súper?" + "te mostramos la diferencia real y el precio de cada página" (copy de Facu).
2. **Prueba real** (negro, VIDEO): "$2.828 de diferencia en el mismo producto" + recorrido
   real de la app hasta la comparación completa del Fernet.
3. **El patrón** (negro, foto): breakdown Yaguar/MCF/MCO vs. cadenas — "Los mayoristas
   compiten por el precio. Las cadenas, no."
4. **La canasta** (negro, VIDEO): lista real de 30 productos, $86.922, en Mi Lista.
5. **El remate** (negro, VIDEO): la misma canasta, dos formas de comprarla.
6. **Cierre** (blanco, foto): "Precios actualizados cada semana" + CTA
   brujuladeprecios.com.ar (espacio para el sticker de link).

## Motor semanal (capa 2 de la estrategia, pendiente de armar)
Idea: cuando corre el pipeline de datos semanal, generar automáticamente 1-2 piezas de contenido usando el dato más llamativo de esa corrida (ej. mayor variación de precio semana a semana) — mismo patrón de plantilla, texto generado a partir del catálogo real. No implementado todavía.
