---
name: feedback_patrones_error
description: Dos patrones criticos de error en el pipeline de precios — Yaguar precio-caja y Maxiconsumo precio-parcial
metadata:
  type: feedback
---

## Patron A: Yaguar precio de CAJA/DISPLAY

Productos afectados: PANTENE sachet 10ml, DOVE sachet, TURRON MISKY, ALFAJOR FULBITO.
Sintoma: precio Yaguar 500-1300x mayor que Carrefour/Maxiconsumo con EAN exacto.
Ejemplos: PANTENE sachet ($190.000 en Yaguar vs $165 en Maxiconsumo), TURRON MISKY ($191.000 vs $148).
Causa probable: Yaguar vende por display completo (24-50 unidades), no por unidad individual.

**Why:** Detectado en auditoria_matches.json el 27/05. Confianza "exacto_ean" confirma que el EAN matchea -- el problema es el precio, no el match.
**How to apply:** Antes de procesar precios de Yaguar para productos sachet/unitarios, verificar si el campo de descripcion menciona cantidad de unidades por caja. Fix en scraper_pro.py de Yaguar.

## Patron B: Maxiconsumo precio parcial

Productos afectados: 24 en auditoria_matches al 28/05. Ejemplos: Coca Cola 600ml a $41 (deberia ser ~$1700), Manaos 2.25L a $31, Salsa CICA a $31.
Sintoma: precio Maxiconsumo < $100 cuando los otros mayoristas muestran $1.000-$2.000.
Causa probable: el scraper raspo el precio sin IVA, precio de descuento especial, o solo los primeros digitos del precio del DOM.

**Why:** Detectado en auditoria_matches.json el 27/05. Patron consistente en bebidas y salsas.
**How to apply:** Al ver precio Maxiconsumo < $100 para producto de consumo masivo -- sospechar error de scraper, no precio real. Fix en selector de precio del scraper_pro.py de Maxiconsumo.

## Patron D: Fragmentacion cruzada yaguar/maxiconsumo <-> maxicarrefour/cadenas (16/07)

El mismo producto fisico aparece como 2 entradas de catalogo con EAN distinto: una
con precio SOLO yaguar/maxiconsumo (sin EAN nativo, matchean por fuzzy), otra con
precio SOLO maxicarrefour/coto/carrefour/dia (100% EAN). Causa: diferencias de
tipeo ("Raspberry" vs "Raspberri") u orden de palabras ("ABSOLUT RASPBERRI" vs
"Raspberri Absolut") que quedan por debajo del umbral fuzzy 0.75 del pipeline
(`_TH6` en `actualizar_catalogo.py`) y de la calibracion TF-IDF (regla 09).

**Why:** Caso semilla Vodka Absolut Raspberri (ver [[project_fragmentacion_catalogo]]
para el detalle completo del metodo de deteccion y sus limitaciones).
**How to apply:** Al auditar, revisar `data/quality/fragmentacion_ampliada.json` si
existe (no siempre esta actualizado -- es un analisis puntual, no parte del pipeline
regular). Si el usuario reporta "esta fuente no tiene el producto pero deberia" y el
producto SI aparece del otro lado (yaguar/maxiconsumo vs cadena) con nombre parecido
pero no identico, sospechar este patron antes que un bug de scraping.

## Patron C: Maxiconsumo precio de pack/caja (nuevo, 28/05)

Productos afectados: 40 en catalogo activo. Top casos: TULIPAN Dispenser 12x3u MC=$21.500 vs Y=$2.012 (10.7x), ALFAJOR GUAYMALLEN 24un MC=$13.500 vs Y=$597.
Sintoma: precio Maxiconsumo es razonable en si mismo, pero corresponde a pack de N unidades mientras Yaguar es por unidad.
Causa probable: el nombre en Maxiconsumo dice "24 UN" o "12X3" -- scraper raspa el precio total del pack.

**Why:** Detectado el 28/05. Diferente del patron B (precio parcial) -- aqui el precio de MC no es bajo, es el precio de un pack entero.
**How to apply:** Antes de comparar precios MC vs Yaguar, detectar si el nombre de MC contiene "X N UN" o "N UN" donde N > 1. Si hay pack, dividir el precio por N para normalizar. Fix en actualizar_catalogo.py.
