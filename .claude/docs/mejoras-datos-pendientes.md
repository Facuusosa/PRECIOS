# Mejoras de Datos — Pendientes (NO hacer ahora, hacer cuando se pueda)

> Creado 16/06/2026. Disparador: el azúcar Ledesma 1kg solo aparecía de Maxiconsumo.
> Al investigar se destapó que (a) no tenemos controles de cobertura del scraping y
> (b) no aprovechamos el histórico que ya venimos guardando. Facu quiere dejar esto
> documentado por pasos para ejecutarlo más adelante, sin dispersarse ahora.

---

## Diagnóstico que originó esto (caso azúcar Ledesma 1kg)

Tres problemas distintos, ninguno es límite del scraper:

1. **Yaguar no scrapeó NINGÚN azúcar de mesa** en la corrida del 23/05 (0 productos de
   cualquier marca). Un sector se cayó en silencio. Re-scrape disparado el 16/06.
2. **Matching no unifica la Ledesma 1kg** entre Maxiconsumo (`AZUCAR LEDESMA 1 KG`) y
   Carrefour (`Azucar Molida Clasica/Superior Ledesma Bolsa X 1 Kg`). Los nombres
   comparten pocas palabras → fuzzy Jaccard no supera umbral → quedan como fichas
   separadas. Por eso en la app se ve "la superior, que no es la misma".
3. No hay alerta automática para ninguno de los dos → pasó callado hasta que Facu lo vio.

---

## Arquitectura actual de datos (para entender el punto de partida)

NO hay base de datos. Todo son archivos JSON:

```
Scrapers ─► output_{mayorista}_{YYYYMMDD_HHMMSS}.json   (CRUDO, 1 por corrida)
            └─ se acumulan fechados en data/history/{yaguar,maxiconsumo,maxicarrefour}/
                    │   (YA es una serie temporal: ~6 semanas guardadas a 16/06)
actualizar_catalogo.py ─► BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json
                    │       (15MB, UNIFICADO, se PISA en cada corrida)
            App Next.js (Vercel) lee ese JSON. localStorage solo guarda lista del usuario.
```

**Clave:** la materia prima del histórico YA existe en `data/history/` y se sigue
acumulando. No se pierde nada mientras esto esté pendiente. No hay urgencia técnica.

---

## PENDIENTE 1 — Histórico de precios en la vista de detalle (PRIORIDAD: feature de producto)

**Objetivo de negocio (lo que pidió Facu):** en la vista de detalle de un material,
mostrar cómo varía el precio en el tiempo — entre todos los mayoristas y por competidor.
Es un insight por el que un comerciante paga (saber tendencia = saber cuándo comprar).
Esto SÍ acerca al primer pagador, por eso va primero.

**Ya tenemos a favor:**
- `recharts` 2.15.0 ya instalado → no hace falta dependencia nueva para el gráfico.
- Vista a tocar: `BRUJULA-DE-PRECIOS/components/vista-detalle.tsx`.
- ~6 semanas de corridas fechadas en `data/history/` → la serie arranca con datos reales.

**Pasos:**
1. **Base SQLite local** (un archivo, cero servidor, gratis). Ej. `data/precios_historico.db`.
   Tabla `precios(fecha DATE, mayorista TEXT, clave TEXT, ean TEXT, nombre TEXT, precio REAL)`.
   Índice por `(clave, mayorista, fecha)`.
2. **Script de ingesta inicial** `ingestar_historico.py`: recorre TODOS los
   `data/history/*/output_*.json`, extrae fecha del nombre de archivo, y puebla la BD.
   Resultado: histórico real de 6 semanas el día uno.
3. **Hook en el pipeline**: que cada corrida nueva inserte su foto del día en la BD
   (agregar paso en `pipeline_local.py` después de `actualizar_catalogo.py`).
4. **Generar series por producto** que la app pueda leer sin BD en runtime: un JSON
   `data/processed/historico_precios.json` con `{clave: [{fecha, mayorista, precio}]}`.
   (La app en Vercel lee JSON, no consulta SQLite — mantener ese patrón.)
5. **UI en `vista-detalle.tsx`**: mini gráfico de líneas con `recharts`, una línea por
   mayorista, eje X = fecha, eje Y = precio. Usar tokens de color del proyecto
   (ver `.claude/docs/frontend/styles.md`).
6. **Verificación**: elegir 1 producto conocido (ej. azúcar Ledesma 1kg), comparar la
   serie del gráfico contra los `output_*.json` crudos de esas fechas.

---

## PENDIENTE 2 — Guardarraíles de scraping (control interno, higiene de datos)

**Objetivo:** que nunca más un scraper deje de traer una categoría en silencio.

- **2a. Reporte por corrida** → `actualizar_catalogo.py` / `pipeline_local.py` escriben a
  archivo `data/quality/reporte_{fecha}.txt`: productos por fuente, precios en 0,
  precios sospechosos (regla 08), categorías presentes por mayorista.
- **2b. Alerta de cobertura por categoría**: definir un set de categorías esperadas por
  mayorista (ej. "Yaguar siempre tiene N azúcares de mesa"). Si una cae a 0 respecto de
  la corrida anterior → alertar y NO publicar (extender el chequeo anti-reciclaje que
  ya existe en `pipeline_local.py`).
- **2c. Reporte de matching**: cuántos productos quedan sin unificar entre mayoristas
  (huecos tipo Ledesma) para ir cerrándolos.

---

## PENDIENTE 3 — Cerrar el caso Ledesma puntual (rápido, casi listo)

- Re-scrape de Yaguar (disparado 16/06) para recuperar la categoría azúcar.
- Forzar el match de la Ledesma 1kg entre Maxiconsumo y Carrefour: agregar al mapeo
  manual `data/raw/mapeo_brujula.json`, o bajar el umbral fuzzy para este caso.
- Verificar que en la app quede una sola ficha comparable entre los 3 mayoristas.

---

## Orden recomendado (estratega)
1. Pendiente 3 (en curso, barato).
2. Pendiente 1 (feature de producto, acerca al pagador) — bloque dedicado.
3. Pendiente 2 (higiene) — cuando haya aire, después de tener tracción de ventas.

**Recordatorio anti-dispersión:** el bloqueador real de Brújula sigue siendo VENTAS.
Nada de esto se hace antes de tener el outreach en la calle, salvo el Pendiente 3.
