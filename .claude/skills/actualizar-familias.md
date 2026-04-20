# Skill: Actualizar Familias

Detecta pack mixing, sugiere FAMILIAs nuevas y actualiza el catálogo. Usar con `/actualizar-familias`.

## Pasos

1. **Correr el analizador**
   - `python analizar_familias.py`
   - Verificar que terminó sin errores
   - Leer las métricas que imprime: sospechosos totales, sugerencias por confianza (ALTA/MEDIA/BAJA)
   - Si hay error de importación → `pip install openpyxl` y reintentar

2. **Revisar sugerencias ALTA confianza**
   - Leer `data/raw/FAMILIAS_CUSTOM.xlsx` hoja FAMILIAS — filas con NOTAS = "SUGERIDA" y confianza ALTA
   - Mostrar al usuario: cuántas hay, con EAN + nombre + familia sugerida
   - Preguntar: "¿Aplico las X sugerencias ALTA confianza automáticamente?"
   - Si dice NO → saltar paso 3 y continuar

3. **Aplicar sugerencias ALTA confianza**
   - Abrir `data/raw/FAMILIAS_CUSTOM.xlsx` con openpyxl en modo escritura
   - Para cada fila SUGERIDA con confianza ALTA: cambiar NOTAS de "SUGERIDA" a "AUTO"
   - Guardar el Excel
   - Confirmar cuántas filas se actualizaron

4. **Re-correr el catálogo**
   - `python actualizar_catalogo.py`
   - Al terminar: leer `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
   - Verificar que `ultima_actualizacion` es de hoy

5. **Reporte final**
   - Sospechosos ratio >2.5x: antes (del paso 1) vs después
   - FAMILIAs activas en FAMILIAS_CUSTOM (filas totales hoja FAMILIAS, excl. encabezado)
   - Productos con 2+ precios comparables (antes vs después)
   - Si quedan sugerencias MEDIA confianza → mencionar cuántas hay para revisión manual en hoja REVISAR del Excel
   - Próximo paso concreto: si ratio bajó → celebrar y recordar correr `/pipeline-datos` después del próximo scraping
