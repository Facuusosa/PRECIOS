> ⚠️ ARCHIVADO — la información útil fue fusionada en `.claude/docs/plan.md`. Ver plan.md para el estado actual.

# Próxima Fase — Auth, Pagos y Vistas (POST-MVP)

> Este plan se activa cuando haya al menos 1 usuario pagando.
> No implementar antes — es overhead sin tracción validada.

---

## Qué hay que definir antes de arrancar

### 1. Tiers — definir exactamente qué tiene cada uno
*(Pendiente de decisión de Facu)*

| Tier | Precio | Features |
|---|---|---|
| FREE | $0 | ? |
| TIER2 | ? ARS/mes | ? |
| TIER3 | ? ARS/mes | ? |

Preguntas a responder:
- ¿Cuántos mayoristas muestra el tier FREE?
- ¿Hay límite de búsquedas en FREE?
- ¿El calculador de margen está en FREE o es premium?
- ¿El historial de precios va en Tier2 o Tier3?

### 2. Stack de auth — elegir uno
Opciones (ordenadas por velocidad de implementación):

| Opción | Pro | Contra |
|---|---|---|
| **SuperBase** | Auth + DB + storage en 1 plataforma, plan free generoso | Plataforma externa |
| **NextAuth.js** | Control total, sin plataforma | Hay que armar la DB |
| **Clerk** | El más rápido de integrar (minutos) | $25/mes si crece |

### 3. Pagos — elegir uno
Opciones para Argentina:

| Opción | Pro | Contra |
|---|---|---|
| ~~MercadoPago~~ | Estándar AR, sin fricción para usuarios | API compleja, comisiones altas |
| **Stripe** | API excelente, fácil de integrar | Más fricción para usuarios AR |
| **Lemon Squeezy** | Todo incluido (checkout + impuestos) | Menos conocido en AR |

### 4. Vistas a crear
- [ ] `/login` — formulario de acceso
- [ ] `/register` — registro con email
- [ ] `/cuenta` — actualizar con datos reales del usuario
- [ ] `/planes` — comparador de tiers con CTA de pago
- [ ] Feature gating en todas las vistas (ocultar/mostrar según tier)

---

## Railway para scrapers en la nube

Railway plan Hobby ($5/mes) — ya contratado. Usar para:

### Opción A: Cron job scraping
- Subir los 3 scrapers Python a Railway
- Configurar cron: `0 6 * * *` (6am todos los días)
- Pipeline: scraper → actualizar_catalogo.py → subir JSON a Vercel via webhook
- Variables de entorno en Railway: YAGUAR_USERNAME, CARREFOUR_PHPSESSID, etc.

### Opción B: API de precios
- Exponer endpoint `GET /catalog` que devuelve el catálogo actual
- El frontend de Vercel consulta Railway en vez de un JSON local
- Permite actualizaciones sin redeploy del frontend

### Recomendación
Empezar con Opción A (más simple). Migrar a B cuando el catálogo sea demasiado grande para JSON.

### Pasos para configurar Railway
1. Crear proyecto en railway.app conectado al repo de GitHub
2. Configurar variables de entorno (desde el .env local)
3. Crear archivo `railway.toml` con cron job
4. Verificar que el primer run produce output_*.json válido
5. Agregar webhook a Vercel para re-deploy automático cuando el catálogo se actualiza

---

## Orden de implementación cuando sea el momento

```
1. Definir tiers exactamente (30 min de decisión)
2. Railway setup → scrapers automáticos (2-3h)
3. Auth (SuperBase o NextAuth) → login/registro (3-4h)
4. Vistas /login, /register, /planes (2-3h)
5. Feature gating en frontend (1-2h)
6. Pagos → al final, cuando haya usuarios listos para pagar
```

**Total estimado: ~12-15h de sesiones Claude Code**

---

## Señal de cuándo activar este plan
- Al menos 1 usuario usando activamente el producto
- Al menos 1 persona que dijo "pagaría por esto"
- O Facu decide que quiere tener la infraestructura lista antes del primer cliente
