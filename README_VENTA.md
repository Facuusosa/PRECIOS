# BRÚJULA DE PRECIOS - Sistema de Scraping Profesional

## Descripción del Producto

**BRÚJULA DE PRECIOS** es un sistema completo de scraping web profesional diseñado para extraer datos de productos de los principales supermercados de Argentina. El sistema incluye 3 scrapers funcionales, una interfaz web para visualización de datos y una arquitectura robusta y escalable.

### Características Principales

- **3 Scrapers Funcionales**: Yaguar, MaxiCarrefour y Maxiconsumo
- **Interfaz Web Moderna**: Next.js con TailwindCSS y componentes de UI profesional
- **Datos Estructurados**: Formato JSON unificado con información completa de productos
- **Sistema de Configuración**: Gestión centralizada de credenciales y configuraciones
- **Arquitectura Limpia**: Código modular, sin dependencias complejas
- **Listo para Producción**: Sistema probado y funcional

## Scrapers Incluidos

### 1. Yaguar Scraper
- **Productos**: ~11,848 productos
- **Categorías**: 12 categorías principales
- **Autenticación**: Login con credenciales
- **Tecnología**: curl_cffi con impersonation Safari 15.3
- **Output**: JSON con precios, nombres, SKU, imágenes y categorías

### 2. MaxiCarrefour Scraper
- **Productos**: ~4,000 productos
- **Sectores**: 10 sectores principales
- **Autenticación**: Cookies de sesión
- **Tecnología**: API REST + requests
- **Output**: JSON con EAN, precios, nombres y categorías

### 3. Maxiconsumo Scraper
- **Productos**: ~500+ productos (configurable)
- **Estrategias**: Categorías + Listado Maestro
- **Tecnología**: curl_cffi con impersonation Safari 15.3
- **Output**: JSON con datos enriquecidos y deduplicación

## Estructura de Datos

Todos los scrapers generan el mismo formato JSON estándar:

```json
{
  "nombre": "NOMBRE COMPLETO DEL PRODUCTO",
  "sku": "CÓDIGO SKU",
  "precio": 0.00,
  "imagen": "URL_IMAGEN",
  "link": "URL_PRODUCTO",
  "categoria": "CATEGORÍA",
  "fuente": "SUPERMERCADO",
  "fecha": "YYYY-MM-DD"
}
```

## Instalación y Configuración

### Requisitos Previos
- Python 3.8+
- Node.js 16+
- pip y npm

### Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone <repositorio>
cd BRUJULA-DE-PRECIOS

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Instalar dependencias Node.js
cd BRUJULA-DE-PRECIOS
npm install
cd ..

# 4. Configurar el sistema
python config.py

# 5. Actualizar credenciales (opcional)
python -c "from config import update_yaguar_credentials; update_yaguar_credentials('usuario', 'contraseña')"
```

## Uso del Sistema

### Comandos de Scraping

```bash
# Scrapear Yaguar
python scrape_yaguar.py

# Scrapear MaxiCarrefour
python scrape_maxicarrefour.py

# Scrapear Maxiconsumo
python scrape_maxiconsumo.py

# Iniciar interfaz web
python start_web.py
```

### Salida Generada

- **Archivos JSON**: `targets/[supermercado]/output_[supermercado]_[timestamp].json`
- **Catálogo Unificado**: `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
- **Logs**: `targets/[supermercado]/scraper_log.txt`

## Interfaz Web

La interfaz web ofrece:

- **Dashboard Principal**: Vista general de productos y precios
- **Búsqueda Avanzada**: Filtrado por nombre, categoría, precio
- **Comparación de Precios**: Productos similares entre supermercados
- **Visualización de Datos**: Gráficos y estadísticas
- **Exportación**: Descarga de datos en múltiples formatos

### Acceso a la Web

```bash
# Iniciar servidor web
python start_web.py

# Acceder a la aplicación
http://localhost:3000
```

## Configuración Avanzada

### Archivo de Configuración

El sistema utiliza `config.py` para gestionar todas las configuraciones:

- **Credenciales**: Usuario y contraseña de Yaguar
- **Cookies**: Sesión de MaxiCarrefour
- **Headers**: User agents y configuraciones HTTP
- **Límites**: Mínimos de productos esperados
- **Delays**: Tiempos de espera entre peticiones

### Actualización de Configuración

```bash
# Actualizar credenciales de Yaguar
python -c "from config import update_yaguar_credentials; update_yaguar_credentials('nuevo_usuario', 'nueva_contraseña')"

# Actualizar cookies de MaxiCarrefour
python -c "from config import update_maxicarrefour_cookies; update_maxicarrefour_cookies('nuevo_phpsessid', 'nuevo_cf_clearance')"
```

## Arquitectura Técnica

### Dependencias Principales

**Python Backend:**
- `requests>=2.31.0` - Cliente HTTP
- `beautifulsoup4>=4.12.0` - Parsing HTML
- `curl_cffi>=0.6.0` - Cliente HTTP avanzado
- `pandas>=2.0.0` - Procesamiento de datos

**Frontend:**
- `Next.js 16` - Framework React
- `TailwindCSS` - Estilos CSS
- `Radix UI` - Componentes UI
- `Framer Motion` - Animaciones

### Estructura de Directorios

```
BRUJULA-DE-PRECIOS/
|
|-- config.py                 # Configuración centralizada
|-- requirements.txt          # Dependencias Python
|-- scrape_yaguar.py         # Wrapper scraper Yaguar
|-- scrape_maxicarrefour.py   # Wrapper scraper MaxiCarrefour
|-- scrape_maxiconsumo.py    # Wrapper scraper Maxiconsumo
|-- start_web.py             # Inicio servidor web
|-- actualizar_catalogo.py   # Unificación de datos
|
|-- targets/
|   |-- yaguar/
|   |   |-- scraper_pro.py   # Scraper principal Yaguar
|   |   |-- output_*.json    # Archivos de salida
|   |   `-- scraper_log.txt  # Logs de ejecución
|   |
|   |-- maxicarrefour/
|   |   |-- scraper_pro.py   # Scraper principal MaxiCarrefour
|   |   |-- output_*.json    # Archivos de salida
|   |   `-- scraper_log.txt  # Logs de ejecución
|   |
|   `-- maxiconsumo/
|       |-- scraper_pro.py   # Scraper principal Maxiconsumo
|       |-- output_*.json    # Archivos de salida
|       `-- scraper_log.txt  # Logs de ejecución
|
|-- BRUJULA-DE-PRECIOS/
|   |-- package.json          # Dependencias Node.js
|   |-- next.config.js       # Configuración Next.js
|   |-- src/                  # Código fuente frontend
|   `-- data/                # Datos procesados
|
`-- config/                  # Archivos de configuración JSON
    |-- yaguar.json
    |-- maxicarrefour.json
    |-- maxiconsumo.json
    `-- general.json
```

## Características de Venta

### Valor Comercial

1. **Sistema Completo**: 3 scrapers funcionales + interfaz web
2. **Código Limpio**: Sin over-engineering, fácil de mantener
3. **Datos Reales**: Extracción de supermercados argentinos
4. **Escalable**: Arquitectura modular para agregar nuevos scrapers
5. **Profesional**: Documentación completa y configuración centralizada

### Casos de Uso

- **Análisis de Precios**: Comparación de precios entre supermercados
- **Inteligencia de Mercado**: Tendencias y precios de productos
- **Aplicaciones E-commerce**: Datos para plataformas de precios
- **Investigación de Mercado**: Estudios de consumo y precios
- **Desarrollo de Software**: Base para aplicaciones de comparación

### Soporte y Mantenimiento

- **Documentación Completa**: Guías de instalación y uso
- **Código Comentado**: Explicaciones claras en el código
- **Configuración Flexible**: Sistema centralizado de configuración
- **Logs Detallados**: Registro de operaciones y errores

## Licencia y Derechos

- **Código Fuente Completo**: Todos los scrapers y sistema web
- **Derechos de Uso**: Comercial, modificar y distribuir
- **Soporte Inicial**: Documentación y guía de configuración
- **Actualizaciones**: Arquitectura preparada para futuras mejoras

## Contacto y Soporte

Para soporte técnico, consultas o personalización:

- **Documentación**: Archivos README y comentarios en código
- **Configuración**: Sistema centralizado en `config.py`
- **Logs**: Archivos de registro en cada scraper
- **Issues**: Revisar `scraper_log.txt` para diagnóstico

---

**BRÚJULA DE PRECIOS** - Sistema profesional de scraping de supermercados argentinos
*Listo para producción y comercialización*
