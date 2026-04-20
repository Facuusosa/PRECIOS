# Skill: Verificar Precios en Vivo (Puppeteer MCP)

Verifica precios reales en los 3 mayoristas comparándolos contra el catálogo. Usa Puppeteer MCP para navegación real con login.

## Cuándo usar
- Después de actualizar el catálogo y hay dudas sobre precios
- Cuando `auditoria_matches.json` tiene productos con ratio alto
- Cuando el usuario reporta un precio incorrecto en el frontend
- Verificación periódica de muestra del catálogo

## Credenciales (leer desde .env con Bash antes de empezar)
```bash
python -c "
from dotenv import load_dotenv; import os; load_dotenv()
print('YAGUAR_USER:', os.getenv('YAGUAR_USERNAME'))
print('CARREFOUR_CUIT:', os.getenv('CARREFOUR_CUIT'))
print('MCO_EMAIL:', os.getenv('MAXICONSUMO_EMAIL'))
"
```

## Paso 1 — Identificar producto a verificar

Si el usuario no especificó un producto, leer el catálogo y elegir 1-3 productos con 2+ fuentes:
```bash
python -c "
import json
with open('BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json') as f:
    cat = json.load(f)
multi = [p for p in cat if sum(1 for v in p['precios'].values() if v > 0) >= 2][:5]
for p in multi:
    pr = {k: v for k, v in p['precios'].items() if v > 0}
    print(f'{p[\"nombre_display\"]} | {pr}')
"
```

Anotar: nombre del producto, precios en catálogo por fuente.

## Paso 2 — Verificar en Yaguar

### Login (selectores verificados 18/04/2026)
1. `puppeteer_navigate` → `https://yaguar.com.ar/login/`
   - Nota: puede aparecer popup "Tienda Nueva" → cerrarlo con `button[class*="close"]`
2. `puppeteer_fill` → `#username` → valor: `Martin`
3. `puppeteer_fill` → `#password` → valor: `Martin2025`
4. `puppeteer_click` → `button[type="submit"]`
5. Confirmar login: busca "Hola, Martin" en el navbar

### Buscar producto — VÍA API (más confiable que el buscador SPA)
La tienda nueva de Yaguar es una SPA que NO responde a `puppeteer_fill` + eventos DOM.
El buscador solo funciona con clicks físicos. Usar la API directamente:

```javascript
// En puppeteer_evaluate — busca el producto y retorna precios
(async () => {
  const r = await fetch('/wp-json/wc/store/v1/products?search=NOMBRE_PRODUCTO&per_page=10', {credentials: 'include'});
  const data = await r.json();
  return data.map(p => ({name: p.name, price: p.prices?.price, sku: p.sku}));
})()
```

- Precio viene en centavos dividido 100 si es WooCommerce estándar, o en pesos directos
- Verificar: si `price` es `"2466"` → es $2.466

### Si el login falla
- Yaguar renovó la tienda — puede haber popup "Tienda Nueva" que bloquea el form
- Cerrar popup con: `document.querySelector('button.modal-close')?.click()`
- Los campos son `#username` y `#password` (WordPress estándar)

## Paso 3 — Verificar en MaxiCarrefour

### Login (flujo verificado 18/04/2026)
El login funciona pero la sesión se pierde si se navega a una URL inexistente.
El modal usa un framework propio — el card COMERCIO tiene clase CSS `.btn__menu_item__left`.

1. `puppeteer_navigate` → `https://comerciante.carrefour.com.ar/`
2. Cerrar popup de bienvenida si aparece: `document.querySelectorAll('button.close')[0]?.click()`
3. Hacer click en "Ingresar": `[...document.querySelectorAll('a, span, div')].find(e => e.textContent.trim() === 'Ingresar')?.click()`
4. Modal muestra "COMERCIO o EMPRENDIMIENTO" y "HOGAR" — clickear por clase CSS: `document.querySelector('.btn__menu_item__left')?.click()`
   - Console log debe decir `login_maxi` si el click funcionó
5. Formulario aparece — llenar con IDs exactos:
   - Seleccionar Provincia: `document.querySelectorAll('select')[0].value = 'CABA'; document.querySelectorAll('select')[0].dispatchEvent(new Event('change', {bubbles:true}))`
   - Esperar 1.5s y seleccionar sucursal value `'20'` (CARREFOUR MAXI AVELLANEDA - Hipolito Yrigoyen)
   - `puppeteer_fill` → `#user-name` → `Martin Lopez` (mínimo 8 chars)
   - `puppeteer_fill` → `#user-cuit` → `4116846`
   - `puppeteer_fill` → `#user-phone` → `01122763748`
   - `puppeteer_fill` → `#user-email` → `martin@comercio.com.ar`
6. Click Ingresar: `[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Ingresar')?.click()`
7. Confirmar: debe decir "Pedido entregado por CARREFOUR MAXI AVELLANEDA" en el header

### Buscar producto
8. `puppeteer_fill` → `#q__search` → nombre del producto
9. Disparar búsqueda con keypress + keyup (ambos necesarios — keydown solo no alcanza):
   ```javascript
   const el = document.querySelector('#q__search');
   el?.dispatchEvent(new KeyboardEvent('keypress', {key:'Enter', keyCode:13, which:13, bubbles:true}));
   el?.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter', keyCode:13, which:13, bubbles:true}));
   ```
   - El contexto de ejecución se destruye (navegación ocurrió) — eso es correcto, esperar screenshot
10. `puppeteer_evaluate` para extraer precio:
```javascript
[...document.querySelectorAll('[data-price]')].map(e => ({
  nombre: e.closest('[class*="product"]')?.querySelector('[class*="name"], [class*="title"]')?.textContent?.trim(),
  precio: e.getAttribute('data-price')
})).filter(p => p.precio !== 'private').slice(0, 5)
```

### Señal crítica: cookies expiradas
Si `data-price="private"` → renovar `CARREFOUR_PHPSESSID` y `CARREFOUR_CF_CLEARANCE` en `.env`

## Paso 4 — Verificar en Maxiconsumo

> **NOTA:** Puppeteer no puede acceder a Maxiconsumo (Cloudflare bloquea headless vía TLS fingerprint).
> Se usa `curl_cffi` con impersonation Safari 15.3 — mismo método que el scraper real → precio 100% en vivo.

### Buscar precio en vivo
```bash
python targets/maxiconsumo/verificar_precio.py "NOMBRE DEL PRODUCTO"
```
- Devuelve los 5 resultados más relevantes con precios en vivo desde maxiconsumo.com
- Buscar el resultado cuyo nombre coincida mejor con el producto del catálogo
- Si no aparece el producto exacto, buscar con términos más cortos (ej: "sprite" en lugar de "sprite 2.25 l")

### Ejemplo real verificado (18/04/2026)
- Catálogo: Sprite 2.25L → Maxiconsumo $4.403,65
- Script en vivo: GASEOSA SPRITE 2,25 LT → **$4.399,90**
- Diferencia: $3,75 (0.08%) ✅ CORRECTO

## Paso 5 — Comparar y reportar

Formatear el resultado así:
```
VERIFICACIÓN BROWSER — [fecha y hora]
Producto: [nombre_display del catálogo]

Catálogo:
  Yaguar:        $[precio_catalogo]
  MaxiCarrefour: $[precio_catalogo]
  Maxiconsumo:   $[precio_catalogo]

Web real:
  Yaguar:        $[precio_scraped] [✅ OK / ⚠️ DIFF X% / ❌ NO ENCONTRADO]
  MaxiCarrefour: $[precio_scraped] [✅ OK / ⚠️ DIFF X% / ❌ COOKIES EXPIRADAS]
  Maxiconsumo:   $[precio_scraped] [✅ OK / ⚠️ DIFF X% / ❌ NO ENCONTRADO]

Estado general: ✅ DATOS FRESCOS / ⚠️ DESACTUALIZADO (correr scraper) / ❌ COOKIES CARREFOUR EXPIRADAS
```

Umbral de discrepancia: **>5%** = ⚠️ DIFF | **>20%** = ❌ ERROR GRAVE

## Si los selectores no funcionan

1. Tomar screenshot en cada paso fallido
2. Usar `puppeteer_evaluate` para inspeccionar el DOM:
```javascript
// Listar todos los elementos con "price" en la clase
[...document.querySelectorAll('[class*="price"]')].map(e => ({class: e.className, text: e.textContent.trim()})).slice(0,10)
```
3. Ajustar el selector según el resultado
4. Documentar el selector correcto al final del reporte para usarlo la próxima vez
