# Skill: /investigar-y-contactar

## Descripcion
Para cada comercio de la lista, investiga quien es, que vende, y genera un email personalizado
que muestra ejemplos reales de ahorro para SU negocio + presenta Brujula de Precios.
Siempre mostrar borrador a Facu para aprobacion antes de crear el draft en Gmail.

## Input esperado
- Nombre del comercio (o fila del xlsx)
- Tipo: kiosco / almacen / minimercado
- Zona (barrio)
- Telefono y/o email si tiene

## Pasos

### 1. Investigacion del comercio (2-3 min por comercio)
- WebSearch: "{nombre} {zona} Buenos Aires" — buscar Google Maps, Facebook, Instagram
- Si aparece Facebook o web: WebFetch para leer que venden, que publican, que ofertas tienen
- Anotar:
  - Tiene presencia web? (si/no)
  - Que tipo de productos destaca (bebidas, snacks, limpieza, etc.)
  - Algun detalle especifico que permita personalizar (ej: "venden mucho Heineken", "tienen fiambreria")
  - Tiene email de contacto? Si tiene → usar para el mail. Si no → usar WhatsApp

### 2. Obtener bombas relevantes para ese tipo de negocio
Correr: `python scripts/bombas_por_tipo.py {tipo} 5`
- Si la investigacion revela productos especificos → filtrar del resultado los mas relevantes
- Elegir 2-3 ejemplos maximos para el email (no abrumar)
- Priorizar: productos de alto consumo + mayor % de ahorro

### 3. Redactar el mensaje personalizado
Estructura OBLIGATORIA — tono cálido, founder buscando feedback, NO marketing:

**Asunto (email):** "Una página que armé para comerciantes — ¿le echás un vistazo?"

**Cuerpo — template base (adaptar según canal y horario):**
```
Hola [Nombre]! [Buenos días / Buenas tardes / Buenas noches].

Me llamo Facundo, y estoy armando una página que se llama Brújula de Precios.

La idea es que compare automáticamente los precios de Yaguar, MaxiCarrefour
y Maxiconsumo, para que antes de ir a comprar sepas en cuál te conviene más
cada producto.

[PERSONALIZACIÓN — 1 ejemplo concreto verificado del catálogo:]
Por ejemplo, la [Producto] hoy está:
- [Mayorista A]: $X.XXX
- [Mayorista B]: $X.XXX
Comprando en [Mayorista A] te ahorrás $X.XXX por [unidad/caja].

Todavía la estoy terminando de pulir, pero ya anda con precios de esta semana.
Si querés darle un vistazo, acá está sin costo:
https://v0-brujula-de-precios.vercel.app

Cualquier cosa que te llame la atención — buena o mala — me servís un montón
si me lo contás.

Saludos!
Facundo
```

**WhatsApp — versión corta (mismo tono, máximo 4 párrafos):**
```
Hola [Nombre]! [Buenos días/tardes].

Me llamo Facundo y estoy armando una página que compara los precios de
Yaguar, MaxiCarrefour y Maxiconsumo para comerciantes.

[1 ejemplo verificado del tipo de ese comercio]

Todavía la estoy terminando, pero ya anda. Si querés echarle un vistazo:
https://v0-brujula-de-precios.vercel.app

Saludos, Facundo
```

**Reglas del tono — CRITICAS:**
- Sin tecnicismos: nunca "desarrollador full stack", "plataforma", "solución", "ecosistema"
- Lenguaje de barrio, que lo entienda cualquiera: claro, simple, directo
- "Todavía la estoy terminando de pulir" → honestidad genera confianza, no la quita
- "Cualquier cosa que te llame la atención, me servís si me lo contás" → cálido, sin presión
- Saludo según horario: antes de 12h "Buenos días", 12-20h "Buenas tardes", después "Buenas noches"
- 1 solo ejemplo de precio en todo el mensaje — verificado en el catálogo antes de enviar
- Si no hay info de investigación → usar el producto más consumido para ese tipo de negocio
- Nunca mencionar precio sin verificar primero en `scripts/bombas_por_tipo.py`

### 4. Mostrar a Facu para aprobacion
Antes de crear el draft, mostrar:
```
=== BORRADOR PARA: [Nombre Comercio] ===
Investigacion: [1-2 lineas de lo que encontre]
Canal: Email a [email] / WhatsApp a [telefono]

ASUNTO: [...]
CUERPO:
[...]

¿Aprobas, modificas o salteo este comercio?
```
Esperar confirmacion. No crear draft sin OK explicito.

### 5. Crear el draft (si hay email)
- Gmail MCP: `mcp__claude_ai_Gmail__create_draft`
- To: [email del comercio]
- Subject: [asunto]
- Body: [cuerpo en texto plano]
- Confirmar creacion y guardar ID del draft

### 6. Si solo tiene telefono (WhatsApp)
- No crear draft de email
- Generar version corta del mensaje para WhatsApp (max 3 parrafos)
- Guardar en data/outreach/whatsapp_pendientes.txt con formato:
  ```
  === [Nombre] | [Telefono] ===
  [mensaje]
  ```

### 7. Reporte final por comercio
```
[Nombre]: 
  - Investigacion: [hallazgo clave]
  - Canal: [email/whatsapp]
  - Draft: [creado / pendiente aprobacion]
  - Productos usados: [nombre1, nombre2]
```

## Ejecucion en lote
Para procesar multiples comercios:
- Buscar archivos JSON en `data/outreach/comercios_*.json` — usar el más reciente
- Filtrar tipo == 'Kiosco' O 'Almacen' O 'Minimercado' (excluir Mayorista)
- Filtrar los que no tengan estado "contactado"
- Procesar de a 5 por vez — mostrar reporte + pedir OK antes de los siguientes 5
- Al terminar cada lote: actualizar campo "estado" en el JSON

## Tokens y eficiencia
- Usar WebSearch (1 query) + WebFetch (1 URL max) por comercio
- Si el WebSearch no devuelve nada util: saltar directamente a bombas genericas
- No usar Puppeteer salvo que haya una URL especifica con contenido dinamico
- Procesar 5 comercios por sesion para no saturar contexto
