# Informe de proceso — Entrega 4 (AHP + SIG en ArcMap 10.x)

Localización de planta de acopio y distribución rural en Uruguay. Evaluación multicriterio
espacial con AHP. Registro incremental de cada proceso ejecutado en ArcMap vía el Add-In MCP
(ArcGeek Tools). Para cada proceso se deja: **parámetros antes** de ejecutar y **resultado
después** de cargar/correr.

**Parámetros obligatorios del modelo:** CRS **EPSG:32721** (UTM 21S, metros) · píxel **500 m** ·
ráster alineados (**snap**). Universo: territorio rural de Uruguay. 3 factores + 1 restricción
(aplicada como **recorte**, según corrección del foro posterior al PDF).

**Pesos AHP (Parte A, verificada):** Padrones **0,633** · Rutas **0,261** · Capitales **0,106**.
CR = 0,033 (consistente).

**Carpetas (desde el Paso 11):**
- Datos de entrada: `02_datos_originales\`
- Resultados: `03_resultados\vectoriales\` y `03_resultados\raster\`
- Mapas: `04_mapas\` · Proyecto ArcMap y script del mapa: `05_arcmap\`
- Informe: `06_documentos\Informe_Entrega4.md`

Los Pasos 00–10 conservan las rutas que se usaron al ejecutarlos (`Entrega 4\` y
`Entrega 4\salidas\`). La equivalencia con las rutas actuales está en el Paso 11.

---

## Paso 00 — Conexión con ArcMap (Add-In MCP)

**Parámetros / acción:** `ping` al Add-In ArcGeek Tools.

**Resultado:** `success — "ArcGIS ArcMap MCP Add-In is responsive!"`. Conexión establecida.

Estado del documento al conectar: `document_path = "Sin título"`, data frame activo `Layers`,
`layer_count = 0`.

---

## Paso 01 — Preparación del entorno de trabajo

**Parámetros / acción:**
- Crear carpeta de salidas: `Entrega 4\salidas\`.
- Verificar que `execute_code` (arcpy) corre como proceso **standalone** (sin `MapDocument('CURRENT')`),
  por lo que las operaciones sobre el documento activo se hacen con las tools del Add-In.
- Guardar el MXD en `Entrega 4\salidas\Entrega4.mxd`.

**Resultado:**
- Carpeta `Entrega 4\salidas\` creada (verificado, `existe out_dir = True`).
- `execute_code` confirmado como proceso aparte.
- Guardado del MXD: **pendiente de un primer `File > Save As` manual** (la tool `save_project`
  no puede nombrar el documento la primera vez). Una vez guardado como `Entrega4.mxd`, los pasos
  siguientes continúan automáticamente.

---

## Paso 02 — Carga de shapefiles y verificación de CRS

**Parámetros / acción (antes):**
- Agregar al data frame activo los 5 shapefiles desde `Entrega 4\`:
  `Rutas.shp`, `Parcelas.shp`, `Departamentos.shp`, `Capitales.shp`, `Localidades.shp`.
- Estado inicial del documento: `Entrega4.mxd`, 0 capas.

**Resultado (después):** las 5 capas se agregaron correctamente al TOC. CRS verificado leyendo
cada `.prj`:

| Capa | Geometría | Features | CRS (WKID) |
|---|---|---|---|
| Rutas | Polyline | 5.448 | WGS_1984_UTM_Zone_21S (32721) |
| Parcelas | Polygon | 252.176 | 32721 |
| Departamentos | Polygon | 20 | 32721 |
| Capitales | Point | 18 | 32721 |
| Localidades | Polygon | 652 | 32721 |

**Decisión:** todas las capas ya están en **EPSG:32721** (UTM 21S, metros). **No se reproyecta**
(el paso de reproyección de la guía queda omitido por innecesario).

**Nota técnica:** `arcpy.Describe()` sobre estos `.shp` devuelve `dataType='File'` y no resuelve
`shapeType`; por eso el CRS se lee vía `arcpy.SpatialReference(.prj)` y los conteos vía
`GetCount_management`. Las herramientas de geoprocesamiento sí aceptan la ruta al `.shp`.

## Paso 03 — Entorno de geoprocesamiento y zona rural (recorte)

**Inspección previa de `Departamentos` (20 features):** son los 19 departamentos + un polígono
**"LIMITE CONTESTADO"** (zona en disputa con Brasil). Incluye además `MONTEVIDEO` como
departamento. Campo de nombre: `NOMDEPTO`.
Extent de Uruguay: `xmin=366605,4 ymin=6121401,9 xmax=858003,8 ymax=6671733,8`
(~491 km × 550 km → grilla de ~983 × 1101 celdas a 500 m).
**Decisión:** se conserva "LIMITE CONTESTADO" como parte del territorio; Montevideo (depto.) se
mantiene porque su mancha urbana se elimina al restar `Localidades`.

**Entorno GP fijado (antes):**
- `outputCoordinateSystem = EPSG:32721`
- `cellSize = 500`
- `extent = Describe(Departamentos).extent`
- `overwriteOutput = True`
- `snapRaster`: se fijará con el primer ráster generado (Factor 1).

**Geoproceso (antes):**
- Tool: `Erase_analysis`
- `in_features = Departamentos.shp`
- `erase_features = Localidades.shp`
- `out_feature_class = salidas\zona_rural.shp`

**Resultado (después):**
- `zona_rural.shp` creado · **20 features** (un polígono por depto. con los huecos de las 652
  localidades recortados) · CRS **32721** · extent = el de Uruguay.
- Capa agregada al TOC como `zona_rural`.
- Esta capa es la **restricción por recorte** (reemplaza a la máscara binaria, según corrección
  del foro). Se usará como `Mask` del entorno y como recorte final de la aptitud.

## Paso 04 — Factor 1: Proximidad a rutas (0–10, invertido)

Requiere **Spatial Analyst** (verificado: `Available`). Este paso fija el **snap raster** de
referencia para todos los ráster posteriores.

### 04.a — Distancia euclidiana a rutas

**Parámetros (antes):**
- Tool: `EucDistance` (Euclidean Distance)
- `in_source_data = Rutas.shp`
- `cell_size = 500`
- `extent = Departamentos` · `mask = zona_rural.shp` · `outputCRS = 32721`
- `out_raster = salidas\dist_rutas.tif`

**Resultado (después):**
- `dist_rutas.tif` · grilla **983 × 1101** · celda 500 m · CRS 32721
- distancia **min = 0 m**, **max = 95.707,9 m**
- **`snapRaster` fijado = dist_rutas.tif** (alinea todos los ráster siguientes).

### 04.b — Normalización lineal invertida a 0–10

**Parámetros (antes):**
- Map Algebra: `(dmax - dist) / (dmax - dmin) * 10`  (menor distancia → mayor aptitud)
- `dmin = 0`, `dmax = 95707,89`
- `out_raster = salidas\F1_rutas.tif`
- Nota: se quitó `env.mask` en esta operación (un `.shp` no sirve como mask en Map Algebra con
  `Float()`); el ráster de entrada ya venía recortado a la zona rural, así que el recorte se
  conserva.

**Resultado (después):**
- `F1_rutas.tif` · **min = 0**, **max = 10**, **media = 7,72** · grilla 983×1101 · CRS 32721.
- Media alta porque la red vial nacional es densa: gran parte del territorio queda cerca de una
  ruta. Capa agregada al TOC.

## Paso 05 — Factor 2: Densidad de padrones de mayor superficie (0–10, directo)

### 05.a — Superficie y selección de parcelas grandes

**Parámetros (antes):**
- Copia de trabajo `salidas\parcelas_area.shp` (el original estaba con *schema lock* por estar
  cargado en el TOC; no se modifica el `.shp` original).
- Campo `AREA_M2 = !shape.area!` (m², CRS 32721).
- Selección `AREA_M2 > 322928` (tercil superior P66) → `salidas\parcelas_grandes.shp`.

**Resultado (después):**
- total parcelas = 252.176 · seleccionadas = **84.059 (33,3%)** · `parcelas_grandes.shp` creado.
- Coincide exactamente con la estadística previa del `.dbf` (tercil superior).

### 05.b — Densidad

**Parámetros (antes):**
- `FeatureToPoint` (INSIDE) → `parcelas_grandes_pt.shp` (centroides).
- `PointDensity`: `cell = 500`, vecindario **círculo r = 10.000 m (10 km)**,
  `area_unit = SQUARE_KILOMETERS` → densidad en pts/km².
- `mask = zona_rural`, `snapRaster = dist_rutas`.
- `out_raster = salidas\dens_padrones.tif`.
- **Justificación del radio:** 10 km capta la *concentración territorial* de padrones grandes a la
  escala del problema (localización regional de una planta), suavizando el ruido de parcelas
  aisladas sin diluir los núcleos de alta densidad. Documentar.

**Resultado (después):**
- 84.059 puntos generados · `dens_padrones.tif` · densidad **min 0 / max 1,210 / media 0,469**
  pts/km² · grilla 983×1101 · CRS 32721.

### 05.c — Normalización lineal directa a 0–10

**Parámetros (antes):**
- Map Algebra: `(dens - dmin) / (dmax - dmin) * 10` (mayor densidad → mayor aptitud).
- `dmin = 0`, `dmax = 1,2095776`.
- `out_raster = salidas\F2_padrones.tif`.

**Resultado (después):**
- `F2_padrones.tif` · **min 0 / max 10 / media 3,88** · grilla 983×1101 · CRS 32721. Capa al TOC.

---

## Paso 06 — Factor 3: Cercanía a capitales, sin Montevideo (0–10, invertido)

### 06.a — Distancia euclidiana a capitales

**Parámetros (antes):**
- Tool: `EucDistance` · `in_source_data = Capitales.shp` (**18 capitales del interior, sin Montevideo**; no hizo falta filtrar) · `cell_size = 500`.
- `extent = F1_rutas` · `snapRaster = F1_rutas` · **sin `mask`** en el cálculo de la distancia.
- Luego `ExtractByMask` con `F1_rutas.tif` para dejar el mismo dominio (zona rural) que los otros factores.
- `out_raster = salidas\dist_capitales.tif`.
- **Por qué sin máscara:** un primer intento con `mask` activa dio distancia máxima de 491 km (imposible para Uruguay). Con máscara, `EucDistance` descarta las fuentes que caen fuera de ella y solo contaba las capitales dentro de la zona rural. Es el mismo problema que el profesor señaló en el foro (la máscara deja las capitales afuera). Ese resultado se descartó y se recalculó: distancia sin máscara y recorte posterior.

**Resultado (después):**
- `dist_capitales.tif` · grilla 983 × 1101 · celda 500 m · CRS 32721.
- distancia **min = 0 m**, **max = 120.052,1 m**, **media = 52.857,6 m**.

### 06.b — Normalización lineal invertida a 0–10

**Parámetros (antes):**
- Map Algebra: `(dmax - dist) / (dmax - dmin) * 10` (menor distancia → mayor aptitud), igual que el Factor 1.
- `dmin = 0`, `dmax = 120052,07` (calculados sobre el dominio recortado).
- `out_raster = salidas\F3_capitales.tif`.

**Resultado (después):**
- `F3_capitales.tif` · **min = 0**, **max = 10**, **media = 5,60** · 696.777 celdas válidas (igual que F1) · grilla 983×1101 · CRS 32721. Capa al TOC.
- Se verificó que F1 se construyó con la misma fórmula sobre `dist_rutas` (diferencia máxima ≈ 1e-6).

## Paso 07 — Combinación ponderada AHP y recorte a zona rural

**Parámetros (antes):**
- Map Algebra: `F2_padrones * 0.633 + F1_rutas * 0.261 + F3_capitales * 0.106` (pesos suman 1,000) → `salidas\aptitud.tif`.
- `ExtractByMask(aptitud, zona_rural.shp)` → `salidas\aptitud_rural.tif`.
- Alineación: `snapRaster = F1_rutas`, celda 500, `extent = F1_rutas`.

**Resultado (después):**
- `aptitud_rural.tif` · **min = 1,34**, **max = 9,52**, **media = 5,07** · **696.517 celdas válidas** (≈ 174.129 km²).
- Las celdas válidas son la intersección de los tres factores. F2 tiene 260 celdas menos que F1 y F3 (696.517 contra 696.777, ≈ 65 km²): son celdas donde `PointDensity` no devolvió valor, y quedan fuera de la aptitud.
- El recorte a `zona_rural` no eliminó celdas, porque los tres factores ya venían recortados. Capa al TOC.

## Paso 08 — Ventil superior de aptitud (percentil 95)

**Parámetros (antes):**
- Script de la letra sobre `aptitud_rural.tif` con una corrección en el filtro de NoData: `valores = valores[valores > -1e8]` en lugar de `valores != nodata`.
- **Motivo de la corrección:** `-999999999` se redondea en float32 y el filtro original no lo reconoce. Con el filtro original contó 1.082.283 celdas (la grilla completa 983 × 1101) y dio un percentil 95 de 7,24. Ese valor es incorrecto porque incluye las celdas sin dato.
- Zonas aptas: `Con(aptitud_rural >= p95, 1)` → `salidas\ventil_superior.tif`; `RasterToPolygon` → `salidas\ventil_superior_pol.shp`.

**Resultado (después):**
- Celdas válidas = **696.517** · **percentil 95 = 7,5204** (umbral del último veintil).
- `ventil_superior.tif`: **34.827 celdas (5,00 % de las válidas) ≈ 8.707 km²**.
- `ventil_superior_pol.shp`: **189 polígonos**; los dos mayores miden 4.721 y 3.155 km².
- Reparto del ventil por departamento (completo, recalculado en el Paso 09; suma 34.827 celdas):

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
- Capas al TOC: `aptitud_rural`, `ventil_superior`.

---

## Paso 09 — Mapa final de aptitud y ventil superior (v2)

**Parámetros (antes):**
- Script reproducible: `salidas\mapa_aptitud_ventil.py` (Python 2.7 de ArcGIS 10.8, arcpy +
  matplotlib 1.5.2), ejecutado vía Add-In MCP.
- Entradas: `aptitud_rural.tif`, `ventil_superior.tif`, `Departamentos.shp`, `Capitales.shp`.
- Umbral del ventil: P95 = 7,5204. Rampa `YlGn` con escala fija **0–10**.
- Reparto por departamento: `PolygonToRaster(Departamentos, FID)` alineado a `F1_rutas`
  (celda 500, snap), cruzado con el ventil. El ráster temporal `_dep_tmp.tif` se borra al final.
- Salida: `salidas\Mapa_aptitud_ventil_v2.png` (se conserva el mapa anterior
  `Mapa_aptitud_ventil.png`).

**Correcciones respecto al mapa anterior:**
- Etiqueta de la barra: decía "Aptitud (1–10)"; ahora dice **"Aptitud (escala 0–10)"** e indica
  el rango observado **1,34–9,52**. Ninguna celda llega a 0 porque ninguna es la peor en los tres
  factores a la vez.
- Se agregaron **flecha de norte** y **escala gráfica** (0–50–100 km).
- Nombres de capitales con tildes (Paysandú, Tacuarembó, San José de Mayo).
- Leyenda con la clase "Fuera del análisis (localidades)" y sin márgenes vacíos.

**Resultado (después):**
- `Mapa_aptitud_ventil_v2.png` · 1641 × 1779 px · 200 dpi.
- Celdas válidas 696.517 · aptitud min 1,3399 / max 9,5153 · ventil 34.827 celdas, todas
  asignadas a un departamento (0 sin departamento).
- La mancha del ventil al sur de Durazno cae en **Florida**, no en Durazno (Durazno no aporta
  celdas al ventil).

---

## Paso 10 — Ajuste de las respuestas de discusión (Parte C)

- Respuesta 3: se quitó la mención "0,037 con el ICA de Moreno"; queda solo el RI = 0,58 del curso.
- Respuesta 6: se aclaró que en la entrega se usó la función lineal de la consigna y que los
  terciles son una alternativa.
- Límite del foro: máximo **300 palabras** por respuesta (verificado en el Paso 10).

## Paso 11 — Reorganización de carpetas

**Parámetros (antes):**
- ArcMap cerrado y sin archivos de bloqueo (`.lock`).
- Inventario previo de los 3 `.mxd`: 33 capas, ninguna rota.
- Se conservaron los intermedios `parcelas_area` y `parcelas_grandes`.

**Equivalencia de rutas:**

| Antes | Ahora |
|---|---|
| `Entrega 4.pdf` | `00_consigna\` |
| `*_apuntes.md`, `Clase_ejercicio_AHP_Saaty.md`, `Tema4_ejercicios_*.md` | `01_apuntes\` |
| `Entrega 4\*.shp` (5 capas originales) | `02_datos_originales\` |
| `Entrega 4\salidas\*.shp` | `03_resultados\vectoriales\` |
| `Entrega 4\salidas\*.tif` | `03_resultados\raster\` |
| `Entrega 4\salidas\Mapa_aptitud_ventil_v2.png` | `04_mapas\` |
| Mapas anteriores | `04_mapas\anteriores\` |
| `Entrega4.mxd`, `Entrega4_presentacion.mxd`, `mapa_aptitud_ventil.py` | `05_arcmap\` |
| Resolución, procedimiento, informe, auditoría, evidencia del punto 6 | `06_documentos\` |
| Respaldos `.md` y `Entrega4_backup_antes_presentacion.mxd` | `_respaldos\` |

**Resultado (después):**
- Las 33 capas de los 3 `.mxd` se re-enlazaron a las rutas nuevas con `replaceDataSource`, y los
  documentos se guardaron con **rutas relativas**. Al reabrirlos: 0 capas rotas.
- `mapa_aptitud_ventil.py` se actualizó a las rutas nuevas.
- Se actualizaron los punteros a archivos en la resolución, el procedimiento y la auditoría.
- `evidencia_punto6_arcmap.txt` no se modificó: es el registro de la ejecución original.
