# BRÚJULA DE PRECIOS - Comandos de Scraping

## 4 Comandos Simples para Todo el Sistema

### 1. Scrapear Yaguar
```bash
python scrape_yaguar.py
```
- Scrapea ~11,848 productos de Yaguar
- Ejecuta pipeline de unificación automáticamente
- Genera `catalogo_unificado.json`

### 2. Scrapear MaxiCarrefour
```bash
python scrape_maxicarrefour.py
```
- Scrapea ~3,900 productos de MaxiCarrefour
- Ejecuta pipeline de unificación automáticamente
- Genera `catalogo_unificado.json`

### 3. Scrapear Maxiconsumo
```bash
python scrape_maxiconsumo.py
```
- Scrapea ~4,900 productos de Maxiconsumo
- Ejecuta pipeline de unificación automáticamente
- Genera `catalogo_unificado.json`

### 4. Levantar Servidor Web
```bash
python start_web.py
```
- Verifica que exista `catalogo_unificado.json`
- Instala dependencias Node.js si es necesario
- Construye la aplicación web
- Inicia servidor en http://localhost:3000

## Flujo de Trabajo Recomendado

### Opción 1: Scraping Individual
```bash
# 1. Scrapear un competidor
python scrape_yaguar.py

# 2. Iniciar servidor web
python start_web.py
```

### Opción 2: Scraping Completo
```bash
# 1. Scrapear todos los competidores
python scrape_yaguar.py
python scrape_maxicarrefour.py
python scrape_maxiconsumo.py

# 2. Iniciar servidor web
python start_web.py
```

## Características de Cada Comando

### Comandos de Scraping
- **Verificación de dependencias**: Revisa que las librerías necesarias estén instaladas
- **Ejecución con retry**: Usa el sistema de reintentos automático
- **Validación de outputs**: Verifica que los datos sean válidos
- **Pipeline automático**: Ejecuta `actualizar_catalogo.py` automáticamente
- **Feedback claro**: Muestra resultados y ubicación de archivos

### Comando de Servidor Web
- **Verificación de catálogo**: Asegura que existan datos para mostrar
- **Instalación automática**: Instala dependencias Node.js si es necesario
- **Construcción**: Compila la aplicación Next.js
- **Modo desarrollo/producción**: Permite elegir el modo de servidor
- **Información del catálogo**: Muestra estadísticas de los datos

## Archivos Generados

### Outputs de Scraping
- `targets/yaguar/output_yaguar_TIMESTAMP.json`
- `targets/maxicarrefour/output_maxicarrefour_TIMESTAMP.json`
- `targets/maxiconsumo/output_maxiconsumo_TIMESTAMP.json`

### Datos Unificados
- `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`

## Requisitos Previos

### Python
- Python 3.8 o superior
- Ejecutar: `pip install -r requirements.txt`

### Node.js (solo para servidor web)
- Node.js 16 o superior
- npm instalado

## Troubleshooting

### Si un scraper falla:
1. Revisa la conexión a internet
2. Verifica que el sitio del supermercado esté accesible
3. Revisa los logs en `logs/`

### Si el servidor web no inicia:
1. Asegúrate de haber ejecutado al menos un scraper
2. Verifica que `catalogo_unificado.json` exista
3. Revisa que Node.js esté instalado

### Si faltan dependencias:
```bash
# Python
pip install -r requirements.txt

# Node.js (automático con start_web.py)
npm install
```

## Tips de Uso

1. **Prueba con un scraper primero**: Comienza con `python scrape_yaguar.py`
2. **Verifica los outputs**: Revisa que los archivos JSON se generen correctamente
3. **Usa modo desarrollo**: Para testing, elige modo 1 en el servidor web
4. **Datos en tiempo real**: Cada scraper actualiza el catálogo automáticamente
