import re

PREFIJO_CORRECTO = (
    "Buenos días. Mi nombre es Facundo Sosa, trabajo como analista de precios y "
    "desarrollé una herramienta web, Brújula de Precios, que compara los precios de "
    "Yaguar, Maxiconsumo y MaxiCarrefour para ver en cuál conviene comprar cada producto "
    "antes de hacer el pedido.\\n\\nLa herramienta revisa automáticamente, todos los días, "
    "los precios de los tres mayoristas"
)

SUFIJO_CORRECTO = (
    ". Tiene más de 18.000 productos e incluye una calculadora que sugiere el precio de "
    "venta según el margen que desee y la opción de armar listas de compra, entre otras "
    "funciones.\\n\\nPor el momento está en fase de prueba, así que cualquier comentario "
    "suyo me sería de mucha utilidad. Le dejo el enlace por si desea probarla: "
    "https://v0-brujula-de-precios.vercel.app\\n\\nQuedo a disposición por cualquier consulta. "
    "Saludos cordiales, Facundo Sosa."
)

html_paths = [
    r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\data\outreach\panel_outreach.html",
    r"c:\Users\Facun\OneDrive\Escritorio\PROYECTOS PERSONALES\PRECIOS\BRUJULA-DE-PRECIOS\public\outreach.html",
]

for path in html_paths:
    with open(path, encoding="utf-8-sig") as f:
        content = f.read()

    # Reemplazar PREFIJO roto (buscar desde const PREFIJO = " hasta el cierre ")
    content = re.sub(
        r'(const PREFIJO = ")([^"]*?)(")',
        lambda m: m.group(1) + PREFIJO_CORRECTO + m.group(3),
        content
    )

    # Reemplazar SUFIJO roto
    content = re.sub(
        r'(const SUFIJO\s*= ")([^"]*?)(")',
        lambda m: m.group(1) + SUFIJO_CORRECTO + m.group(3),
        content
    )

    # Guardar sin BOM
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"OK: {path.split(chr(92))[-1]}")

print("Encoding corregido.")
