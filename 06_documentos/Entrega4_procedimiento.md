# Entrega 4 — Procedimiento y resultados

Localización de una planta de acopio y distribución rural en Uruguay mediante evaluación
multicriterio con AHP. Software: ArcMap 10.8 con Spatial Analyst.

**Condiciones del modelo:** sistema de coordenadas WGS 84 / UTM 21S (EPSG:32721), tamaño de
píxel 500 m y todos los ráster alineados al mismo snap raster.

---

## 1. Datos de entrada

Se cargaron los cinco shapefiles provistos por la cátedra. Todos ya estaban en EPSG:32721, así
que no fue necesario reproyectar.

| Capa | Geometría | Elementos | Uso en el modelo |
|---|---|---|---|
| Rutas | Línea | 5.448 | Factor 1 |
| Parcelas | Polígono | 252.176 | Factor 2 |
| Capitales | Punto | 18 | Factor 3 (ya sin Montevideo) |
| Localidades | Polígono | 652 | Zona de trabajo |
| Departamentos | Polígono | 20 | Zona de trabajo y extensión |

`Departamentos` tiene 20 elementos: los 19 departamentos y el polígono "LIMITE CONTESTADO". Se
conservó como parte del territorio.

---

## 2. Entorno de geoprocesamiento

**Geoprocessing → Environments**

| Parámetro | Valor |
|---|---|
| Output Coordinate System | WGS_1984_UTM_Zone_21S (32721) |
| Processing Extent | Igual a `Departamentos`: X 366.605,4–858.003,8 · Y 6.121.401,9–6.671.733,8 |
| Cell Size | 500 |
| Snap Raster | `dist_rutas` (desde el paso 4) |

**Resultado:** grilla de 983 columnas × 1101 filas para todo el país.

---

## 3. Zona de trabajo (restricción)

Siguiendo la indicación del foro, la restricción se aplicó **recortando** los ráster a la zona
de trabajo, sin usar la máscara de clase.

**ArcToolbox → Analysis Tools → Overlay → Erase**

| Parámetro | Valor |
|---|---|
| Input Features | `Departamentos` |
| Erase Features | `Localidades` |
| Output | `zona_rural.shp` |

**Resultado:** `zona_rural`, con 20 polígonos: el territorio nacional sin las 652 localidades.

---

## 4. Factor 1 — Proximidad a rutas nacionales

### 4.1 Distancia a rutas

**ArcToolbox → Spatial Analyst Tools → Distance → Euclidean Distance**

| Parámetro | Valor |
|---|---|
| Input feature source data | `Rutas` |
| Output cell size | 500 |
| Mask (Environments) | `zona_rural` |
| Output | `dist_rutas.tif` |

**Resultado:** distancia mínima 0 m y máxima 95.707,89 m. Este ráster queda como snap raster
para el resto del trabajo.

### 4.2 Normalización lineal 0–10 (menor distancia = mayor aptitud)

**ArcToolbox → Spatial Analyst Tools → Map Algebra → Raster Calculator**

Fórmula: F1 = (dist_máx − dist) / (dist_máx − dist_mín) × 10

```
(95707.89 - "dist_rutas") / (95707.89 - 0) * 10
```

**Resultado:** `F1_rutas.tif` · mínimo 0 · máximo 10 · media 7,72.

---

## 5. Factor 2 — Densidad de padrones rurales de mayor superficie

### 5.1 Superficie de cada parcela

1. **Data Management Tools → Features → Copy Features**: `Parcelas` → `parcelas_area.shp`.
2. **Add Field**: `AREA_M2`, tipo Double.
3. **Field Calculator** sobre `AREA_M2`: `!shape.area!` (m²).

**Resultado (estadística de `AREA_M2`):**

| Estadístico | m² | ha |
|---|---|---|
| Media | 674.799 | 67,5 |
| Mediana | 129.705 | 13,0 |
| Percentil 66 (tercil superior) | 322.928 | 32,3 |
| Máximo | 95.584.896 | 9.558,5 |

La media está inflada por pocas parcelas muy grandes: supera a la mediana unas cinco veces. Por
eso se tomó como "de mayor superficie" al **tercil superior** de la superficie.

### 5.2 Selección de las parcelas de mayor superficie

**Selection → Select By Attributes** sobre `parcelas_area`:

```
"AREA_M2" > 322928
```

Luego **Copy Features** de la selección → `parcelas_grandes.shp`.

**Resultado:** 84.059 parcelas seleccionadas (33,3 % de 252.176).

### 5.3 Centroides

**Data Management Tools → Features → Feature To Point** (opción *Inside*):
`parcelas_grandes` → `parcelas_grandes_pt.shp`.

**Resultado:** 84.059 puntos.

### 5.4 Densidad

**ArcToolbox → Spatial Analyst Tools → Density → Point Density**

| Parámetro | Valor |
|---|---|
| Input point features | `parcelas_grandes_pt` |
| Population field | NONE |
| Output cell size | 500 |
| Neighborhood | Circle, radio 10.000 m |
| Area units | Square kilometers |
| Mask (Environments) | `zona_rural` |
| Output | `dens_padrones.tif` |

**Resultado:** densidad mínima 0, máxima 1,2096 y media 0,469 padrones grandes por km².

### 5.5 Normalización lineal 0–10 (mayor densidad = mayor aptitud)

**Raster Calculator**

Fórmula: F2 = (dens − dens_mín) / (dens_máx − dens_mín) × 10

```
("dens_padrones" - 0) / (1.2095776 - 0) * 10
```

**Resultado:** `F2_padrones.tif` · mínimo 0 · máximo 10 · media 3,88.

---

## 6. Factor 3 — Cercanía a capitales departamentales (sin Montevideo)

La capa `Capitales` ya contiene las 18 capitales del interior, así que no hubo que filtrar.

### 6.1 Distancia a capitales

**Euclidean Distance**, **sin máscara** (con máscara se descartan las capitales que caen dentro
de las localidades recortadas):

| Parámetro | Valor |
|---|---|
| Input feature source data | `Capitales` |
| Output cell size | 500 |
| Output | distancia en todo el país |

Luego **Spatial Analyst Tools → Extraction → Extract by Mask**, con `F1_rutas` como máscara, para
dejar la misma zona de trabajo → `dist_capitales.tif`.

**Resultado:** distancia mínima 0 m, máxima 120.052,07 m y media 52.857,6 m.

### 6.2 Normalización lineal 0–10 (menor distancia = mayor aptitud)

**Patrón de normalización lineal invertida (como F1, porque menor distancia = mayor aptitud):**

- F1 = (distancia_máx − distancia) / (distancia_máx − distancia_mín) × 10
- F3 = (dist_capitales_máx − dist_capitales) / (dist_capitales_máx − dist_capitales_mín) × 10

**Raster Calculator**

```
(120052.07 - "dist_capitales") / (120052.07 - 0) * 10
```

**Resultado:** `F3_capitales.tif` · mínimo 0 · máximo 10 · media 5,60.

---

## 7. Pesos de los factores (AHP)

### 7.1 Juicios de la consigna en escala de Saaty

| Juicio | Intensidad | Valor |
|---|---|---|
| Padrones medianamente más importante que Rutas | Moderada | 3 |
| Padrones fuertemente más importante que Capitales | Fuerte | 5 |
| Rutas medianamente más importante que Capitales | Moderada | 3 |

### 7.2 Matriz de comparación por pares

|  | Padrones | Rutas | Capitales |
|---|---|---|---|
| Padrones | 1 | 3 | 5 |
| Rutas | 1/3 | 1 | 3 |
| Capitales | 1/5 | 1/3 | 1 |
| **Suma** | **1,5333** | **4,3333** | **9,0000** |

### 7.3 Matriz normalizada (cada celda dividida por la suma de su columna) y pesos

|  | Padrones | Rutas | Capitales | Promedio de la fila = peso |
|---|---|---|---|---|
| Padrones | 0,6522 | 0,6923 | 0,5556 | **0,633** |
| Rutas | 0,2174 | 0,2308 | 0,3333 | **0,261** |
| Capitales | 0,1304 | 0,0769 | 0,1111 | **0,106** |

Los pesos suman 1,000.

### 7.4 Consistencia

| Paso | Cálculo | Resultado |
|---|---|---|
| A · w | matriz × vector de pesos | [1,9456 ; 0,7901 ; 0,3197] |
| (A · w) / w | división elemento a elemento | [3,0720 ; 3,0330 ; 3,0112] |
| λmáx | promedio | 3,0387 |
| IC | (λmáx − n) / (n − 1) = (3,0387 − 3) / 2 | 0,0194 |
| RC | IC / RI = 0,0194 / 0,58 | **0,033** |

**Resultado:** RC = 0,033 < 0,10, así que los juicios son consistentes y el vector de pesos es
válido.

---

## 8. Combinación ponderada

**Raster Calculator**

```
"F2_padrones" * 0.633 + "F1_rutas" * 0.261 + "F3_capitales" * 0.106
```

→ `aptitud.tif`

Luego **Extract by Mask** con `zona_rural` → `aptitud_rural.tif`.

**Resultado:**

| Estadístico | Valor |
|---|---|
| Celdas con valor | 696.517 (≈ 174.129 km²) |
| Mínimo | 1,34 |
| Máximo | 9,52 |
| Media | 5,07 |

---

## 9. Zona de mayor aptitud (último ventil)

### 9.1 Umbral del percentil 95

Script de la consigna en **Geoprocessing → Python**, con `raster = "aptitud_rural"`.

| Variante | Celdas | Percentil 95 |
|---|---|---|
| Script tal cual la consigna | 1.082.283 | 7,2421 |
| Script con filtro de NoData corregido | **696.517** | **7,5204** |

El script original cuenta 1.082.283 celdas, que es la grilla completa (983 × 1101). En un ráster
float32, el valor `-999999999` se guarda como `-1000000000`, así que la línea
`valores != nodata` no elimina las celdas sin dato. Se corrigió el filtro con
`valores = valores[valores > -1e8]`, que deja las 696.517 celdas reales.

**Umbral adoptado: aptitud ≥ 7,5204.**

### 9.2 Zonas del último ventil

1. **Spatial Analyst Tools → Conditional → Con**: `Con("aptitud_rural" >= 7.5204, 1)` →
   `ventil_superior.tif`.
2. **Conversion Tools → From Raster → Raster to Polygon** → `ventil_superior_pol.shp`.

**Resultado:**
- 34.827 celdas (5,0 % de 696.517) · 34.827 × 0,25 km² ≈ **8.707 km²**.
- 189 polígonos. Los dos mayores miden 4.721 km² y 3.155 km².

### 9.3 Reparto del último ventil por departamento

| Departamento | Celdas | km² | % |
|---|---|---|---|
| Colonia | 11.846 | 2.961,5 | 34,0 |
| Lavalleja | 5.150 | 1.287,5 | 14,8 |
| San José | 4.728 | 1.182,0 | 13,6 |
| Maldonado | 4.631 | 1.157,8 | 13,3 |
| Rocha | 3.300 | 825,0 | 9,5 |
| Soriano | 2.651 | 662,8 | 7,6 |
| Florida | 1.509 | 377,2 | 4,3 |
| Cerro Largo | 548 | 137,0 | 1,6 |
| Treinta y Tres | 338 | 84,5 | 1,0 |
| Rivera | 96 | 24,0 | 0,3 |
| Flores | 17 | 4,2 | < 0,1 |
| Canelones | 12 | 3,0 | < 0,1 |
| Río Negro | 1 | 0,2 | < 0,1 |
| **Total** | **34.827** | **8.706,8** | **100** |

---

## 10. Resultado final

Las zonas más aptas se concentran en el sur del país, en dos núcleos:

- **Suroeste:** corredor Colonia – San José – sur de Soriano. Reúne el 55 % del último ventil.
- **Sureste:** Lavalleja – Maldonado – Rocha, alrededor de Minas y Rocha. Reúne el 38 %.

Hay núcleos menores en Florida, Cerro Largo (cerca de Melo), Treinta y Tres y Rivera.

El patrón sigue al Factor 2, que tiene el peso mayor (0,633). Este factor cuenta cuántos padrones
de más de 32,3 ha hay por km², por lo que favorece al sur, con muchos padrones medianos y
grandes, frente al norte, donde los padrones son más extensos pero hay menos por km².

Mapa: `04_mapas\Mapa_aptitud_ventil_v2.png`.
