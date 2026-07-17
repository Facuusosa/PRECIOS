---
name: project_fragmentacion_catalogo
description: Deteccion de productos partidos en 2 entradas (yaguar/maxiconsumo vs maxicarrefour/cadenas) que el pipeline fuzzy/TF-IDF no atrapa -- metodo, resultado y limitaciones (16/07/2026)
metadata:
  type: project
---

Tarea 16/07/2026: encontrar candidatos de fusion que `matches_pendientes.json` /
`mapeos_sospechosos.json` NO cubren -- casos por debajo del umbral fuzzy 0.75 o con
diferencias de tipeo/formato mas grandes (caso semilla: "Vodka ABSOLUT Raspberry"
(maxicarrefour+coto, EAN 7312040350056) vs "VODKA ABSOLUT RASPBERRI" (maxiconsumo,
EAN 7312040040759) -- mismo vodka, dos EAN distintos, nunca se fusiono).

## Metodo que funciono
Script en `scratchpad` (no versionado, ver detalle abajo) que:
1. Separa Grupo A (precio SOLO yaguar/maxiconsumo) vs Grupo B (precio SOLO
   maxicarrefour/coto/carrefour/dia), filtrado a ABC A/B **O precio > percentil 70
   de su sector** (el ABC puro pierde justo los casos de mas impacto: un producto
   fragmentado en 2 mitades diluye su volumen y cada mitad queda con ABC bajo -- caso
   medido: Absolut Raspberri via MaxiCarrefour+Coto, precio ~$27k pero ABC='D').
2. Compara por token de marca (no el primero de la frase -- el ORDEN cambia entre
   fuentes: MaxiConsumo dice "ABSOLUT RASPBERRI", MaxiCarrefour dice "Raspberri
   Absolut") + cantidad canonica (tolerancia 12%, reusa `_cantidad_canonica` de
   `actualizar_catalogo.py`) + similitud de caracteres (`SequenceMatcher` sobre
   `clave_nombre`).
3. Clave del fix de precision: un token de marca solo cuenta si es INFRECUENTE en
   su sector (document frequency <= max(4, 0.8% del sector)). Sin este filtro, un
   68% de los "alta confianza" eran falsos positivos por palabras genericas
   compartidas (product-type: "crema", "acondicionador", "limpiador"; varietal de
   vino: "cabernet", "chardonnay", "reserve"; sabor/corte: "naranja", "mitades",
   "bondiola"). [[feedback_patrones_error]]

## Resultado final (16/07/2026)
`data/quality/fragmentacion_ampliada.json` (NO trackeado en git -- `data/quality/*.json`
esta en `.gitignore`, igual que matches_pendientes.json): 1254 candidatos, 359 de
confianza "alta". Grupo A evaluado: 4642 productos. Grupo B: 1967. 1.4M comparaciones.

## Limitaciones conocidas -- avisar siempre al revisar esta lista
Dos patrones de falso positivo que sobrevivieron pese a los filtros:
1. **Mismo fabricante, variante distinta**: si la cadena solo tiene UNA variante en
   catalogo, un vino/licor del mismo productor pero varietal/etiqueta distinta puede
   matchear (ej. "Estancia Mendoza Cabernet Malbec" <-> "Estancia Mendoza Espumante";
   "Johnnie Walker Rojo" <-> "Hiram Walker" via apellido "walker" compartido).
   Se agrego un descalificador para colores/etiquetas mutuamente excluyentes
   (Rojo/Negro, Red/Black, etc.) pero no cubre todos los casos.
2. **Vinos/licores en general son el sector mas ruidoso** (mucha jerga de varietal/
   estilo que se parece a nombre propio). Almacen/Limpieza/Cuidado Personal salieron
   mas limpios en el muestreo manual (~85-90% de aciertos en "alta" tras el fix).

**Como aplicar:** siempre leer los DOS nombres completos antes de aceptar una
fusion -- el campo `razon` explica que token disparo el match pero no reemplaza el
juicio humano, sobre todo en Bebidas.
