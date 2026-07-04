---
name: project_auditoria_28mayo
description: Resultado de auditoría post-limpieza del 28/05/2026 — estado general del proyecto Brújula de Precios
metadata:
  type: project
---

Auditoría ejecutada el 28/05/2026 después de limpieza de scripts y outputs.

**Por qué:** Verificar que la limpieza no rompió nada crítico antes de continuar con el desarrollo.

**Resultados clave:**
- Catálogo: 18.186 productos, 2.946 con 2+ precios comparables, 0 sin precio, actualizado hoy
- Frontend: 6 vistas OK, tsc sin errores, data.ts apunta a catalogo_unificado.json correcto
- Scrapers: 1 output cada uno (limpieza exitosa), counts razonables (Yaguar 12.664, MC 5.228, Maxiconsumo 9.775)
- Seguridad: .env en .gitignore, PHPSESSID y cf_clearance solo vía os.getenv() — no hardcodeados
- Deploy: .vercel/project.json existe, projectId=prj_yPhvVMNsKpGhcA86mBGeXDlRxPCs

**Deuda detectada:**
- `cache_off_imagenes.json` (217KB) y `skills-lock.json` (20KB) en raíz — huérfanos, candidatos a borrar
- `analizar_familias.py` (40 días sin tocar) — probable candidato a archivar
- `check_env_leak.py` (26 días sin tocar) — podría moverse a scripts/

**How to apply:** En próxima sesión de limpieza, borrar los 2 JSONs huérfanos y revisar analizar_familias.py.
