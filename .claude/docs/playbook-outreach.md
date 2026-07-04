# Playbook de Outreach — Brújula de Precios

> Cómo contactar comerciantes para que prueben la app. Destilado de 8 skills de marketing
> (cold-email, copywriting, copy-editing, marketing-psychology, customer-research, free-tool-strategy,
> product-marketing-context, pricing-strategy, ad-creative, competitor-alternatives) y tácticas
> actuales de la web. Molde aprobado por Facu el 15/06/2026.

## Registro: FORMAL y PROFESIONAL (trato de usted)
Nada de chamuyo ni tono "del barrio". Somos correctos y profesionales. El comerciante tiene que
terminar el mensaje entendiendo TODO el servicio y poder contárselo a otro. Nos estamos
promocionando: el mensaje vende el servicio, con honestidad.

## MENSAJE OFICIAL (molde)

> Buenos días. Mi nombre es Facundo Sosa, trabajo como analista de precios y desarrollé una
> herramienta web, Brújula de Precios, que compara los precios de Yaguar, Maxiconsumo y
> MaxiCarrefour para ver en cuál conviene comprar cada producto antes de hacer el pedido.
>
> La herramienta revisa automáticamente, todos los días, los precios publicados por los tres
> mayoristas en sus sitios web y los reúne en una sola pantalla. Es un comparador independiente:
> no vende productos ni reemplaza a ningún mayorista, únicamente indica dónde conviene comprar.
>
> Pensé que podía resultarle útil. Por ejemplo, el aceite Cocinero 900 ml figura a $4.300 en
> Maxiconsumo y a $2.755 en MaxiCarrefour: una diferencia de $1.545 por unidad (36%). Tiene más de
> 18.000 productos e incluye una calculadora que sugiere el precio de venta según el margen que
> desee y la opción de armar listas de compra, entre otras funciones.
>
> Por el momento está en fase de prueba, así que cualquier comentario suyo me sería de mucha
> utilidad. Le dejo el enlace por si desea probarla: https://v0-brujula-de-precios.vercel.app
>
> Quedo a disposición por cualquier consulta. Saludos cordiales, Facundo Sosa.

### Qué es FIJO y qué VARÍA
- 🔒 **Fijo:** todo el cuerpo (presentación como analista, cómo funciona, posicionamiento, escala,
  calculadora, fase de prueba, cierre).
- 🔄 **Varía por comercio:** SOLO el ejemplo del párrafo 3 → un producto que **ese comercio venda**
  (leído de la foto de su local en Maps) + precios reales del catálogo de hoy + ahorro en $ y %.
- **Saludo según horario:** "Buenos días" (mañana), "Buenas tardes" (tarde). Se mandan de día.

## Reglas del mensaje (de las skills)
1. **"Precios publicados"** es la palabra de confianza para explicar el scraping. NUNCA decir
   "scrapea" ni "bot": decir "revisa automáticamente los precios publicados en sus sitios web".
   Son datos que el mayorista muestra abierto, nada turbio.
2. **Posicionar por lo que NO es:** "no vende, no es un mayorista" → desactiva el "¿qué me quiere
   vender?".
3. **Ancla de precio:** mostrar el caro primero y después el barato. Combinar % y $ (el % comunica
   magnitud, el $ lo hace concreto).
4. **Pedir feedback, no uso:** "está en fase de prueba, su comentario me sería útil" baja la presión
   y da un motivo real para responder.
5. **Honestidad total:** nunca inventar prueba social ni exagerar ahorros. El de barrio lo detecta.
6. **Ortografía impecable:** tildes y puntuación cuidadas — somos analistas, la forma da autoridad.

## Cómo elegir el producto del ejemplo (variable)
- Mirar la foto de fachada/góndola del comercio en Maps → ver qué marcas vende.
- `python scripts/buscar_producto.py <termino>` → ahorro real de hoy en ese producto.
- Elegir un producto de **alto consumo y reconocible** (aceite, gaseosa, cerveza, yerba, fideos,
  lavandina) con ahorro claro, NO el de mayor % si es un producto raro.
- Verificar que el ahorro sea real (3 precios > 2 precios; evitar outliers, ver reglas 08 y 09).

## El flujo
1. **Buscar comercios** por zona en Google Maps (Puppeteer): búsqueda por rubro+barrio → filtrar ICP
   (kioscos, almacenes, autoservicios, súper chinos) → descartar verdulerías, gasolineras, cadenas.
2. **Sacar el canal** entrando a cada ficha: celular/Instagram/Facebook = contactable digital;
   solo fijo = visita o llamada. Priorizar los digitales.
3. **Investigar qué vende** cada uno (foto de fachada) → elegir el producto del ejemplo.
4. **Armar el mensaje** con el molde + su producto.
5. **Enviar** por el canal de cada uno (WhatsApp / Instagram DM / Facebook).
6. **Un solo follow-up** a los 3-4 días si no responde, con otro ejemplo de ahorro. Después soltar.
7. **Lote chico y profundo:** 10-15 por tanda, no 100. Calidad mata volumen.

## Palanca paralela (más alcance) — pendiente, NO ahora
Grupos de Facebook/WhatsApp de comerciantes de CABA (kiosqueros, almaceneros por comuna) + 1 video
corto mostrando un ahorro real. Un posteo llega a cientos vs 1 DM = 1 persona. Orden: grupos →
captás interesados → mensaje a esos → referido cuando uno quede contento. Hacer DESPUÉS de cerrar
la tanda 1 a 1 (no abrir el frente ahora).

## Herramientas del flujo
- `python scripts/buscar_producto.py <termino>` → ahorro real de hoy en un producto.
- `python scripts/bombas_por_tipo.py <kiosco|almacen|minimercado>` → top ahorros por tipo.
- Google Maps vía Puppeteer → buscar comercios + sacar canal y qué venden.
- Base de comercios: `data/outreach/comercios_<zona>_<fecha>.json` (campos `canal` y `estado`).
