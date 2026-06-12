# AUDITORIA CATALOGO BRUJULA DE PRECIOS - 2026-06-11
Archivo auditado: BRUJULA-DE-PRECIOS/data/processed/catalogo_unificado.json
Total productos: 17812

---

## RESUMEN EJECUTIVO
| Problema | Cantidad | Gravedad |
|---|---|---|
| Outliers Maxiconsumo (precio >2.5x mediana otras fuentes) | 23 | ALTA |
| Outliers generales por fuente | 22 | ALTA |
| Matches con gramaje/cantidad sospechosa | 101 | MEDIA-ALTA |
| Ahorros imposibles >60% (probable match incorrecto) | 58 | ALTA |
| Precios stale >30 dias | 0 | MEDIA |
| Precios sin fecha_scraping | 1497 | BAJA |
| Productos con flag precio_stale | 0 | INFO |

CRITICO: Los outliers Maxiconsumo y los ahorros >60% son los que generan precios incorrectos visibles al usuario.

---

## ANALISIS 1: OUTLIERS MAXICONSUMO (precio MC > 2.5x mediana otras fuentes)
Total casos: 23

| # | Nombre | EAN | Yaguar | MaxiCarrefour | Maxiconsumo | Ratio |
|---|---|---|---|---|---|---|
| 1 | Preservativo TULIPAN dispenser 12x3u | 7791014122033 | $2080 | $0 | $23500 | 11.3x |
| 2 | Alimento Gatos Gati Carne y Pollo 0.500 g Cp | 8445291478923 | $0 | $2267 | $23000 | 10.15x |
| 3 | CARAMELOS BUTTER TOFFEES LECHE 80 g |  | $1209 | $0 | $10000 | 8.27x |
| 4 | Caramelos BUTTER TOFFEES chocolate x80g | 7790580152109 | $1209 | $1410 | $10000 | 7.64x |
| 5 | FLYNN caram.confitado est.x50gr | 7790380002826 | $934 | $999 | $7300 | 7.55x |
| 6 | Gomitas MOGUL conitos x80g | 7790580152239 | $0 | $1395 | $10200 | 7.31x |
| 7 | CARAMELOS LIPO GAJITOS 150 g |  | $1030 | $0 | $6300 | 6.12x |
| 8 | ALIMENTO PARA GATOS GATI PESCADO y SALMON 1 kg |  | $4199 | $0 | $23000 | 5.48x |
| 9 | Caramelos PALITOS DE LA SELVA x150gr | 7790380258018 | $0 | $2070 | $10500 | 5.07x |
| 10 | PAPAS FRITAS SNACKO CLASICA 25 g |  | $934 | $0 | $4200 | 4.5x |
| 11 | Ginebra BOLS x195cc | 7790480090303 | $0 | $2889 | $11500 | 3.98x |
| 12 | Supremitas de pollo GDS +croc x480g | 7790070036148 | $9200 | $0 | $36390 | 3.96x |
| 13 | PAPAS FRITAS SNACKO CLASICA 40 g |  | $1135 | $0 | $4200 | 3.7x |
| 14 | Jugo CITRIC naranja x250ml | 7798085681445 | $0 | $1470 | $5300 | 3.61x |
| 15 | Hamburguesa PATY de cancha 2ux125g | 7790670052791 | $6582 | $0 | $22579 | 3.43x |
| 16 | WHISKY HIRAM WALKER 750 ml |  | $5435 | $0 | $16600 | 3.05x |
| 17 | Galletitas HOGAREÑAS salvado x200gr | 7790040132962 | $0 | $1229 | $3600 | 2.93x |
| 18 | Palitos de pollo SWIFT x260g | 7790360971135 | $5326 | $0 | $15000 | 2.82x |
| 19 | Panceta ahumada LARIO feteada x150g | 7790625005353 | $6799 | $0 | $18900 | 2.78x |
| 20 | Papas MC CAIN corte tradicional x400g | 7797906000700 | $4350 | $0 | $12000 | 2.76x |
| 21 | Shampoo ELVIVE Glycolic Gloss x200ml | 7509552937343 | $0 | $2868 | $7900 | 2.75x |
| 22 | Galletitas CRIOLLITAS x100gr | 7790040377707 | $0 | $529 | $1450 | 2.74x |
| 23 | Leche polvo LS descremada x200g | 7790742436207 | $3489 | $3099 | $8500 | 2.58x |

---

## ANALISIS 2: OUTLIERS GENERALES POR FUENTE (cualquier precio > 2.5x o < 0.4x mediana)
Total instancias: 22

| Mayorista | Casos outlier |
|---|---|
| yaguar | 5 |
| maxicarrefour | 3 |
| maxiconsumo | 14 |

Top 30 peores (mayor desviacion de la mediana):

| # | Nombre | EAN | Fuente outlier | Precio outlier | Mediana | Ratio | Tipo |
|---|---|---|---|---|---|---|---|
| 1 | FLYNN caram.confitado est.x50gr | 7790380002826 | maxiconsumo | $7300 | $999 | 7.31x | alto |
| 2 | Caramelos BUTTER TOFFEES chocolate x80g | 7790580152109 | maxiconsumo | $10000 | $1410 | 7.09x | alto |
| 3 | Manteca LA PAULINA pilon x5kg | 7790398000388 | maxiconsumo | $3830 | $47782 | 0.08x | bajo |
| 4 | Queso crema LA PAULINA pouch x4kg | 7794990879939 | maxiconsumo | $3000 | $21495 | 0.14x | bajo |
| 5 | Preservativo TULIPAN dispenser 12x3u | 7791014122033 | yaguar | $2080 | $12790 | 0.16x | bajo |
| 6 | Alimento Gatos Gati Carne y Pollo 0.500 g Cp | 8445291478923 | maxicarrefour | $2267 | $12633 | 0.18x | bajo |
| 7 | CARAMELOS FLYNNIES YOGHURT 600 g |  | maxiconsumo | $900 | $4447 | 0.2x | bajo |
| 8 | CARAMELOS FLYNNIES SURTIDOS 600 g |  | maxiconsumo | $900 | $4447 | 0.2x | bajo |
| 9 | Chocolate COFLER BLOCKAZO x1kg | 7790580115579 | maxiconsumo | $4000 | $19042 | 0.21x | bajo |
| 10 | CARAMELOS BUTTER TOFFEES LECHE 80 g |  | yaguar | $1209 | $5604 | 0.22x | bajo |
| 11 | Gomitas MOGUL conitos x80g | 7790580152239 | maxicarrefour | $1395 | $5797 | 0.24x | bajo |
| 12 | Queso hebras LA PAULINA ITAL. 4qsox400gr | 7794990880157 | maxiconsumo | $1650 | $6872 | 0.24x | bajo |
| 13 | Manteca PRIMER PREMIO x2.5kg | 7798085370097 | maxiconsumo | $5600 | $20695 | 0.27x | bajo |
| 14 | Barra cereal FLOW con yogurt 6ux27gr | 7790380016205 | maxiconsumo | $740 | $2620 | 0.28x | bajo |
| 15 | CARAMELOS LIPO GAJITOS 150 g |  | yaguar | $1030 | $3665 | 0.28x | bajo |
| 16 | JABON de TOCADOR VERITAS NECTAR de FRUTAS 3x1 |  | maxiconsumo | $800 | $2752 | 0.29x | bajo |
| 17 | ALIMENTO PARA GATOS GATI PESCADO y SALMON 1 k |  | yaguar | $4199 | $13599 | 0.31x | bajo |
| 18 | Caramelos PALITOS DE LA SELVA x150gr | 7790380258018 | maxicarrefour | $2070 | $6285 | 0.33x | bajo |
| 19 | PAPAS FRITAS SNACKO CLASICA 25 g |  | yaguar | $934 | $2567 | 0.36x | bajo |
| 20 | POSTRE ILOLAY CONFITES 110 g |  | maxiconsumo | $450 | $1220 | 0.37x | bajo |
| 21 | OBLEA NUGATON BLACK 27 g |  | maxiconsumo | $250 | $642 | 0.39x | bajo |
| 22 | LECHE en POLVO VITAL INFANTIL ETAPA 1 800 g |  | maxiconsumo | $11800 | $29640 | 0.4x | bajo |

---

## ANALISIS 3: MATCHES FUZZY SOSPECHOSOS (gramaje/cantidad diferente en nombre de fuente)
Total casos con discrepancia de cantidad >= 2x: 101

| # | Nombre display | EAN | Fuente | Nombre fuente | Qty display | Qty fuente | Ratio | Precio |
|---|---|---|---|---|---|---|---|---|
| 1 | Vino CANCILLER cabernet x1.125lt | 7790314065170 | maxicarrefour | Vino Tinto Cabernet Suavignon Canciller  | x1 | X 1125 | 1125.0x | $4193 |
| 2 | Vino Toro Viejo clasico tinto x1.125lt | 7790314005305 | maxicarrefour | Vino Tinto Toro Viejo X 1125 Cc | x1 | X 1125 | 1125.0x | $2992 |
| 3 | Vino CANCILLER blend x1.125lt | 7790314080142 | maxicarrefour | Vino Tinto Blend Iii Canciller Bot X 112 | x1 | X 1125 | 1125.0x | $3127 |
| 4 | Quitam AYUDIN colores vivos bot x1.5ml | 7793253003432 | maxicarrefour | Quitamanchas P Ropa Color Ayudin Bot X 1 | 1.5ml | 1.5 Lt | 1000.0x | $7399 |
| 5 | Quitam AYUDIN colores vivos bot x1.5ml | 7793253003432 | yaguar | QUITA MANCHAS AYUDIN COLORES VIVOS 1.5LT | 1.5ml | 1.5LT | 1000.0x | $5809 |
| 6 | Alimento Gatos Gati Carne y Pollo 0.500  | 8445291478923 | maxiconsumo | ALIMENTO PARA GATOS GATI CARNE Y POLLO 5 | 0.500 g | 500 GR | 1000.0x | $23000 |
| 7 | Yerba PIPORE tradicional x500gr | 7793750009838 | yaguar | YERBA PIPORE TRADICIONAL CLASICA 500KG | 500gr | 500KG | 1000.0x | $1649 |
| 8 | Limpiador PROCENEX brisa floral x1.8ml | 7791130963350 | yaguar | LIMPIADOR LIQUIDO PROCENEX BRISA FLORAL  | 1.8ml | 1,8LT | 1000.0x | $3845 |
| 9 | Lavavajillas MAGISTRAL marina x1.4lt | 7790990003121 | maxicarrefour | Detergente Ultra Marina Magistral Bot X  | x1 | X 300 | 300.0x | $1999 |
| 10 | ALIM. GATO fancy feast filet sal.x85gr | 7891000296158 | maxiconsumo | ALIMENTO PARA GATOS GATI CARNE Y POLLO 1 | 85gr | 15KG | 176.5x | $23000 |
| 11 | Pan lactal LA SANTIAGUEÑA chico x3 | 7793806000703 | maxicarrefour | Pan Lacteado Blanco La Santiaguena Bolsa | x3 | X 350 | 116.7x | $1580 |
| 12 | Agua saborizada VDS LEVITE pera x5 | 7798062540260 | maxicarrefour | Agua Saborizada Pera Sin Gas Vds Levite  | x5 | X 500 | 100.0x | $1700 |
| 13 | Desinfectante X5 clasico aerosol x360cc | 7792389000056 | maxicarrefour | Desinfectante Clasico Aerosol X.5 X 360  | X5 | X 360 | 72.0x | $3068 |
| 14 | Cerveza PATAGONIA 24.7 lata x473cc | 7792798001972 | maxicarrefour | Cerveza Varied 24.7Km Ipa Patagonia Lata | 24.7 l | 473Cc | 52.2x | $4019 |
| 15 | Hilo dental COLGATE 2x1 x50m | 7891024183120 | maxicarrefour | Hilo Dental Floss Lleva2 Paga1 Colgate X | x1 | X 50 | 50.0x | $4120 |
| 16 | HILO DENTAL COLGATE 2X1 50 ml |  | maxiconsumo | HILO DENTAL COLGATE 2X1 X50 ml | X1 | X50 | 50.0x | $260 |
| 17 | Limp. MULTIMAX multiuso lavanda x150ml | 7798184581103 | maxicarrefour | Limp Liq Lavanda Rinde 5Lt Multimax X 15 | 150ml | 5Lt | 33.3x | $1315 |
| 18 | Limp Liq Citrico Rinde 5 L Multimax 150  | 7798184581097 | maxicarrefour | Limp Liq Citrico Rinde 5Lt Multimax X 15 | 5 L | 150 Cc | 33.3x | $1315 |
| 19 | Limp. MULTIMAX multiuso cherry x150ml | 7798184581066 | maxicarrefour | Limp Liq Cherry Rinde 5Lt Multimax X 150 | 150ml | 5Lt | 33.3x | $1315 |
| 20 | Limp Liq Marina Rinde 5 L Multimax 150 m | 7798184581073 | maxicarrefour | Limp Liq Marina Rinde 5Lt Multimax X 150 | 5 L | 150 Cc | 33.3x | $1315 |
| 21 | Limp.MULTIMAX multiuso citronella x150ml | 7798184581738 | maxicarrefour | Limpiadro Liq Citronella Rinde 5Lt Multi | 150ml | 5Lt | 33.3x | $1315 |
| 22 | Jabon Antibacterial Aloe Protex 3 Uni 90 | 7509546688145 | maxicarrefour | Jabon Antibacterial Aloe Protex X 3 Uni  | x 3 | X 90 | 30.0x | $2505 |
| 23 | ALIM. PERRO dog chow peq.p/pollo s.x100g | 7891000244159 | maxiconsumo | ALIMENTO PARA ANIMALES DOG CHOW ADULTOS  | 100g | 3 KG | 30.0x | $8000 |
| 24 | Limp. MULTIMAX multiuso marina x35ml | 7798184581561 | maxicarrefour | Limpiador Liq Marina Rinde 1Lt Multimax  | 35ml | 1Lt | 28.6x | $685 |
| 25 | Limp. MULTIMAX multiuso lavanda x35ml | 7798184581554 | maxicarrefour | Limpiador Liq Lavanda Rinde 1Lt Multimax | 35ml | 1Lt | 28.6x | $685 |
| 26 | Limp. MULTIMAX multiuso coco-vain. x35ml | 7798184581547 | maxicarrefour | Limpiador Liq Coco Rinde 1Lt Multimax X  | 35ml | 1Lt | 28.6x | $685 |
| 27 | Limpiador Liq Cherry Rinde 1 L Multimax  | 7798184581523 | maxicarrefour | Limpiador Liq Cherry Rinde 1Lt Multimax  | 1 L | 35 Cc | 28.6x | $685 |
| 28 | Bombon BON O BON chocolinas cj. 18ux15gr | 7790580117771 | maxicarrefour | Bombones Chocolinas Bon O Bon Caja X 270 | 15gr | 270 Gr | 18.0x | $9649 |
| 29 | Bombon BON O BON chocolinas cj. 18ux15gr | 7790580117771 | maxiconsumo | BOMBON BON O BON CHOCOLINAS 270 GR | 15gr | 270 GR | 18.0x | $8700 |
| 30 | Bombon BON O BON aguila caja 18ux15g | 7790580102517 | maxicarrefour | Bombones Bon O Bon Aguila Caja 270G | 15g | 270G | 18.0x | $9649 |

... y 71 casos mas.

---

## ANALISIS 4: AHORROS IMPOSIBLES > 60% (probable match incorrecto o precio mal capturado)
Total casos: 58

| # | Nombre | EAN | Yaguar | MaxiCarrefour | Maxiconsumo | Fuente max | Fuente min | Ahorro% |
|---|---|---|---|---|---|---|---|---|
| 1 | Manteca LA PAULINA pilon x5kg | 7790398000388 | $91735 | $0 | $3830 | yaguar | maxiconsumo | 95.8% |
| 2 | Queso crema LA PAULINA pouch x4kg | 7794990879939 | $39990 | $0 | $3000 | yaguar | maxiconsumo | 92.5% |
| 3 | Preservativo TULIPAN dispenser 12x3u | 7791014122033 | $2080 | $0 | $23500 | maxiconsumo | yaguar | 91.1% |
| 4 | Alimento Gatos Gati Carne y Pollo 0.500 g Cp | 8445291478923 | $0 | $2267 | $23000 | maxiconsumo | maxicarrefour | 90.1% |
| 5 | CARAMELOS FLYNNIES YOGHURT 600 g |  | $7995 | $0 | $900 | yaguar | maxiconsumo | 88.7% |
| 6 | CARAMELOS FLYNNIES SURTIDOS 600 g |  | $7995 | $0 | $900 | yaguar | maxiconsumo | 88.7% |
| 7 | Chocolate COFLER BLOCKAZO x1kg | 7790580115579 | $0 | $34085 | $4000 | maxicarrefour | maxiconsumo | 88.3% |
| 8 | Caramelos BUTTER TOFFEES chocolate x80g | 7790580152109 | $1209 | $1410 | $10000 | maxiconsumo | yaguar | 87.9% |
| 9 | CARAMELOS BUTTER TOFFEES LECHE 80 g |  | $1209 | $0 | $10000 | maxiconsumo | yaguar | 87.9% |
| 10 | FLYNN caram.confitado est.x50gr | 7790380002826 | $934 | $999 | $7300 | maxiconsumo | yaguar | 87.2% |
| 11 | Queso hebras LA PAULINA ITAL. 4qsox400gr | 7794990880157 | $12095 | $0 | $1650 | yaguar | maxiconsumo | 86.4% |
| 12 | Gomitas MOGUL conitos x80g | 7790580152239 | $0 | $1395 | $10200 | maxiconsumo | maxicarrefour | 86.3% |
| 13 | Manteca PRIMER PREMIO x2.5kg | 7798085370097 | $35790 | $0 | $5600 | yaguar | maxiconsumo | 84.4% |
| 14 | CARAMELOS LIPO GAJITOS 150 g |  | $1030 | $0 | $6300 | maxiconsumo | yaguar | 83.7% |
| 15 | Barra cereal FLOW con yogurt 6ux27gr | 7790380016205 | $4500 | $0 | $740 | yaguar | maxiconsumo | 83.6% |
| 16 | JABON de TOCADOR VERITAS NECTAR de FRUTAS 3x1 |  | $4705 | $0 | $800 | yaguar | maxiconsumo | 83.0% |
| 17 | ALIMENTO PARA GATOS GATI PESCADO y SALMON 1 k |  | $4199 | $0 | $23000 | maxiconsumo | yaguar | 81.7% |
| 18 | Caramelos PALITOS DE LA SELVA x150gr | 7790380258018 | $0 | $2070 | $10500 | maxiconsumo | maxicarrefour | 80.3% |
| 19 | PAPAS FRITAS SNACKO CLASICA 25 g |  | $934 | $0 | $4200 | maxiconsumo | yaguar | 77.8% |
| 20 | POSTRE ILOLAY CONFITES 110 g |  | $1990 | $0 | $450 | yaguar | maxiconsumo | 77.4% |
| 21 | OBLEA NUGATON BLACK 27 g |  | $1035 | $0 | $250 | yaguar | maxiconsumo | 75.9% |
| 22 | LECHE en POLVO VITAL INFANTIL ETAPA 1 800 g |  | $47480 | $0 | $11800 | yaguar | maxiconsumo | 75.1% |
| 23 | FECULA RANCHITO MANDIOCA 1 kg |  | $2595 | $0 | $650 | yaguar | maxiconsumo | 75.0% |
| 24 | Ginebra BOLS x195cc | 7790480090303 | $0 | $2889 | $11500 | maxiconsumo | maxicarrefour | 74.9% |
| 25 | Supremitas de pollo GDS +croc x480g | 7790070036148 | $9200 | $0 | $36390 | maxiconsumo | yaguar | 74.7% |
| 26 | Flan SER vainilla x95gr | 7791337091580 | $4535 | $0 | $1150 | yaguar | maxiconsumo | 74.6% |
| 27 | Vino ESMERALDA malbec x750cc | 7794450941237 | $0 | $7025 | $1900 | maxicarrefour | maxiconsumo | 73.0% |
| 28 | PAPAS FRITAS SNACKO CLASICA 40 g |  | $1135 | $0 | $4200 | maxiconsumo | yaguar | 73.0% |
| 29 | Jugo CITRIC naranja x250ml | 7798085681445 | $0 | $1470 | $5300 | maxiconsumo | maxicarrefour | 72.3% |
| 30 | OBLEA NUGATON BLANCO 27 g |  | $1035 | $0 | $290 | yaguar | maxiconsumo | 72.0% |

... y 28 casos mas.

---

## ANALISIS 5: PRECIOS STALE (fecha_scraping > 30 dias desde 2026-06-11)
Total precios stale (>30 dias): 0
Total precios sin fecha: 1497

| Mayorista | Stale (>30 dias) | Sin fecha |
|---|---|---|
| yaguar | 0 | 925 |
| maxicarrefour | 0 | 0 |
| maxiconsumo | 0 | 572 |


---

## ANALISIS 6: ESTADISTICA GENERAL
| Metrica | Valor |
|---|---|
| Total productos | 17812 |
| Con 0 precios | 0 |
| Con 1 precio | 15254 |
| Con 2 precios | 2077 |
| Con 3 precios | 481 |
| ABC=A con 3 precios | 47 |
| Con flag precio_stale | 0 |
| % con 2+ precios comparables | 14.4% |

---

## RECOMENDACIONES EN ORDEN DE IMPACTO

### 1. CRITICO: Filtro outlier MC en actualizar_catalogo.py (23 productos)
Impacto: 23 productos donde Maxiconsumo muestra precio 2.5x+ mayor que la competencia.
Fix: antes de consolidar precios de Maxiconsumo, calcular mediana de otras fuentes. Si precio MC > 2.5x mediana, descartar.

Agregar en actualizar_catalogo.py:
```python
OUTLIER_MC_RATIO = 2.5
precios_otras = [v for k, v in precios.items() if k != "maxiconsumo" and v and v > 0]
if precios_otras and precio_mc > 0:
    mediana_otras = statistics.median(precios_otras)
    if mediana_otras > 0 and precio_mc / mediana_otras > OUTLIER_MC_RATIO:
        logging.warning(f"Outlier MC descartado: {nombre} - MC=${precio_mc:.0f} vs mediana=${mediana_otras:.0f}")
        precio_mc = 0
```

### 2. CRITICO: Ahorros > 60% - revisar en frontend y pipeline (58 productos)
Impacto: 58 productos con ahorro mostrado de >60% que casi siempre es un error.
Fix frontend en lib/data.ts: si ahorro > 60%, marcar como precio_sospechoso = true y no mostrar como "Top Bomba".
Fix pipeline: los top 30 de la lista deben revisarse manualmente. Muchos son matches incorrectos.

### 3. MEDIA: Penalizar matches de gramaje incorrecto (101 casos)
Causa: fuzzy matching conecta "500g" con "1kg" del mismo producto porque el nombre base es similar.
Fix en unificador_v2.py o actualizar_catalogo.py: penalizar 50% el score de match cuando la cantidad extraida difiere mas de 50%.

### 4. BAJA: Precios sin fecha_scraping (1497 instancias)
Fix: asegurar que cada scraper propaga fecha_scraping siempre en la fuente del producto.

---

## PATRON DE ERROR MAS FRECUENTE
Los outliers de Maxiconsumo son la causa raiz principal de precios incorrectos visibles al usuario.
La mayoria son productos donde MC captura precio de bulto (caja x12, fardo x6) mientras Yaguar/Carrefour tienen precio unitario.
Regla de negocio recomendada: si precio_mc > 2.5x mediana_otras -> descartar precio MC del catalogo.
