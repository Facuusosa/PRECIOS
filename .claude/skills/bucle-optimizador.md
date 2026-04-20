# Skill: /bucle-optimizador
## Descripcion
Auditoria completa del proyecto buscando mejoras reales con ROI. Propone top 3 oportunidades ordenadas por Impacto x Facilidad. Si se invoca via `/loop`, solo reporta — no implementa. Si se invoca manualmente, espera aprobacion antes de implementar.

## Modo automatico (cuando corre via /loop)
- NO implementar cambios automaticamente
- Escribir oportunidades encontradas a `.claude/audit_log.md` con timestamp
- Formato: `[DD/MM HH:MM] OPORTUNIDAD: [descripcion] | IMPACTO: [Alto/Medio/Bajo] | ESFUERZO: [1-4h]`
- El usuario revisara el log cuando vuelva y elegira que implementar

## Modo manual (invocacion directa)

### Paso 1 — Auditar codigo
- Revisar `actualizar_catalogo.py`: hay logica duplicada? funciones muy largas? oportunidades de optimizacion?
- Revisar scrapers en `targets/*/scraper_pro.py`: patrones repetidos entre los 3 que podrian factorizarse?
- Revisar `BRUJULA-DE-PRECIOS/lib/data.ts`: calculos ineficientes? tipos innecesariamente complejos?
- Revisar `BRUJULA-DE-PRECIOS/app/page.tsx`: re-renders innecesarios? estado que podria simplificarse?

### Paso 2 — Auditar datos
- Leer `BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json`
- Verificar: count productos, % con precios >0, distribucion de 1/2/3 mayoristas
- Hay productos con precios extremadamente altos o bajos? (posible error de scraping)
- Tasa de matching: mejoro o empeoro respecto al baseline (3018 con 2+ precios)?

### Paso 3 — Auditar frontend
- Correr `npx tsc --noEmit` en `BRUJULA-DE-PRECIOS/` — reportar errores TypeScript
- Las 4 vistas cargan sin errores de consola?
- El calculador de margen funciona end-to-end?
- Hay componentes que podrian simplificarse?

### Paso 4 — Evaluar contexto
- Mostrar % de contexto actual
- Si >60%: recomendar /compact antes de implementar cualquier mejora
- Si >75%: recomendar abrir nueva sesion para la implementacion

### Paso 5 — Proponer TOP 3 mejoras
Ordenar por: (Impacto en usuario o negocio) x (Facilidad de implementacion)
Formato para cada mejora:
```
MEJORA #N: [nombre corto]
Que: [descripcion en 1 linea]
Por que: [impacto concreto — velocidad, dinero, UX]
Esfuerzo: [estimacion realista]
ROI score: [Alto/Medio/Bajo]
```

### Paso 6 — Esperar aprobacion
"Elegis cual implementar? (1/2/3) o 'ninguna' para terminar"
- Si el usuario elige: implementar -> verificar -> reportar resultado
- Si el usuario quiere continuar el bucle: volver al Paso 1
- Si el usuario dice "ninguna": cerrar con resumen de lo auditado
