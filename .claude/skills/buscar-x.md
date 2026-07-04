# Skill: /buscar-x

## Descripcion
Busca en X/Twitter tecnicas, ejemplos y patrones recientes sobre un tema de UI/UX o frontend antes de implementar. El objetivo es no reinventar la rueda — siempre hay alguien que ya resolvio el problema y lo compartio en X.

Usar ANTES de cualquier tarea de diseno o animacion para encontrar la mejor tecnica disponible.

## Uso
`/buscar-x [tema]` — donde tema es lo que se quiere implementar

Ejemplos:
- `/buscar-x dark mode toggle animation`
- `/buscar-x price comparison UI mobile`
- `/buscar-x framer motion spring tabs`
- `/buscar-x product card hover effects`

## Pasos

1. **Construir queries de busqueda**
   - Query principal: `site:x.com [tema]`
   - Query alternativa: `[tema] css/react/framer motion tip 2024 OR 2025`
   - Query de referentes: buscar en cuentas conocidas de UI: @emilkowalski_, @shadcn, @rauno, @lukewebdev

2. **Buscar con WebSearch**
   - Ejecutar 2-3 queries en paralelo
   - Filtrar resultados: preferir tweets con likes/retweets altos, code snippets, o demos
   - Ignorar contenido sin valor practico (opiniones sin ejemplos)

3. **Sintetizar hallazgos**
   - Identificar el patron o tecnica mas relevante para el problema
   - Si hay codigo: copiar el snippet relevante
   - Si hay demo/video: describir la tecnica key que se puede replicar

4. **Reportar antes de implementar**
   - "Encontre esto en X: [tecnica]. Voy a aplicarla de esta forma: [descripcion concreta]"
   - Pedir aprobacion si la tecnica cambia el enfoque planeado

5. **Aplicar o descartar**
   - Si hay algo util: aplicarlo en la implementacion
   - Si no hay nada nuevo: confirmar "No encontre nada mejor que el enfoque actual, sigo con el plan"

## Reglas
- Maximo 5 minutos de busqueda — si no encontre nada en 3 queries, seguir con el plan
- No bloquear la implementacion por buscar demasiado
- Si el skill ya se corrio para este tema en la sesion actual, no repetirlo

## Cuando usar (obligatorio)
- Antes de implementar cualquier animacion nueva
- Antes de disenar un componente UI que no existe en el proyecto
- Cuando la implementacion actual se ve "genérica" y no hay una solucion clara
