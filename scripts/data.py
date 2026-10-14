"""
Exploración inicial de datos -- Proyecto Vulnerabilidad Red Vial Primaria
Correr POR BLOQUES en Spyder (cada "# %%" es una celda: Ctrl+Enter).

Objetivo: no es limpiar todavía, es DIAGNOSTICAR qué tienen y qué les falta
para construir: (1) el grafo, (2) la matriz O-D, (3) el peso de costo
económico y (4) la simulación de cierres.
"""

# %% 0. Configuración -- ajusten rutas. Los nombres de columnas se llenan
#       DESPUÉS de ver la salida del bloque 1.
import pandas as pd
import geopandas as gpd
from collections import Counter

RUTAS_RNDC = ["data/raw/base1.csv", "data/raw/base2.csv"]   # el RNDC viene partido en dos
RUTA_DIVIPOLA = "data/raw/divipola.csv"
RUTA_INVIAS = "data/raw/invias.geojson"      # o .geojson / .gpkg

# dtype=str a propósito: los códigos DANE empiezan con 0 (05001 = Medellín)
# y pandas los convertiría en 5001 si los lee como número.
partes = [pd.read_csv(r, dtype=str, low_memory=False) for r in RUTAS_RNDC]

# Antes de apilar: ¿las dos partes tienen exactamente las mismas columnas?
# Si una tiene un nombre distinto o un orden distinto, concat crea columnas
# duplicadas llenas de NaN sin avisar.
print("Filas por parte:", [len(p) for p in partes], "(límite Excel = 1,048,576)")
print("Columnas idénticas:", list(partes[0].columns) == list(partes[1].columns))
print("Solo en base1:", set(partes[0].columns) - set(partes[1].columns))
print("Solo en base2:", set(partes[1].columns) - set(partes[0].columns))

# 'parte' guarda de qué archivo viene cada fila, útil si algo no cuadra
rndc = pd.concat(partes, keys=[1, 2], names=["parte", "fila"]).reset_index(level=0)

# ¿Hay filas repetidas en ambos archivos? (pasa si el corte se solapó)
dup = rndc.drop(columns="parte").duplicated(keep=False)
print(f"Filas idénticas repetidas: {dup.sum():,} "
      f"(de ellas, entre archivos distintos: "
      f"{rndc[dup].groupby(list(rndc.columns.drop('parte')), dropna=False)['parte'].nunique().gt(1).sum():,})")

div = pd.read_csv(RUTA_DIVIPOLA, dtype=str)
red = gpd.read_file(RUTA_INVIAS)


# %% 1. Primer vistazo: forma, columnas, ejemplos
for nombre, df in [("RNDC", rndc), ("DIVIPOLA", div), ("INVIAS", red)]:
    print(f"\n===== {nombre}: {df.shape[0]:,} filas x {df.shape[1]} columnas =====")
    print(df.head(3).T)
    print("\nNulos por columna:\n", df.isna().sum()[df.isna().sum() > 0])


# %% 2. RNDC -- llenen con los nombres reales de columnas
C_ORIG = "COLUMNA_MUNICIPIO_ORIGEN"
C_DEST = "COLUMNA_MUNICIPIO_DESTINO"
C_TON = "COLUMNA_TONELADAS"
C_VIAJES = "COLUMNA_VIAJES"
C_KM = "COLUMNA_KILOMETROS"
C_FLETE = "COLUMNA_VALOR_PAGADO"

for c in [C_TON, C_VIAJES, C_KM, C_FLETE]:
    antes = rndc[c].notna().sum()
    rndc[c] = pd.to_numeric(rndc[c], errors="coerce")
    print(f"{c}: {antes - rndc[c].notna().sum():,} valores no numéricos")

# 2a. ¿La base está completa? Filas totales tras apilar
#     (el chequeo por archivo contra el límite de Excel está en el bloque 0)
print(f"\nFilas totales apiladas: {len(rndc):,}")

# 2b. Totales contra las cifras que citan en la entrega 1
print(f"Toneladas totales: {rndc[C_TON].sum():,.0f}  (citado: 85,7 millones)")
print(f"Viajes totales:    {rndc[C_VIAJES].sum():,.0f}  (citado: ~6 millones)")

# 2c. Formato de códigos
for c in [C_ORIG, C_DEST]:
    print(f"\nLongitud de códigos en {c}:\n", rndc[c].str.len().value_counts())

# 2d. Viajes intramunicipales (origen = destino): no usan la red primaria
intra = rndc[C_ORIG] == rndc[C_DEST]
print(f"\nIntramunicipal: {intra.mean():.1%} de filas, "
      f"{rndc.loc[intra, C_TON].sum() / rndc[C_TON].sum():.1%} de toneladas")

# 2e. Costo observado por tonelada-km: insumo candidato para el peso
rndc["cop_ton_km"] = rndc[C_FLETE] / (rndc[C_TON] * rndc[C_KM])
print("\nCOP por ton-km (sin intramunicipales):")
print(rndc.loc[~intra, "cop_ton_km"].describe(percentiles=[.01, .25, .5, .75, .99]))

# 2f. Pareto de pares O-D: ¿cuántos pares explican el 80 % de la carga?
od = (rndc[~intra].groupby([C_ORIG, C_DEST])[C_TON].sum()
      .sort_values(ascending=False))
acum = od.cumsum() / od.sum()
print(f"\nPares O-D distintos: {len(od):,}")
print(f"Pares para el 80 % de toneladas: {(acum <= 0.80).sum() + 1:,}")


# %% 3. DIVIPOLA -- llenen nombres
D_COD = "COLUMNA_CODIGO_MUNICIPIO"
D_LAT = "COLUMNA_LATITUD"
D_LON = "COLUMNA_LONGITUD"

for c in [D_LAT, D_LON]:
    div[c] = pd.to_numeric(div[c].str.replace(",", "."), errors="coerce")
print("Códigos duplicados:", div[D_COD].duplicated().sum())
print("Fuera de Colombia:",
      (~div[D_LAT].between(-4.3, 13.6) | ~div[D_LON].between(-82, -66.8)).sum())

# 3a. Cruce RNDC -> DIVIPOLA: ¿qué municipios de la carga no puedo ubicar?
cods = set(div[D_COD])
for c in [C_ORIG, C_DEST]:
    falta = ~rndc[c].isin(cods)
    print(f"\n{c} sin match: {rndc.loc[falta, c].nunique()} códigos, "
          f"{rndc.loc[falta, C_TON].sum() / rndc[C_TON].sum():.2%} de toneladas")
    print(rndc.loc[falta, c].value_counts().head(10))


# %% 4. INVIAS -- geometría y atributos
print("CRS original:", red.crs)
red = red.to_crs(9377)            # MAGNA-SIRGAS Origen Nacional, en metros
red = red.explode(index_parts=False).reset_index(drop=True)
print(red.geom_type.value_counts())
red["long_km"] = red.length / 1000
print(f"Tramos: {len(red):,}  |  Longitud total: {red['long_km'].sum():,.0f} km")

# Atributos categóricos: ¿qué información trae cada tramo?
for c in red.columns:
    if c != "geometry" and red[c].dtype == object and red[c].nunique() < 30:
        print(f"\n{c}:\n", red[c].value_counts(dropna=False))


# %% 5. INVIAS -- ¿los tramos realmente se tocan? (topología)
# Un grafo se arma uniendo extremos de tramos. Si dos tramos "casi" se tocan
# (quedan a 20 m), sin corrección serían dos componentes distintas.
ext = []
for g in red.geometry:
    xy = list(g.coords)
    ext += [xy[0][:2], xy[-1][:2]]
grado = Counter((round(x), round(y)) for x, y in ext)   # redondeo a 1 m
print(f"Nodos (extremos únicos): {len(grado):,}")
print("Distribución de grado:", sorted(Counter(grado.values()).items()))

g1 = gpd.GeoDataFrame(geometry=gpd.points_from_xy(
    [p[0] for p, v in grado.items() if v == 1],
    [p[1] for p, v in grado.items() if v == 1]), crs=9377)
todos = gpd.GeoDataFrame(geometry=gpd.points_from_xy(
    [p[0] for p in grado], [p[1] for p in grado]), crs=9377)
cerca = gpd.sjoin_nearest(g1, todos, max_distance=200, distance_col="d",
                          exclusive=True)
print(f"\nNodos de grado 1: {len(g1):,}")
print(f"...de ellos, con otro extremo a menos de 200 m: {cerca.index.nunique():,}")
print(cerca["d"].describe())


# %% 6. Cruce municipios <-> red: ¿qué tan lejos está la carga de la red?
mun = gpd.GeoDataFrame(div, geometry=gpd.points_from_xy(div[D_LON], div[D_LAT]),
                       crs=4326).to_crs(9377)
mun = gpd.sjoin_nearest(mun, red[["geometry"]], distance_col="dist_red_m")
mun = mun.drop_duplicates(D_COD)

ton_orig = rndc[~intra].groupby(C_ORIG)[C_TON].sum()
mun["ton_origen"] = mun[D_COD].map(ton_orig).fillna(0)
for umbral in [5, 20, 50]:
    lejos = mun["dist_red_m"] > umbral * 1000
    print(f"> {umbral} km de la red primaria: {lejos.sum()} municipios, "
          f"{mun.loc[lejos, 'ton_origen'].sum() / mun['ton_origen'].sum():.1%} "
          f"de toneladas despachadas")