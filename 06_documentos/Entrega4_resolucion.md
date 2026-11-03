# Entrega 4 (2026) — Localización de planta de acopio rural (AHP + SIG)

Resolución de la Entrega 4. La parte que no depende del software (AHP, consistencia, respuestas de discusión) está resuelta y verificada. La parte SIG está como guía paso a paso para ArcMap 10.4 (vía principal) con la equivalencia en QGIS.

**Parámetros obligatorios del modelo:** CRS **EPSG:32721** (UTM 21S, metros), **píxel 500 m**, todos los ráster **alineados (snap)**. Universo: territorio rural de Uruguay. Tres factores + una restricción.

---

## PARTE A — AHP (puntos 4 y 5) · RESUELTO Y VERIFICADO

### A.1 Traducción de los juicios a la escala de Saaty
Criterios: **P** = Densidad de padrones · **R** = Proximidad a rutas · **C** = Cercanía a capitales.

| Juicio de la letra | Escala de Saaty | Valor |
|---|---|---|
| P **medianamente** más importante que R | moderada | **3** |
| P **fuertemente** más importante que C | fuerte | **5** |
| R **medianamente** más importante que C | moderada | **3** |

### A.2 Matriz de comparación por pares
Diagonal = 1, reciprocidad `a_ji = 1/a_ij`:

|  | Padrones | Rutas | Capitales |
|---|---|---|---|
| **Padrones** | 1 | 3 | 5 |
| **Rutas** | 1/3 | 1 | 3 |
| **Capitales** | 1/5 | 1/3 | 1 |

### A.3 Paso 1 — Suma de columnas
| Columna | Suma |
|---|---|
| Padrones | 1 + 1/3 + 1/5 = **1,5333** |
| Rutas | 3 + 1 + 1/3 = **4,3333** |
| Capitales | 5 + 3 + 1 = **9,0000** |

### A.4 Paso 2 — Matriz normalizada (celda ÷ suma de su columna)
|  | Padrones | Rutas | Capitales |
|---|---|---|---|
| **Padrones** | 0,6522 | 0,6923 | 0,5556 |
| **Rutas** | 0,2174 | 0,2308 | 0,3333 |
| **Capitales** | 0,1304 | 0,0769 | 0,1111 |

### A.5 Paso 3 — Vector de pesos (promedio de cada fila)
```
w_Padrones  = (0,6522 + 0,6923 + 0,5556)/3 = 1,9000/3 = 0,6333  → 63,3 %
w_Rutas     = (0,2174 + 0,2308 + 0,3333)/3 = 0,7815/3 = 0,2605  → 26,1 %
w_Capitales = (0,1304 + 0,0769 + 0,1111)/3 = 0,3185/3 = 0,1062  → 10,6 %
```
**Vector de ponderación = [0,633 ; 0,261 ; 0,106]**  (Padrones, Rutas, Capitales). Suma = 1,00.

> Verificado también por **media geométrica** (exacta para n ≤ 3): [0,637 ; 0,258 ; 0,105]. Coincide con el autovector salvo redondeo.

### A.6 Paso 4 — Análisis de consistencia
1. **A·w** = [1,9456 ; 0,7901 ; 0,3197]
2. **(A·w)/w** = [3,0720 ; 3,0330 ; 3,0112]
3. **λmáx** = promedio = **3,0387**
4. **CI** = (λmáx − n)/(n − 1) = (3,0387 − 3)/2 = **0,01936**
5. **CR** = CI / RI:

| Índice aleatorio (n=3) | CR | ¿Consistente? |
|---|---|---|
| **RI = 0,58 (el del curso)** | **0,033 (3,3 %)** | **Sí (< 0,10)** |

> **RI confirmado por la presentación de clase del profesor:** su tabla de Índice Aleatorio da RI(3) = 0,58 · RI(4) = 0,90 · RI(5) = 1,12 · RI(6) = 1,24. Para n=3 → **RI = 0,58**. (El valor 0,525 de la lectura de Moreno NO se usa en este curso.)

**Conclusión:** **CR = 0,033 (3,3 %) < 0,10 → los juicios son consistentes**. El vector de pesos es válido y no requiere revisar la matriz. El método (pesos por promedio de columnas normalizadas; λmáx = promedio de (A·w)/w; IC = (λmáx−n)/(n−1); RC = IC/RI) es exactamente el del ejercicio de Saaty que el profesor resolvió en clase.

### A.7 Fórmula de combinación (punto que alimenta el ráster final)
```
Aptitud = 0,633 · F_padrones + 0,261 · F_rutas + 0,106 · F_capitales
```
con cada F_i normalizado a 0–10. El resultado queda en 0–10.

---

## PARTE B — Guía SIG paso a paso (ArcMap 10.4)

> Vía principal ArcMap 10.4; columna QGIS para la réplica. Requiere **Spatial Analyst**.

### B.0 Preparación (una sola vez)
1. **Cargar** los shapefiles: `Departamentos`, `Localidades`, `Parcelas`, `Rutas`, `Capitales`.
2. **Reproyectar todo a EPSG:32721** (*Project* / *Project Raster*). No trabajar en geográficas.
3. **Entorno de geoprocesamiento** (*Geoprocessing → Environments*), fijar para TODO el trabajo:
   - Output Coordinate System: **WGS 1984 UTM Zone 21S** (EPSG:32721).
   - **Cell Size = 500**.
   - **Extent** = extensión de Uruguay (usar `Departamentos`).
   - **Snap Raster** = el primer ráster que generes (o uno de referencia), para alinear todos.
   - Processing Extent / Mask = ver B.5.

### B.1 Zona de análisis (la restricción / recorte)
La letra pide restricción como **máscara binaria** (áreas rurales), pero el profesor **corrigió esto expresamente en el foro de la Entrega 4**: la máscara generada en clase dejaba **todas las capitales fuera** (salvo Colonia), así que recomienda **NO usar la máscara sino recortar (Clip) los ráster a la "zona de trabajo" = diferencia entre el territorio de Uruguay y las localidades**. → **Usar recorte, no máscara.** (Confirmado por el profesor, no es una opción.)

- **Zona rural = diferencia** entre el territorio (Departamentos) y las Localidades:
  `Erase` (Departamentos, Localidades) → `zona_rural` (vectorial). En QGIS: *Diferencia*.
- Esta `zona_rural` se usa como **máscara** (Environments → Mask) para todos los ráster y como recorte final.

### B.2 Factor 1 — Proximidad a rutas (0–10, invertido)
1. **Euclidean Distance** sobre `Rutas` → `dist_rutas` (celda 500, snap).  *(QGIS: `gdal:proximity`)*
2. **Normalizar lineal 0–10, invertida** (menor distancia = mayor aptitud):
   - Rescale by Function: `TfLinear`, from_scale **10**, to_scale **0**.
   - o Raster Calculator: `10 * (dist_max - "dist_rutas") / (dist_max - dist_min)`.
   → `F1_rutas`.

### B.3 Factor 2 — Densidad de padrones de mayor superficie (0–10, directo)
> **Dato verificado del `.dbf`:** `Parcelas` tiene **252.176 registros** y solo dos campos: `NOMDEPTO` y `PADRON`. **No existe campo de superficie**, hay que calcularlo desde la geometría (ArcMap: `AREA = !shape.area!`; QGIS: `$area`, en m² con CRS 32721). Distribución muy asimétrica: media **67,5 ha** (674.799 m²), mediana **13,0 ha**, tercil superior P66 **32,3 ha** (322.928 m²), máx **9.558 ha**.

1. **Calcular superficie** de `Parcelas`: `AREA = !shape.area!` (ArcMap) o campo `$area` (QGIS), en m², CRS 32721.
2. **Seleccionar las parcelas "de mayor superficie"**:
   - **Umbral elegido: tercil superior, `AREA > 322928` m² (≈ 32,3 ha).** Deja **84.059 parcelas (33,3%)**.
   - `Select by Attributes`: `AREA > 322928` → `parcelas_grandes`.
   > **Justificación del corte:** la media (67,5 ha) está muy inflada por latifundios de la cola (máx ≈ 9.558 ha) y solo deja 21,3% de las parcelas; la mediana es de apenas 13 ha. El **tercil superior (P66 ≈ 32,3 ha)** es robusto a esos extremos, reparte un tercio del padrón como "de mayor superficie" y es coherente con el uso de cuantiles que la propia consigna sugiere para otro criterio. Documentar este umbral en la entrega.
3. **Densidad** de esas parcelas grandes:
   - opción puntual: centroides (`Feature To Point`) → **Kernel Density** o **Point Density** (radio a justificar), o
   - opción areal: `Polygon to Raster` del área y **Focal Statistics** (suma en ventana) para densidad local.
   → `dens_padrones`.
4. **Normalizar lineal 0–10, directa** (mayor densidad = mayor aptitud):
   - Rescale by Function `TfLinear`, from_scale **0**, to_scale **10**, o
   - Raster Calculator: `10 * ("dens" - dmin) / (dmax - dmin)`.
   → `F2_padrones`.

### B.4 Factor 3 — Cercanía a capitales sin Montevideo (0–10, invertido)
> **Dato verificado del `.dbf`:** `Capitales` ya trae **exactamente 18 registros** y **Montevideo NO está incluido** (las 18 son las capitales del interior: Artigas, Maldonado, Colonia del Sacramento, Durazno, Trinidad, Canelones, Paysandú, Treinta y Tres, Florida, Mercedes, Rivera, Melo, Rocha, Fray Bentos, Minas, San José de Mayo, Salto, Tacuarembó). Campo de nombre: `NOMLOC` (ciudad) / `NOMDEPTO` (departamento). **No hay que filtrar nada.**

1. **Usar `Capitales` tal cual** (18 capitales, sin Montevideo). Si se quisiera verificar: `Select by Attributes` sobre `NOMDEPTO`/`NOMLOC`; no aparece Montevideo.
2. **Euclidean Distance** → `dist_capitales`.
3. **Normalizar lineal 0–10, invertida** (igual que rutas): from_scale **10**, to_scale **0** → `F3_capitales`.

### B.5 Combinación ponderada (AHP)
Con los pesos de la Parte A:
- **Raster Calculator** (o **Weighted Sum**):
  `"F1_rutas"*0.261 + "F2_padrones"*0.633 + "F3_capitales"*0.106`
  → `aptitud` (en 0–10).
- Aplicar la **máscara** `zona_rural` (Environments → Mask, o `Extract by Mask`) para que solo quede territorio rural.
  → `aptitud_rural`.

> Ojo al orden de los pesos: **Padrones 0,633 · Rutas 0,261 · Capitales 0,106**.

### B.6 Punto 6 — Identificar el ventil de mayor aptitud
Pegar el script de la letra en *Geoprocessing → Python* de ArcMap, cambiando el nombre de la capa:
```python
import arcpy, numpy as np
raster = "aptitud_rural"          # <- nombre de tu capa de aptitud
nodata = -999999999
arr = arcpy.RasterToNumPyArray(raster, nodata_to_value=nodata)
valores = arr.ravel()
valores = valores[valores != nodata]
valores = valores[np.isfinite(valores)]
if valores.size == 0:
    raise ValueError("El raster no contiene valores validos.")
p95 = np.percentile(valores, 95)
print("Cantidad de celdas: {}".format(valores.size))
print("Percentil 95: {:.4f}".format(p95))
print("Umbral del ultimo veintil: {:.4f}".format(p95))
```
Devuelve el **umbral del percentil 95**. Luego, las zonas aptas del último ventil:
- Raster Calculator: `Con("aptitud_rural" >= <p95>, 1)` → zonas del ventil superior.
- Convertir a vectorial (`Raster to Polygon`) para medir áreas y mapear.

> **Réplica QGIS del ventil** (no hay arcpy): calcular el percentil 95 con estadísticas de la capa (o `numpy` en la consola de Python de QGIS) y luego `r.mapcalc` / Calculadora ráster con `aptitud >= p95`.

---

## PARTE C — Respuestas a las preguntas de discusión (punto 7)

**1. Sets de datos y fuentes.**
Shapefiles provistos: `Rutas` (red vial nacional → Factor 1), `Parcelas` (padrones rurales, superficie gráfica → Factor 2), `Capitales` (capitales departamentales → Factor 3), `Localidades` (para definir la zona rural / recorte), `Departamentos` (límite del territorio y extensión). Fuente: datos de la cátedra (de origen nacional: catastro/DINOT/MTOP según corresponda; declarar la fuente oficial que indique el curso). Todos reproyectados a EPSG:32721.

**2. ¿Por qué no combinar los tres ráster originales antes de normalizar?**
Porque están en **unidades y rangos distintos** (metros de distancia a rutas, densidad de parcelas, metros de distancia a capitales). Sumarlos directamente haría que la variable de mayor magnitud numérica domine artificialmente el resultado, sin relación con su importancia real. La normalización a una **escala común 0–10** los hace comparables; recién entonces los pesos del AHP controlan la influencia de cada factor. (Es la lección del ejercicio 4 del módulo: un scoring sin normalizar da valores fuera de escala e ininterpretables.)

**3. Tras el análisis de consistencia, ¿a qué conclusión se llega?**
El **CR = 0,033** (RI = 0,58, el índice aleatorio del curso) está **muy por debajo de 0,10**, de modo que los juicios de comparación por pares son **consistentes**. La matriz es coherente (p. ej. como P domina a R y R domina a C, P domina a C con intensidad acorde) y el vector de pesos [0,633 ; 0,261 ; 0,106] es **válido** sin necesidad de revisar ningún juicio.

**4. Diferencia conceptual entre factor y restricción.**
Un **factor** gradúa la aptitud: aporta un valor continuo (0–10) que potencia o resta viabilidad, pero no excluye territorio. Una **restricción** es binaria (0/1): excluye del análisis las áreas que no cumplen una condición (máscara), sin graduar. Aquí los tres criterios de distancia/densidad son factores; la condición de ser territorio rural es la restricción (máscara / recorte). Factor = *cuánto de apto*; restricción = *dentro o fuera*.

**5. ¿Qué efecto tendría aumentar el peso de la proximidad a rutas?**
Subir el peso de Rutas (hoy 0,261) desplaza aptitud hacia las **cercanías de la red vial nacional**: las zonas próximas a rutas suben de puntaje y el mapa de aptitud se concentra en corredores viales. Como los pesos suman 1, ese aumento obliga a **bajar** el de Padrones y/o Capitales, restándoles influencia; el ventil superior tendería a alinearse con las rutas en vez de con las zonas de parcelas grandes. Es lo que mide un **análisis de sensibilidad**: cuánto cambia la selección al mover los pesos.

**6. Ventaja de usar terciles para la cercanía a capitales.**
Clasificar la distancia a capitales en **terciles** (tres clases: cerca / media / lejos por igual número de celdas) hace la variable **robusta a valores extremos y a la forma de la distribución**: en lugar de una rampa lineal sensible a la distancia máxima (una celda muy lejana comprime el resto de la escala), los terciles reparten el territorio en tres grupos de tamaño comparable, facilitan la interpretación (clases de accesibilidad) y evitan que outliers distorsionen la normalización. Es una estandarización por **ranking/cuantiles** en vez de por rango lineal.
En esta entrega se aplicó la **función lineal** que pide la consigna para el Factor 3; los terciles se plantean como alternativa. Aquí el efecto sería acotado: la distancia máxima a una capital es de 120 km y el factor pesa solo 0,106.

---

## Nota sobre decisiones que dependían de ver los datos — CERRADAS
Ambas se resolvieron inspeccionando los `.dbf` reales:
- **Factor 2:** `Parcelas` (252.176 registros) solo tiene `NOMDEPTO` y `PADRON`; **no hay campo de superficie**, se calcula con `$area` (CRS 32721). Umbral de "mayor superficie" fijado en el **tercil superior: `AREA > 322928` m² (≈ 32,3 ha) → 84.059 parcelas (33,3%)**. (Estadística: media 67,5 ha, mediana 13,0 ha, máx 9.558 ha.)
- **Factor 3:** `Capitales` ya trae **18 capitales sin Montevideo**; no hace falta filtrar. Campo de nombre: `NOMLOC` / `NOMDEPTO`.

---

### Resumen de resultados clave
- **Pesos AHP:** Padrones **0,633** · Rutas **0,261** · Capitales **0,106**.
- **λmáx** = 3,039 · **CI** = 0,0194 · **CR** = **0,033** (consistente).
- **Combinación:** `Aptitud = 0,633·F_padrones + 0,261·F_rutas + 0,106·F_capitales`.
- **Ventil superior:** umbral = percentil 95 de la aptitud (script arcpy del punto 6).

---

## PARTE D — Evidencia numérica del modelo ejecutado en ArcMap

Resultados reales de la ejecución (detalle paso a paso en `06_documentos\Informe_Entrega4.md`). Sirven de respaldo cuantitativo a las respuestas de la Parte C.

### D.1 Factores antes y después de normalizar (respalda la respuesta 2)
| Factor | Variable original | Rango original | Media original | Tras normalizar 0–10 (media) |
|---|---|---|---|---|
| Rutas (F1) | distancia a rutas | 0 – 95,7 km | 21,8 km | 7,72 |
| Padrones (F2) | densidad de parcelas grandes (r = 10 km) | 0 – 1,21 pts/km² | 0,47 pts/km² | 3,88 |
| Capitales (F3) | distancia a 18 capitales | 0 – 120,1 km | 52,9 km | 5,60 |

Las tres variables originales están en unidades y escalas incomparables (km, km y pts/km²). Recién tras llevarlas a 0–10 los pesos AHP gobiernan su influencia.

### D.2 Aptitud y ventil superior (puntos 5 y 6)
- `Aptitud = 0,633·F_padrones + 0,261·F_rutas + 0,106·F_capitales` → `aptitud_rural`: **1,34 a 9,52**, media **5,07**, sobre **696.517 celdas** (≈ 174.129 km²).
- **Percentil 95 = 7,5204** → ventil superior: **34.827 celdas (5,00 %) ≈ 8.707 km²**, en **189 polígonos**; los dos mayores miden 4.721 y 3.155 km².
- Reparto por departamento: Colonia 34,0 % · Lavalleja 14,8 % · San José 13,6 % · Maldonado 13,3 % · Rocha 9,5 % · Soriano 7,6 % · Florida 4,3 % · Cerro Largo 1,6 %.

### D.3 Sensibilidad al peso de Rutas (respalda la respuesta 5)
Escenario: Rutas sube de 0,261 a **0,411**; Padrones y Capitales bajan proporcionalmente a **0,505** y **0,084** (suma 1).

| | Base | Escenario |
|---|---|---|
| Umbral p95 | 7,52 | 7,84 |
| Distancia media a rutas dentro del ventil | 8,6 km | 6,4 km |
| F2 (padrones) media dentro del ventil | 7,59 | 7,43 |

- **85,9 %** de las celdas del ventil base se mantienen en el ventil del escenario: la selección es **bastante estable**.
- Pero el ventil se **acerca a la red vial** (8,6 → 6,4 km de media, contra 21,8 km del dominio completo) y gana algo menos de densidad de padrones grandes. Confirma lo planteado en la respuesta 5: más peso a rutas desplaza la aptitud hacia los corredores viales.

### D.4 Distribución de la distancia a capitales (respalda la respuesta 6)
Percentiles de `dist_capitales`: **P33 = 39,3 km · P66 = 64,2 km · P95 = 95,8 km · máx = 120,1 km** (media 52,9 km; mediana de F3 = 5,78 contra media 5,60).

Con terciles, las clases serían ≈ cerca (< 39 km), media (39–64 km) y lejos (> 64 km). Aquí la distribución es poco sesgada (media y mediana cercanas, máximo no muy alejado del P95), por lo que la rampa lineal no está muy distorsionada por extremos. La ventaja de los terciles se mantiene en general (robustez a outliers, clases interpretables), pero en este caso concreto sería **moderada**.

### D.5 Notas de método relevantes
- **Recorte, no máscara:** `EucDistance` con máscara activa ignora las fuentes fuera de ella. Con la máscara, la distancia a capitales daba un máximo de 491 km; sin máscara y recortando después, 120 km. Es lo que advirtió el profesor en el foro.
- **Script del punto 6:** el filtro `valores != nodata` no reconoce el NoData tras el redondeo float32 (contó 1.082.283 celdas, la grilla completa, y dio p95 = 7,24). Con el filtro corregido (`valores > -1e8`): 696.517 celdas y **p95 = 7,5204**.
- F2 tiene **260 celdas** (≈ 65 km²) menos que F1 y F3 (sin valor de `PointDensity`); quedan fuera de la aptitud.
