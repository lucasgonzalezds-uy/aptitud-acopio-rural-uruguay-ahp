# Auditoría de resultados — Entrega 4 (verificado contra los archivos reales)

Registro de verificación de los números de `Entrega4_resolucion.md` contra los archivos de salida efectivamente generados. Todos los valores se reprodujeron de forma independiente (lectura directa de `.tif`/`.shp` y ejecución del script del punto 6 dentro de ArcMap).

---

## 1. Pesos AHP y consistencia

Método: promedio de columnas normalizadas (Saaty), escala de juicios 3 / 5 / 3.

| Elemento | Valor declarado | Verificación |
|---|---|---|
| Matriz de comparación por pares | P>R=3, P>C=5, R>C=3 | Consistente con los juicios de la letra |
| Vector de pesos | [0,633 · 0,261 · 0,106] | Suma 1,000 |
| λmáx | 3,0387 | Recalculado desde `A·w` |
| CI | 0,01936 | (λmáx − 3) / 2 |
| CR (RI = 0,58) | **0,033** | < 0,10 → juicios consistentes |

---

## 2. Factores ráster (estadística de la grilla completa)

| Archivo | Celdas válidas | Mín | Máx | Media |
|---|---|---|---|---|
| `dist_rutas.tif` | 696.777 | 0,000 | 95.707,891 | 21.779,611 m |
| `dist_capitales.tif` | 696.777 | 0,000 | 120.052,070 | 52.857,602 m |
| `dens_padrones.tif` | 696.517 | 0,000 | 1,210 | 0,469 |
| `F1_rutas.tif` | 696.777 | 0,000 | 10,000 | **7,724** |
| `F2_padrones.tif` | 696.517 | 0,000 | 10,000 | **3,879** |
| `F3_capitales.tif` | 696.777 | 0,000 | 10,000 | **5,597** |

> Coincide con la Parte D.1 de la resolución (7,72 / 3,88 / 5,60).
> Todos: celda **500 m**, EPSG:32721, 983 × 1101.

---

## 3. Ráster de aptitud y ventil superior

| Dato | Declarado | Verificado |
|---|---|---|
| Celdas válidas de `aptitud_rural.tif` | 696.517 | **696.517** |
| Mín / Máx / Media | 1,34 / 9,52 / 5,07 | **1,340 / 9,515 / 5,065** |
| Percentil 95 | 7,5204 | **7,5204** |
| Celdas del ventil superior (≥ p95) | 34.827 | **34.827** (5,00 % de 696.517) |
| Área del ventil (30 ha/celda) | ≈ 8.707 km² | **8.706,75 km²** |
| Polígonos de `ventil_superior_pol.shp` | 189 | **189** |
| Dos mayores polígonos | 4.721 / 3.155 km² | **4.721 / 3.155 km²** |

---

## 4. Reparto departamental del ventil superior

Intersección de `ventil_superior_pol.shp` con `zona_rural.shp` (ambos EPSG:32721).

| Departamento | Área (km²) | % |
|---|---|---|
| Colonia | 2.957,50 | 34,0 |
| Lavalleja | 1.286,99 | 14,8 |
| San José | 1.181,04 | 13,6 |
| Maldonado | 1.156,63 | 13,3 |
| Rocha | 824,54 | 9,5 |
| Soriano | 662,73 | 7,6 |
| Florida | 376,45 | 4,3 |
| Cerro Largo | 137,00 | 1,6 |
| Treinta y Tres | 84,50 | 1,0 |
| Rivera | 24,00 | 0,3 |
| Resto (Flores, Canelones, Río Negro) | 7,35 | 0,1 |
| **Total intersectado** | **8.698,7** | 100 |

> Coincide con la Parte D.3 de la resolución (Colonia 34,0 · Lavalleja 14,8 · San José 13,6 · Maldonado 13,3 · Rocha 9,5 · Soriano 7,6 · Florida 4,3 · Cerro Largo 1,6).

---

## 5. Punto 6 — Script ejecutado dentro de ArcMap (evidencia)

Ejecutado con el intérprete arcpy de ArcGIS Desktop 10.8 (**Python 2.7.16**, arcpy 10.8), no en QGIS.

| Variante | Celdas contadas | Percentil 95 | Observación |
|---|---|---|---|
| Script de la letra (`valores != nodata`) | 1.082.283 | **7,2421** | El filtro `!= nodata` no descarta el NoData float32 (−3,40282e+38); sobrecuenta la grilla completa (983×1101). |
| Filtro corregido (`valores > -1e8`) | 696.517 | **7,5204** | Descarta el NoData correctamente. **Variante válida.** |

Además, con el umbral corregido el conteo de celdas ≥ p95 da **34.827**, exactamente el área del ventil superior registrado.

**Conclusión:** el número reportado en la resolución (**p95 = 7,5204**) es el correcto; el script de la letra, copiado literal, produce 7,2421 por el problema de NoData. Ver `06_documentos/evidencia_punto6_arcmap.txt`.

---

## 6. Confirmación de datos de entrada (vía add-in ArcGeek MCP en ArcMap)

| Capa | Geometría | Observación |
|---|---|---|
| `Parcelas` | polígono | Solo `NOMDEPTO` y `PADRON`; no trae `AREA` (superficie se calcula desde la geometría). |
| `Capitales` | punto | Trae las 18 capitales departamentales sin Montevideo; campos `NOMLOC`, `NOMDEPTO`. |
| `Rutas` | línea | `categoria` incluye `CORREDOR INTERNACIONAL`; `numero`, `jurisdicci` (NACIONAL). |
| `zona_rural` | polígono | Diferencia `Departamentos` − `Localidades` (20 features). |
| `ventil_superior` | polígono | `gridcode = 1`; corresponde a las celdas ≥ p95. |

---

## 7. Conclusión

Los resultados de la Parte A y de la Parte D de `Entrega4_resolucion.md` se **reproducen exactamente** a partir de los archivos generados. No se encontraron discrepancias salvo el conocido problema del NoData en el script del punto 6, ya documentado y corregido en la resolución.
