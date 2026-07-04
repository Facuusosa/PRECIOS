# Skill: Buscar Comercios

Busca comercios potenciales (supermercados chinos, autoservicios, minimercados independientes) en una zona específica para outreach. Usar con `/buscar-comercios [zona]`.

## ICP (cliente ideal)
Comercios que hacen pedidos semanales/quincenales a mayoristas (Yaguar, Maxiconsumo, MaxiCarrefour).
Ejemplos: supermercados de barrio, autoservicios, súper chinos, minimercados independientes.
NO son ICP: kioscos puros, maxikioscos, cadenas (Carrefour, Dia, Coto), verdulerías, gasolineras.

## Input esperado
- Zona a buscar (ej: "Villa Pueyrredón", "Villa del Parque", "Agronomía")
- Si no se especifica zona → usar Villa Pueyrredón por defecto

## Pasos

1. **Leer base existente**
   - Buscar archivos JSON en `data/outreach/comercios_*.json` — leer el más reciente
   - Ver cuántos contactos ya hay y cuáles tienen estado "contactado"
   - Evitar duplicados en la nueva búsqueda

2. **Buscar en Google Maps** (via Puppeteer — navegar directamente)
   Correr las 3 queries en orden, esperar resultados antes de pasar a la siguiente:
   - `supermercado chino [zona] Buenos Aires` — ICP más puro (~90% útil)
   - `supermercados [zona] Buenos Aires` — cobertura amplia
   - `autoservicio [zona] Buenos Aires` — agrega locales únicos

   Por cada resultado en el panel lateral, extraer el texto básico (nombre, categoría, dirección).
   Luego, **para cada resultado que pase el filtro**, hacer clic en su card y extraer el perfil completo:

   ```javascript
   // En el perfil individual de Maps, extraer:
   const tel = document.querySelector('[data-tooltip="Copiar número de teléfono"], [aria-label*="eléfono"]')
     ?.closest('*')?.innerText?.match(/[\d\s\-\+\(\)]{7,}/)?.[0]?.trim() || '';
   const web = document.querySelector('a[data-tooltip="Abrir sitio web"], a[aria-label*="sitio"]')?.href || '';
   const foto = document.querySelector('button[jsaction*="pane.heroHeaderImage"] img, .RZ66Rb img')?.src || '';
   const rating = document.querySelector('.MW4etd')?.innerText?.trim() || '';
   const reviews = document.querySelector('.UY7F9')?.innerText?.trim() || '';
   const horario = document.querySelector('.o0Svhf, [data-attrid*="hour"] span')?.innerText?.trim() || '';
   // Buscar redes sociales en links del perfil
   const links = [...document.querySelectorAll('a[href]')].map(a => a.href);
   const instagram = links.find(l => l.includes('instagram.com')) || '';
   const facebook = links.find(l => l.includes('facebook.com')) || '';
   const whatsapp = links.find(l => l.includes('wa.me') || l.includes('whatsapp.com')) || '';
   ```

   **OBLIGATORIO:** nunca guardar un comercio sin haber visitado su perfil individual. El panel de lista no muestra teléfono de forma confiable.

3. **Filtrar resultados**

   **DESCARTAR si:**
   - Categoría Maps dice `Kiosco` o `Restaurante`
   - Nombre contiene: Carrefour, Dia, ChangoMás, Walmart, Coto, Jumbo, Vea, Disco, Express, Natural&Fresh

   **INCLUIR si categoría Maps dice:**
   - `Supermercado chino` ✅
   - `Tienda de alimentación` ✅
   - `Tienda general` ✅
   - `Supermercado` ✅
   - `Mercado` ✅
   - `Comercio` (evaluar por nombre) ⚠️

4. **Estructurar resultados** (formato completo — SIEMPRE estos campos)
   ```json
   {
     "nombre": "Supermercado Argenchino",
     "categoria": "Supermercado chino",
     "direccion": "Gavilán 4552",
     "zona": "Villa Pueyrredón",
     "telefono": "011 4571-8898",
     "es_celular": false,
     "whatsapp": "",
     "instagram": "",
     "facebook": "",
     "website": "",
     "rating": "3.9",
     "reviews": "152",
     "horario": "Abre a las 9 a.m.",
     "foto_url": "https://...",
     "url_maps": "https://maps.google.com/...",
     "canal": "WhatsApp|Instagram|Facebook|fijo|sin_contacto",
     "tiene_whatsapp": false,
     "estado": "pendiente",
     "fuente": "google_maps"
   }
   ```
   - `canal`: inferir según disponibilidad — WhatsApp si es celular (011 5xxx/15xxx), Instagram si tiene IG, Facebook si tiene FB, fijo si solo tiene fijo, sin_contacto si no hay nada
   - `es_celular`: true si el número empieza con 011 5, 011 15, o es un número de celular visible
   - Marcar los que ya estaban en la base como "ya contactado"

5. **Guardar resultados**
   - Agregar nuevos comercios a `data/outreach/comercios_[zona]_[fecha].json`
   - Si el directorio no existe → crearlo
   - Reportar: cuántos nuevos, cuántos descartados por filtro, cuántos tienen teléfono

6. **Reporte**
   - Total encontrados / descartados / netos
   - Breakdown por tipo
   - Próximo paso sugerido: `/enviar-outreach` con estos comercios
