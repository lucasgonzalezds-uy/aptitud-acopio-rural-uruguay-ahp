# -*- coding: utf-8 -*-
# Mapa final de aptitud + ventil superior (Entrega 4, SIG Avanzado).
# Ejecutar con el Python 2.7 de ArcGIS 10.8 (arcpy + matplotlib 1.5.2).
# Ademas calcula el reparto del ventil superior por departamento.
from __future__ import print_function
import os
import arcpy
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap

arcpy.env.overwriteOutput = True

# Raiz del repositorio: carpeta que contiene 02_datos_originales, 03_resultados, etc.
# Si el script se pega en la ventana Python de ArcMap (sin __file__), ejecutar con
# el directorio de trabajo en la raiz del repositorio.
try:
    RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    RAIZ = os.getcwd()
DATOS = os.path.join(RAIZ, "02_datos_originales")
RAS = os.path.join(RAIZ, "03_resultados", "raster")
MAPAS = os.path.join(RAIZ, "04_mapas")
APT = os.path.join(RAS, "aptitud_rural.tif")
VEN = os.path.join(RAS, "ventil_superior.tif")
REF = os.path.join(RAS, "F1_rutas.tif")          # snap / extent de referencia
DEP = os.path.join(DATOS, "Departamentos.shp")
CAP = os.path.join(DATOS, "Capitales.shp")
PNG = os.path.join(MAPAS, "Mapa_aptitud_ventil_v2.png")
DEP_TMP = os.path.join(RAS, "_dep_tmp.tif")      # temporal, se borra al final

P95 = 7.5204          # umbral del ventil (evidencia_punto6_arcmap.txt)
PESOS = (0.633, 0.261, 0.106)

# Nombres con tildes (el .dbf viene en mayusculas y sin tildes)
NOMBRES = {
    u"PAYSANDU": u"Paysandú", u"TACUAREMBO": u"Tacuarembó",
    u"SAN JOSE DE MAYO": u"San José de Mayo", u"COLONIA DEL SACRAMENTO": u"Colonia del Sacramento",
    u"TREINTA Y TRES": u"Treinta y Tres", u"FRAY BENTOS": u"Fray Bentos",
}


def nombre(n):
    n = n.strip()
    return NOMBRES.get(n, n.title())


def fmt(x, d=2):
    return (u"{:.%df}" % d).format(x).replace(u".", u",")


print("=== PARAMETROS (antes) ===")
print("aptitud      :", APT)
print("ventil       :", VEN)
print("departamentos:", DEP)
print("capitales    :", CAP)
print("umbral P95   :", P95)
print("salida PNG   :", PNG)

# ---------------------------------------------------------------- rasters
ras = arcpy.Raster(APT)
ext = ras.extent
apt = arcpy.RasterToNumPyArray(APT, nodata_to_value=-9999).astype(float)
apt[apt < -9000] = np.nan
ven = arcpy.RasterToNumPyArray(VEN, nodata_to_value=0)
validas = np.isfinite(apt)
print("aptitud: celdas validas =", int(validas.sum()),
      "| min =", round(float(np.nanmin(apt)), 4), "| max =", round(float(np.nanmax(apt)), 4))
print("ventil : celdas =", int((ven == 1).sum()))

# ------------------------------------------- reparto del ventil por depto
arcpy.env.snapRaster = REF
arcpy.env.extent = REF
arcpy.env.cellSize = 500
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(32721)
arcpy.PolygonToRaster_conversion(DEP, "FID", DEP_TMP, "CELL_CENTER", "", 500)
dep_arr = arcpy.RasterToNumPyArray(DEP_TMP, nodata_to_value=-1)
fid_nom = dict((r[0], r[1]) for r in arcpy.da.SearchCursor(DEP, ["FID", "NOMDEPTO"]))
if dep_arr.shape != ven.shape:
    raise ValueError("Grillas no alineadas: %s vs %s" % (dep_arr.shape, ven.shape))
mask_v = ven == 1
tot_v = int(mask_v.sum())
reparto = []
for fid, nom in fid_nom.items():
    n = int((mask_v & (dep_arr == fid)).sum())
    if n:
        reparto.append((nom, n))
sin_depto = tot_v - sum(n for _, n in reparto)
reparto.sort(key=lambda t: -t[1])
print("=== Reparto del ventil por departamento ===")
for nom, n in reparto:
    print(u"  {:<20s} {:>6d} celdas  {:>7.1f} km2  {:>5.1f} %".format(nom, n, n * 0.25, 100.0 * n / tot_v))
print("  sin departamento (borde):", sin_depto)
print("  total:", tot_v)
arcpy.Delete_management(DEP_TMP)

# ---------------------------------------------------------- vectoriales
lineas_dep = []
for (shp,) in arcpy.da.SearchCursor(DEP, ["SHAPE@"]):
    for part in shp:
        anillo = []
        for p in part:
            if p is None:            # separador de anillos interiores
                if anillo:
                    lineas_dep.append(anillo)
                anillo = []
            else:
                anillo.append((p.X, p.Y))
        if anillo:
            lineas_dep.append(anillo)
caps = [(xy[0], xy[1], nombre(n)) for xy, n in arcpy.da.SearchCursor(CAP, ["SHAPE@XY", "NOMLOC"])]

# ----------------------------------------------------------------- mapa
extent_img = [ext.XMin, ext.XMax, ext.YMin, ext.YMax]
fig, ax = plt.subplots(figsize=(9.5, 10))
ax.set_axis_bgcolor("#eef3f7")

cmap = plt.cm.YlGn
cmap.set_bad(alpha=0)
im = ax.imshow(np.ma.masked_invalid(apt), cmap=cmap, vmin=0, vmax=10,
               extent=extent_img, interpolation="nearest", zorder=1)
ax.imshow(np.ma.masked_where(ven != 1, ven), cmap=ListedColormap(["#c8201e"]),
          extent=extent_img, interpolation="nearest", zorder=2)
for l in lineas_dep:
    xs, ys = zip(*l)
    ax.plot(xs, ys, color="#444444", lw=0.6, zorder=3)
for x, y, n in caps:
    ax.plot(x, y, "o", ms=5, mfc="white", mec="black", mew=1.0, zorder=5)
    ax.text(x + 6000, y + 5000, n, fontsize=7.5, zorder=6)

ax.set_xlim(ext.XMin - 10000, ext.XMax + 10000)
ax.set_ylim(ext.YMin - 25000, ext.YMax + 10000)
ax.set_xticks([])
ax.set_yticks([])

# Norte
ax.annotate("", xy=(0.93, 0.965), xytext=(0.93, 0.885), xycoords="axes fraction",
            arrowprops=dict(facecolor="black", edgecolor="black", width=5, headwidth=14))
ax.text(0.93, 0.97, "N", transform=ax.transAxes, ha="center", va="bottom",
        fontsize=14, fontweight="bold")

# Escala grafica 0-100 km (tramos de 25 km)
x0 = ext.XMax - 125000
y0 = ext.YMin - 5000
alto = 4500
for i in range(4):
    ax.add_patch(mpatches.Rectangle((x0 + i * 25000, y0), 25000, alto,
                                    facecolor="black" if i % 2 == 0 else "white",
                                    edgecolor="black", lw=0.8, zorder=7))
for km, txt in ((0, "0"), (50, "50"), (100, "100 km")):
    ax.text(x0 + km * 1000, y0 - 3500, txt, ha="center", va="top", fontsize=8, zorder=7)

# Leyenda
handles = [
    mpatches.Patch(facecolor="#c8201e", edgecolor="black",
                   label=u"Ventil superior (aptitud ≥ %s; percentil 95)" % fmt(P95, 2)),
    Line2D([], [], marker="o", ls="", mfc="white", mec="black", label=u"Capitales departamentales (sin Montevideo)"),
    Line2D([], [], color="#444444", lw=0.8, label=u"Límites departamentales"),
    mpatches.Patch(facecolor="#eef3f7", edgecolor="#999999", label=u"Fuera del análisis (localidades)"),
]
ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.95, numpoints=1)

# Barra de color (pegada al mapa)
cb = fig.colorbar(im, ax=ax, ticks=range(0, 11), shrink=0.5, pad=0.02, fraction=0.04)
cb.set_label(u"Aptitud (escala 0–10)\nrango observado %s–%s" % (fmt(float(np.nanmin(apt))), fmt(float(np.nanmax(apt)))),
             fontsize=10)

# Titulo y pie anclados al mapa (sin huecos)
ax.set_title(u"Aptitud para localización de planta de acopio rural — Uruguay\n"
             u"AHP: Padrones %s · Rutas %s · Capitales %s" % tuple(fmt(p, 3) for p in PESOS),
             fontsize=13)
ax.text(0.5, -0.02, u"WGS 84 / UTM 21S (EPSG:32721) · píxel 500 m · Datos: provistos por la cátedra · "
                    u"SIG Avanzado, Entrega 4", transform=ax.transAxes, ha="center", va="top", fontsize=8)

fig.savefig(PNG, dpi=200, bbox_inches="tight", pad_inches=0.15)
plt.close(fig)

print("=== RESULTADO (despues) ===")
print("PNG existe:", os.path.isfile(PNG), "| KB:", int(os.path.getsize(PNG) / 1024))
print("temporal borrado:", not arcpy.Exists(DEP_TMP))
