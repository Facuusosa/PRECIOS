# Skill: /verificar-app

## Descripcion
Verifica el estado real de la app en produccion usando Puppeteer (o Chrome DevTools si esta activo).
Devuelve VERDE / AMARILLO / ROJO por seccion con screenshots como evidencia.

## Prerequisitos
- Puppeteer MCP activo (siempre disponible)
- Chrome DevTools MCP activo (si Facu abrio VSCode con Chrome ya iniciado con --remote-debugging-port=9222)
- URL de produccion: https://v0-brujula-de-precios.vercel.app

## Pasos

### 1. Navegar la app
```
puppeteer_navigate: https://v0-brujula-de-precios.vercel.app
puppeteer_screenshot: guardar como evidencia inicial
```

### 2. Verificar las 4 vistas

**Vista Inicio**
- Screenshot completo
- Verificar que carguen las "Bombas del dia" (top productos con mayor ahorro)
- Confirmar que Heineken 473ml aparece con precio ~$1.738 en Yaguar
- ROJO si no hay productos, AMARILLO si hay menos de 3, VERDE si hay 3+

**Vista Comparar**
- Buscar "Rexona" → verificar que NO aparezcan comparaciones con ratio >200% entre fuentes
- Buscar "Heineken" → precio Yaguar debe ser ~$1.738
- Buscar "Coca Cola" → verificar que tenga 2+ precios comparables
- ROJO si los resultados tienen precios absurdos, VERDE si son coherentes

**Calculadora de margen**
- Ingresar precio compra: 1000
- Ingresar margen deseado: 30
- Verificar que el precio sugerido sea ~$1.429 (1000 / 0.70)
- ROJO si no calcula, AMARILLO si el calculo es incorrecto, VERDE si funciona

**Vista Lista (guardados)**
- Guardar 1 producto desde Vista Comparar
- Ir a Vista Lista → verificar que aparece
- ROJO si no guarda o no aparece, VERDE si funciona

### 3. Verificar errores de consola
```
puppeteer_evaluate: 
  const errors = [];
  window.addEventListener('error', e => errors.push(e.message));
  // Reportar window.__console_errors si existe
```
Reportar cualquier error JS critico.

### 4. Guardar screenshots
Guardar evidencia en `data/quality/screenshots/verificacion_YYYYMMDD.png`
(o describir lo que se ve si no se puede guardar a disco)

### 5. Reporte final
```
=== VERIFICACION APP - [fecha] ===
Vista Inicio:     [VERDE/AMARILLO/ROJO] - [detalle]
Vista Comparar:   [VERDE/AMARILLO/ROJO] - [detalle]
Calculadora:      [VERDE/AMARILLO/ROJO] - [detalle]
Vista Lista:      [VERDE/AMARILLO/ROJO] - [detalle]
Errores JS:       [ninguno / lista]

Estado general: [VERDE si todo verde | AMARILLO si hay amarillos | ROJO si hay alguno rojo]
Proxima accion: [que hacer si hay problemas]
```

## Uso tipico
- Despues de cada deploy (push a git → Vercel redeploy)
- Antes de enviar mensajes a comercios (confirmar que la app funciona)
- Despues de correr el pipeline de datos (verificar que el catalogo nuevo se ve bien)

## Prioridad de herramienta
1. Chrome DevTools MCP (si activo) — mas rapido, controla el browser ya abierto
2. Puppeteer MCP — abre browser nuevo, siempre disponible
