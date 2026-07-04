# Verificacion precios Maxiconsumo — 2026-05-28

## Resumen
- Productos verificados en la web: 5 (top 5 con mayor ahorro aparente vs otros mayoristas)
- Coincidencias exactas (diff <5%): 2 (Milka Almendras, Sprite 2.25L — precio meta tag == catalogo)
- Diferencias detectadas: 3
  - Snacko 500g: precio unitario/bulto mal capturado
  - Tequila Jose Cuervo 750ml: precio MC correcto ($5.900) pero Yaguar tiene $45.475 (error de matching)
  - Caramelos Flynnies / Hilo Dental: sin precio visible en web (DISPONIBILIDAD CRITICA)
- Conclusion: HAY DOS PROBLEMAS DISTINTOS — ver seccion Analisis

---

## Detalle por producto

### 1. Papas Fritas SNACKO Clasica 500g
- EAN: 7798149380581
- Precio en catalogo: $203,16
- Precio bulto web (precio unitario por bulto cerrado): $4.199,90
- Precio unitario web (precio por unidad en bulto): $203,16
- meta[property="product:price:amount"]: $203,16 — ESTE ES EL CAMPO QUE LEE EL SCRAPER
- Diferencia: 1.968% — DIFERENCIA CRITICA
- Causa: el campo `meta[property="product:price:amount"]` devuelve el precio POR UNIDAD individual
  dentro del bulto, no el precio del bulto completo. El bulto tiene ~20 unidades.
  El enriquecedor (`enriquecer_precios.py` linea 93-98) lee exactamente ese campo.
- URL verificada: https://maxiconsumo.com/sucursal_burzaco/almacen/papas-fritas-snacko-clasica-500-gr-20993.html
- Estado: DISPONIBILIDAD CRITICA (sin stock)
- Screenshot: screenshots/maxiconsumo_snacko_precio.png

### 2. Caramelos Flynnies Surtidos 600g
- EAN: 7790384117106
- Precio en catalogo: $338,68
- Precio bulto web: sin precio visible (DISPONIBILIDAD CRITICA)
- Precio meta tag: no recuperable (producto sin precio expuesto en HTML)
- Diferencia: no verificable
- Nota: precio de Yaguar ($7.995) vs MC ($338,68) -> mismo patron que Snacko: precio por unidad vs bulto
- URL verificada: https://maxiconsumo.com/sucursal_burzaco/almacen/caramelos-flynnies-surtidos-600-gr-12234.html
- Estado: DISPONIBILIDAD CRITICA (sin stock, sin precio visible)
- Screenshot: no tomado (pagina sin contenido util)

### 3. Caramelos Flynnies Yoghurt 600g
- EAN: 7790380029946
- Precio en catalogo: $338,68
- Precio bulto web: sin precio visible (DISPONIBILIDAD CRITICA)
- Diferencia: no verificable — mismo patron que producto 2
- URL verificada: https://maxiconsumo.com/sucursal_burzaco/almacen/caramelos-flynnies-yoghurt-600-gr-11725.html
- Estado: DISPONIBILIDAD CRITICA

### 4. Hilo Dental Colgate 2x1 x50m
- EAN: 7891024183120
- Precio en catalogo: $259,90
- Precio Carrefour: $3.359,25 (90%+ mas caro -> mismo patron sospechoso)
- Precio bulto web: sin precio visible (DISPONIBILIDAD CRITICA)
- URL verificada: https://maxiconsumo.com/sucursal_burzaco/perfumeria/hilo-dental-colgate-2x1-x50-ml-17800.html
- Estado: DISPONIBILIDAD CRITICA

### 5. Tequila Jose Cuervo Reposado 750ml
- EAN: 7501035010109
- Precio en catalogo (MC): $5.899,90
- Precio meta tag web: $5.899,90 — COINCIDENCIA EXACTA (diff 0%)
- Precio en Yaguar segun catalogo: $45.475 — ERROR DE MATCHING en Yaguar
- Package: 1 (bulto de 1 unidad) -> precio meta tag correcto
- Diferencia MC vs web: 0% — OK
- URL verificada: https://maxiconsumo.com/sucursal_burzaco/bebidas/tequila-jose-cuervo-reposado-750-cc-23682.html
- Estado: DISPONIBILIDAD CRITICA
- Screenshot: screenshots/maxiconsumo_tequila.png

---

## Productos adicionales verificados (fuera del top 5 sospechosos)

### Gaseosa Sprite 2,25 Lt (EAN: 7790895001000)
- Precio en catalogo: $4.599,90
- Precio meta tag web: $4.599,90 — COINCIDENCIA EXACTA
- Package: 1 — precio correcto
- Screenshot: screenshots/maxiconsumo_sprite.png

### Chocolate Milka Almendras 55g (EAN: primer resultado con 3 mayoristas alineados)
- Precio en catalogo (MC): $4.199,90
- Precio meta tag web: $4.199,90 — COINCIDENCIA EXACTA
- Package: 1 — precio correcto
- Screenshot: screenshots/maxiconsumo_milka.png

---

## Analisis del problema

### Problema 1 — BUG CONFIRMADO: precio por unidad vs precio de bulto (enriquecer_precios.py)

El scraper de Maxiconsumo usa `enriquecer_precios.py` que lee el campo:
```html
<meta property="product:price:amount" content="203.159001"/>
```

Para productos de bulto multi-unidad, este campo devuelve el PRECIO POR UNIDAD individual,
no el precio del bulto completo. El precio correcto del bulto esta en el DOM como:
```html
<span data-label="con iva" data-price-amount="$ 4.199,90" class="price-wrapper">
  <span class="price">$ 4.199,90</span>
</span>
```
junto al label "Precio unitario por bulto cerrado".

**Escala del problema (analisis del catalogo):**
- Total productos con precio MC: 9.360
- Con comparativa contra otro mayorista: 2.084
- Sospechosos (MC >50% mas barato que otros): 41 productos
- OK (diferencia razonable <50%): 2.043 productos
- Impacto estimado: ~2% de productos con comparativa tienen precio unitario mal capturado

**Distincion importante:**
- Cuando `package = 1` (bulto de 1 unidad): el meta tag es correcto. La mayoria de productos.
- Cuando `package > 1` (bultos multi-unidad como caja de papas fritas x20): el meta tag da el precio
  por unidad individual, lo que genera valores 10x-30x mas bajos que el precio real del bulto.

**Fix necesario en `enriquecer_precios.py`:**
En lugar de leer solo `meta[property="product:price:amount"]`, leer el selector:
```python
# Selector DOM: precio del bulto cerrado
soup.find("span", {"data-label": "con iva", "class": "price-wrapper"})
# O buscar el precio asociado al label "Precio unitario por bulto cerrado"
```

### Problema 2 — ERROR DE MATCHING en Yaguar (no es problema de Maxiconsumo)

El Tequila Jose Cuervo 750ml tiene en Yaguar un precio de $45.475 vs $5.900 en MC.
El precio de MC ($5.900) esta correcto segun la web. El error es que Yaguar empareja
esta botella de 750ml con un pack de varias botellas o una presentacion diferente.
Esto genera falsos positivos en las comparativas de la app.

---

## Estado del scraper

El scraper de Maxiconsumo que se lanzo hoy (2026-05-28) sigue corriendo en background.
El archivo mas reciente disponible es del 2026-05-27 con 9.775 productos.

---

## Proximos pasos recomendados

1. **[CRITICO] Fix en `enriquecer_precios.py`**: leer precio del DOM ("Precio unitario por bulto cerrado")
   en lugar de `meta[property="product:price:amount"]` para productos con `package > 1`.
   Alternativa mas simple: agregar logica de deteccion — si el meta price es < 300 y existe un
   data-price-amount >> en el DOM, usar ese ultimo.

2. **[MEDIO] Filtrar matching Yaguar**: revisar productos donde la diferencia supera el 300%
   — probablemente son falsos matches de distintas presentaciones.

3. **[BAJO] Limpiar productos con "DISPONIBILIDAD CRITICA"**: estos productos tienen precio
   en cache pero no tienen stock, lo que genera comparativas incorrectas para el usuario.
   Considerar etiquetarlos o excluirlos del ranking de bombas.
