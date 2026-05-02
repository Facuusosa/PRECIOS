# Plan de Análisis y Mejora de Scrapers para Venta

Analizar y preparar los 3 scrapers existentes para que funcionen perfectamente y sean listos para comercialización.

## Estado Actual de los Scrapers

### 1. Yaguar (FUNCIONAL) - ✅
- **Archivo**: `targets/yaguar/scraper_pro.py`
- **Estado**: Funciona con login y paginación
- **Outputs**: Archivos JSON de 4MB+ con datos reales
- **Productos**: ~11,848 productos
- **Login**: Requiere credenciales (Martin/Martin2025)
- **Estructura**: 12 categorías, 73 páginas por categoría
- **Problema**: Importa módulos eliminados (error_handler, validator)

### 2. MaxiCarrefour (FUNCIONAL) - ✅
- **Archivo**: `targets/maxicarrefour/scraper_pro.py`
- **Estado**: Funciona con API por sectores
- **Outputs**: Archivos JSON de 1.5MB+ con datos reales
- **Productos**: ~3,900 productos
- **Cookies**: PHPSESSID y cf_clearance hardcodeados
- **Estructura**: 10 sectores, API /products
- **Problema**: Importa módulos eliminados (error_handler, validator)

### 3. Maxiconsumo (FUNCIONAL) - ✅
- **Archivo**: `targets/maxiconsumo/scraper_pro.py`
- **Estado**: Funciona con curl_cffi impersonate
- **Outputs**: Archivos JSON de 4.5MB+ con datos reales
- **Productos**: ~4,900 productos
- **Tecnología**: curl_cffi con safari15_3 impersonate
- **Estructura**: Categorías + listado maestro
- **Problema**: Importa módulos eliminados (error_handler, validator)

## Problemas Críticos a Resolver

### 1. Imports Rotos
- Todos los scrapers importan `error_handler` y `validator` (eliminados)
- Esto causa que los scrapers no funcionen
- **Solución**: Remover imports y código relacionado

### 2. Dependencias Faltantes
- Los scrapers usan `curl_cffi` pero no está en requirements.txt simplificado
- **Solución**: Agregar `curl_cffi>=0.6.0` a requirements.txt

### 3. Credenciales y Cookies
- Yaguar necesita credenciales de login
- MaxiCarrefour necesita cookies actualizadas
- **Solución**: Sistema de configuración externa

## Plan de Mejoras

### Fase 1: Reparación Inmediata
1. **Limpiar imports** de módulos eliminados en los 3 scrapers
2. **Actualizar requirements.txt** con dependencias esenciales
3. **Probar cada scraper** individualmente

### Fase 2: Mejora para Producción
1. **Sistema de configuración** externa para credenciales/cookies
2. **Manejo de errores** simple sin over-engineering
3. **Logging básico** para debugging
4. **Validación de outputs** simple

### Fase 3: Preparación para Venta
1. **Documentación profesional** de cada scraper
2. **Instalador automático** (setup.py simple)
3. **Interfaz de configuración** para usuarios
4. **Testing automatizado** básico

## Estructura de Datos Unificada

Todos los scrapers generan el mismo formato:
```json
{
  "nombre": "NOMBRE PRODUCTO",
  "sku": "CÓDIGO",
  "precio": 0.00,
  "imagen": "URL_IMAGEN",
  "link": "URL_PRODUCTO",
  "categoria": "CATEGORÍA",
  "fuente": "SUPERMERCADO",
  "fecha": "YYYY-MM-DD"
}
```

## Comandos Finales

Después de las mejoras:
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales (una vez)
python setup_config.py

# Scrapear cada supermercado
python scrape_yaguar.py
python scrape_maxicarrefour.py
python scrape_maxiconsumo.py

# Levantar web
python start_web.py
```

## Entregable Final

- **3 scrapers funcionales** y listos para producción
- **Sistema web** para visualización de datos
- **Documentación completa** para usuarios
- **Instalador automático** para fácil despliegue
- **Configuración externa** para credenciales
