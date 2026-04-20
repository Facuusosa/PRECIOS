# Skill: /status-proyecto
## Descripcion
Semaforo rapido del estado completo de Brujula de Precios. Verificar scrapers, catalogo, deploy, cookies y proximos pasos. Reporta VERDE / AMARILLO / ROJO por componente.

## Pasos

1. **Scrapers — verificar ultimos outputs:**
   - Buscar archivos `targets/yaguar/output_yaguar_*.json` — ultimo timestamp y count de productos (esperado >3000)
   - Buscar archivos `targets/maxicarrefour/output_maxicarrefour_*.json` — ultimo timestamp y count (esperado >3000)
   - Buscar archivos `targets/maxiconsumo/output_maxiconsumo_*.json` — ultimo timestamp y count (esperado >500)
   - ROJO si el ultimo output tiene mas de 7 dias de antiguedad
   - ROJO si el count es significativamente menor que el esperado

2. **Catalogo — verificar catalogo_unificado.json:**
   - Leer `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
   - Contar: productos totales, con 2+ precios, con 3 precios
   - Verificar fecha de ultima modificacion del archivo
   - AMARILLO si tiene mas de 3 dias sin actualizarse

3. **Cookies MaxiCarrefour:**
   - La ultima renovacion fue el 16/04/2026
   - Calcular dias transcurridos desde entonces
   - AMARILLO si >20 dias, ROJO si >28 dias
   - Si ROJO: recordar que el proceso de renovacion esta en `.claude/docs/operaciones.md`

4. **Deploy Vercel:**
   - Verificar que el proyecto esta desplegado en Vercel
   - Estado del ultimo deploy

5. **Plan — proximos pasos:**
   - Leer `.claude/docs/plan.md` seccion de pendientes
   - Listar top 3 proximos pasos concretos

6. **Reportar en formato semaforo:**
   ```
   === STATUS BRUJULA DE PRECIOS ===
   Yaguar:        [VERDE/AMARILLO/ROJO] — X productos, ultima vez: DD/MM
   MaxiCarrefour: [VERDE/AMARILLO/ROJO] — X productos, ultima vez: DD/MM
   Maxiconsumo:   [VERDE/AMARILLO/ROJO] — X productos, ultima vez: DD/MM
   Catalogo:      [VERDE/AMARILLO/ROJO] — X productos, X con 2+ precios
   Cookies CF:    [VERDE/AMARILLO/ROJO] — X dias desde renovacion
   Deploy:        [VERDE/AMARILLO/ROJO] — [estado]
   
   PROXIMOS PASOS:
   1. [accion concreta]
   2. [accion concreta]
   3. [accion concreta]
   ```
