# Skill: Pipeline de Datos

Ejecuta el pipeline completo de scraping y actualización del catálogo. Usar con `/pipeline-datos`.

## Pasos

1. **Verificar entorno**
   - Leer `.env` — confirmar que existen las 4 variables: `YAGUAR_USERNAME`, `YAGUAR_PASSWORD`, `CARREFOUR_PHPSESSID`, `CARREFOUR_CF_CLEARANCE`
   - Si falta alguna → detener y avisar qué variable falta

2. **Correr Yaguar**
   - `python scrape_yaguar.py` (output en tiempo real)
   - Al terminar: verificar que se generó `targets/yaguar/output_yaguar_*.json` con >3000 productos

3. **Correr MaxiCarrefour**
   - `python scrape_maxicarrefour.py` (output en tiempo real)
   - Al terminar: verificar output con >3000 productos
   - Si devuelve 0 productos → las cookies expiraron. NO tocar el código. Avisar el proceso de renovación (ver docs/operaciones.md)

4. **Correr Maxiconsumo**
   - `python scrape_maxiconsumo.py` (output en tiempo real — incluye enriquecer_precios.py automáticamente)
   - Al terminar: verificar output con >500 productos

5. **Correr Coto (cadena)**
   - `python scrape_coto.py` (sin credenciales — API Constructor.io pública)
   - Al terminar: verificar output con >10.000 productos

6. **Correr Carrefour retail (cadena)**
   - `python scrape_carrefour.py` (sin credenciales — API VTEX pública)
   - Al terminar: verificar output con >8.000 productos y que las promos por cantidad no bajen de 5% (WARN del scraper)

7. **Verificar catálogo unificado**
   - Leer `data/processed/catalogo_unificado.json` — confirmar que la fecha `ultima_actualizacion` es de hoy
   - Contar productos totales y cuántos tienen 2+ precios comparables
   - Si el catálogo no se actualizó automáticamente → correr `python actualizar_catalogo.py`

8. **Reporte final**
   - Productos por fuente (con count — mayoristas y cadenas por separado)
   - Productos con 2+ precios comparables
   - Fecha de actualización del catálogo
   - Si algún scraper falló → qué falló y por qué (sin crashear los demás)
