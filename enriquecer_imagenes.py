"""
enriquecer_imagenes.py — Enriquecimiento de imagenes en catalogo_unificado.json

Estrategias (en orden):
  1. Yaguar SKU -> URL construida: yaguar.com.ar/wp-content/uploads/yaguar-skus/{SKU}.png
     Los 404 son manejados por el fallback del frontend (onError handler).
  2. Open Food Facts -> OFF URL para productos con EAN pero sin imagen actual
     (en el pipeline actual el OFF va como fallback en frontend, esto lo precarga en catalogo)
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOGO_PATH = os.path.join(BASE_DIR, "BRUJULA-DE-PRECIOS", "data", "processed", "catalogo_unificado.json")
YAGUAR_IMG_BASE = "https://yaguar.com.ar/wp-content/uploads/yaguar-skus"

PLACEHOLDERS = {"0000-", "base.png", "noimage", "placeholder", "no-image", "sin-imagen", "default"}


def es_placeholder(url: str) -> bool:
    if not url:
        return True
    url_lower = url.lower()
    return any(p in url_lower for p in PLACEHOLDERS)


def main():
    print("=" * 60)
    print("ENRIQUECIMIENTO DE IMAGENES - Brujula de Precios")
    print("=" * 60)

    with open(CATALOGO_PATH, encoding="utf-8") as f:
        data = json.load(f)

    productos = data if isinstance(data, list) else data.get("productos", [])
    print(f"Catalogo: {len(productos)} productos")

    yaguar_enriquecidos = 0
    off_enriquecidos = 0
    sin_imagen_antes = 0
    sin_imagen_despues = 0

    for p in productos:
        img_principal = p.get("imagen", "")
        fuentes = p.get("fuentes", {})
        imgs_fuentes = [fuentes.get(k, {}).get("imagen", "") for k in ["maxicarrefour", "maxiconsumo", "yaguar"]]
        tiene_imagen = not es_placeholder(img_principal) or any(not es_placeholder(i) for i in imgs_fuentes)

        if not tiene_imagen:
            sin_imagen_antes += 1

        # Estrategia 1: construir URL desde SKU de Yaguar
        fuente_yag = fuentes.get("yaguar", {})
        sku_yag = fuente_yag.get("sku", "")
        img_yag_actual = fuente_yag.get("imagen", "")

        if sku_yag and es_placeholder(img_yag_actual):
            url_construida = f"{YAGUAR_IMG_BASE}/{sku_yag}.png"
            fuentes.setdefault("yaguar", {})["imagen"] = url_construida
            if es_placeholder(img_principal):
                p["imagen"] = url_construida
            yaguar_enriquecidos += 1

        # Estrategia 2: OFF para productos con EAN y sin imagen (prioridad baja)
        ean = p.get("ean", "")
        img_actualizada = p.get("imagen", "")
        if ean and len(ean) >= 8 and es_placeholder(img_actualizada):
            off_url = f"https://images.openfoodfacts.org/images/products/{ean}/front_es.full.jpg"
            p["imagen"] = off_url
            off_enriquecidos += 1

    # Reconteo post-enriquecimiento
    for p in productos:
        img_principal = p.get("imagen", "")
        fuentes = p.get("fuentes", {})
        imgs_fuentes = [fuentes.get(k, {}).get("imagen", "") for k in ["maxicarrefour", "maxiconsumo", "yaguar"]]
        tiene_imagen = not es_placeholder(img_principal) or any(not es_placeholder(i) for i in imgs_fuentes)
        if not tiene_imagen:
            sin_imagen_despues += 1

    print(f"Yaguar SKU construido: {yaguar_enriquecidos} productos")
    print(f"Open Food Facts: {off_enriquecidos} productos")
    print(f"Sin imagen antes: {sin_imagen_antes}")
    print(f"Sin imagen despues: {sin_imagen_despues}")
    print(f"Recuperados: {sin_imagen_antes - sin_imagen_despues}")

    with open(CATALOGO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"\nGuardado: {CATALOGO_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
