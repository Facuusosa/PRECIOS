# Skill: /railway-deploy — ARCHIVADO

> ⚠️ Railway fue dado de baja el 13/06/2026. El pipeline corre LOCAL en la PC de Facu.
> Esta skill está archivada. No usar a menos que se quiera reactivar Railway.

## Por qué se dio de baja
- Maxiconsumo bloquea IPs de datacenter (Cloudflare) → fallaba en la nube
- MaxiCarrefour necesita renovar cookies desde la PC local
- Costo $5/mes por entregar 2/3 de las fuentes recicladas/viejas

## Cómo reactivar (cuando haya ingresos y se quiera nube 24/7)
1. Conseguir proxy residencial para Maxiconsumo
2. Configurar CAPSOLVER_API_KEY en Railway para renovar cookies de MaxiCarrefour
3. Mover `archive/railway_pipeline.py` y `archive/railway.toml` a la raíz
4. Ver `archive/README.md` para instrucciones completas

## Pipeline actual (reemplaza a Railway)
```
pipeline_local.py        → corre los 3 scrapers + actualizar_catalogo.py + git push
actualizar_brujula.bat   → wrapper para Task Scheduler de Windows
```
Tarea programada: "Brujula - Actualizar precios", diaria 10:00, StartWhenAvailable.
