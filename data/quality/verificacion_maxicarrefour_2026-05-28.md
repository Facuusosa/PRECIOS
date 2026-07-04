# Verificación de Precios MaxiCarrefour — 2026-05-28

**Método:** curl_cffi con cookies PHPSESSID + cf_clearance del .env  
**Endpoint:** `comerciante.carrefour.com.ar/products?method=productsList`  
**Scraper corrido:** `output_maxicarrefour_20260528_005530.json` — 5.067 productos  
**Catálogo actualizado:** `catalogo_unificado.json` — 18.046 productos totales, 3.029 con 2+ precios

---

## Top 5 Bombas verificadas (MaxiCarrefour más barato)

### 1. Caramelo Masticable Tutti Frutti Lenguetazo X 13 G
- **EAN:** 77907943  
- **Precio en catálogo:** $230  
- **Precio en API Carrefour:** $230.00  
- **Estado: OK** ✓  
- **Contexto:** Vs Yaguar $7.259 (96.8% ahorro) — gap extremo, probable falso match fuzzy con Yaguar

### 2. (G)Chocolate Con Mani Sapito X 10 Grs
- **EAN:** 77912718  
- **Precio en catálogo:** $318  
- **Precio en API Carrefour:** $318.00  
- **Estado: OK** ✓  
- **Contexto:** Vs Maxiconsumo $6.000 (94.7% ahorro) — gap extremo, probable falso match fuzzy con Maxiconsumo

### 3. Caramelos De Chocolate Butter Toffes X 80 Grm
- **EAN:** 7790580152109  
- **Precio en catálogo:** $1.410  
- **Precio en API Carrefour:** $1.410,00  
- **Estado: OK** ✓  
- **Contexto:** Vs Maxiconsumo $10.000 (85.9% ahorro) — gap extremo, probable falso match fuzzy con Maxiconsumo

### 4. Gelatina Cereza Light Royal X 25 Grs
- **EAN:** 7622201819736  
- **Precio en catálogo:** $1.129  
- **Precio en API Carrefour:** $1.129,00  
- **Estado: OK** ✓  
- **Contexto:** Vs Maxiconsumo $4.949 (77.2% ahorro) — gap extremo, probable falso match fuzzy con Maxiconsumo

### 5. Bizcochuelo Chocolate Godet Caja X 480 Grs
- **EAN:** 7790580131760  
- **Precio en catálogo:** $3.654  
- **Precio en API Carrefour:** $3.654,00  
- **Estado: OK** ✓  
- **Contexto:** Vs Maxiconsumo $8.795 (58.5% ahorro) — gap alto, verificar si es match correcto

---

## Resumen

| # | Producto | Catálogo | API Carrefour | Estado |
|---|----------|----------|---------------|--------|
| 1 | Lenguetazo Tutti Frutti 13g | $230 | $230 | OK |
| 2 | Sapito Chocolate Maní 10g | $318 | $318 | OK |
| 3 | Butter Toffees Chocolate 80g | $1.410 | $1.410 | OK |
| 4 | Royal Gelatina Cereza Light 25g | $1.129 | $1.129 | OK |
| 5 | Godet Bizcochuelo Chocolate 480g | $3.654 | $3.654 | OK |

**Coincidencias: 5/5 (100%)**  
**Diferencias: 0/5**

---

## Alerta de calidad — falsos matches

Los productos 1, 2, 3 y 4 muestran ahorros de 77-97% que son estadísticamente imposibles en el contexto mayorista. Sus nombres tienen "SIN NOMBRE" en el catálogo (nombre_yaguar y nombre_maxiconsumo vacíos), lo que indica que el matching fuzzy (Paso 6c) los unió incorrectamente a productos de Yaguar/Maxiconsumo que no corresponden.

**Acción recomendada:** Estos 4 productos deberían aparecer como comparativas individuales de MaxiCarrefour, no como "bombas" vs otros mayoristas. La lógica de bombas debería filtrar productos con `nombre == "SIN NOMBRE"` o sin nombre en los otros mayoristas para evitar mostrar falsos ahorros en el frontend.

---

*Reporte generado: 2026-05-28 | Verificador: Claude Code + curl_cffi*
