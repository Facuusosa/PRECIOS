# Rules: Testing

## Bucle verificador (obligatorio después de TODA tarea)
```
MIENTRAS resultado no sea óptimo:
  1. Verificar concretamente — leer archivo, contar productos, revisar logs
  2. Juzgar — ¿los números tienen sentido? ¿hay algo raro?
  3. Si hay problema → identificar causa → corregir → volver a 1
  4. Si está bien → reportar qué se verificó y el resultado
FIN
```
No es una verificación única. Es un bucle. Nunca decir "listo" después de un solo check.

## Verificación post-scraping
1. ¿Se generó `output_mayorista_YYYYMMDD_HHMMSS.json`?
2. ¿Cuántos productos? (Yaguar >3000, Carrefour >3000, Maxiconsumo >500)
3. ¿Precios > 0 en la mayoría de productos?
4. ¿`catalogo_unificado.json` tiene fecha de hoy?

## Verificación post-cambio frontend
1. `npx tsc --noEmit` — sin errores TypeScript
2. `npm run lint` — sin warnings críticos
3. Las 4 vistas cargan en `localhost:3000`
4. El calculador funciona end-to-end (precio compra → margen → precio venta)
5. Sin errores en consola del browser

## Cambios de ranking/orden — verificar visualmente, no solo tsc (06/07/2026)

`tsc --noEmit` sin errores no prueba que el comportamiento visible cambió. Puede haber
MÁS DE UN punto que reordena/filtra la misma lista antes de llegar a la pantalla.

Caso real: se fijó el Fernet Branca X750 como bomba #1 tocando solo `calcularBombas()`
en `lib/data.ts`. Compiló bien, parecía completo. Pero `vista-inicio.tsx` tiene su propia
función `rankearTop()` que vuelve a ordenar el array de bombas con otro criterio — el fix
quedó invisible en producción durante un commit entero hasta que Facu preguntó por qué
no se veía.

**Regla:** antes de dar por terminado un fix de ranking/orden/filtro:
1. `grep` el nombre de la función que arma el array final en TODOS los componentes que
   la consumen — no asumir que solo se ordena una vez donde se calcula.
2. Levantar `npm run dev` local y verificar con Puppeteer (screenshot real de la pantalla
   que el usuario ve) ANTES de commitear. Leer el código de nuevo no alcanza si ya se
   leyó una vez y "se veía bien".

## Verificación post-pipeline completo
```bash
python scrape_yaguar.py        # verifica output + producto count
python scrape_maxicarrefour.py # verifica output + producto count
python scrape_maxiconsumo.py   # verifica output + producto count
# catalogo_unificado.json actualizado automáticamente
python start_web.py            # localhost:3000 con data fresca
```

## Principios
- Tests de tipo + lint verifican corrección del código — no corrección de features
- Si no se puede testear la UI, decirlo explícitamente en vez de asumir que funciona
- No mockear la DB o scrapers en tests — mejor datos reales aunque sean lentos
