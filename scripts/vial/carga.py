"""Carga y validación de los datos: leer, renombrar columnas, reproyectar y reportar.

Lee tres archivos (rutas en config.py):
  red vial       data/raw/invias.geojson (o invias.zip)
  municipios     data/final/nodos_demanda.csv   (salida de 01_limpieza_rndc.R)
  matriz O-D     data/final/matriz_od.csv       (salida de 01_limpieza_rndc.R)
"""

import warnings

import pandas as pd
import geopandas as gpd

import config

warnings.filterwarnings("ignore", "GeoSeries.notna", UserWarning)

# columnas que usan limpieza.py y grafo.py (nombres internos)
COLUMNAS_INTERNAS_RED = ["id_tramo", "codigo_via", "cod_tramo", "nombre_tramo", "ruta",
                         "administrador", "superficie", "calzada", "concesion"]


def cargar_red(reporte: list) -> gpd.GeoDataFrame:
    ruta = config.ARCHIVO_RED
    red = gpd.read_file(ruta)
    if red.crs is None:
        red = red.set_crs(config.CRS_ENTRADA_RED)
        reporte.append(f"[red] El archivo no trae CRS; se asume {config.CRS_ENTRADA_RED}.")
    faltan = [c for c in config.COLUMNAS_RED if c not in red.columns]
    if faltan:
        raise KeyError(f"Columnas de COLUMNAS_RED que no están en {ruta.name}: {faltan}. "
                       f"Columnas disponibles: {list(red.columns)}")
    red = red[list(config.COLUMNAS_RED) + ["geometry"]].rename(columns=config.COLUMNAS_RED)
    reporte.append(f"[red] {len(red)} filas leídas de {ruta.name} (CRS {red.crs.to_string()}).")

    # columnas internas que el archivo no trae (INVIAS no trae 'concesion')
    for col in COLUMNAS_INTERNAS_RED:
        if col not in red.columns:
            red[col] = None
            reporte.append(f"[red] El archivo no trae '{col}'; se deja vacía.")
    # todo como texto limpio: " " (blanco) cuenta como dato faltante
    for col in COLUMNAS_INTERNAS_RED:
        if col != "id_tramo":
            red[col] = red[col].astype("string").str.strip().replace("", pd.NA)
            red[col] = red[col].astype(object).where(red[col].notna(), None)

    # tramos fuera de servicio
    if config.EXCLUIR_TRAMOS_CON_NOMBRE:
        fuera = red["nombre_tramo"].fillna("").str.contains(
            config.EXCLUIR_TRAMOS_CON_NOMBRE, case=False)
        if fuera.any():
            km = red[fuera].to_crs(config.CRS_METRICO).length.sum() / 1000
            reporte.append(f"[red] {fuera.sum()} tramos descartados por estar "
                           f"'{config.EXCLUIR_TRAMOS_CON_NOMBRE}' ({km:,.0f} km).")
            red = red[~fuera].reset_index(drop=True)
    for col in config.COLUMNAS_RED.values():
        n = red[col].isna().sum()
        if n:
            reporte.append(f"[red] {n} nulos en '{col}'.")
    return red


def _leer_municipios() -> pd.DataFrame:
    d = pd.read_csv(config.ARCHIVO_MUNICIPIOS, dtype=str)
    d = d[list(config.COLUMNAS_MUNICIPIOS)].rename(columns=config.COLUMNAS_MUNICIPIOS)
    for c in ("lon", "lat", "ton_total"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["cod_mpio"] = d["cod_mpio"].str.zfill(5)
    return d


def cargar_municipios(reporte: list) -> gpd.GeoDataFrame:
    """Las N_CIUDADES con más carga (alcance del proyecto), en coordenadas métricas."""
    d = _leer_municipios()
    malos = d["lon"].isna() | d["lat"].isna()
    if malos.any():
        reporte.append(f"[municipios] {malos.sum()} sin coordenadas válidas (se omiten).")
    d = d[~malos]
    total = d["ton_total"].sum()
    d = d.nlargest(config.N_CIUDADES, "ton_total")
    reporte.append(f"[municipios] Se conservan las {config.N_CIUDADES} ciudades con más carga: "
                   f"{100 * d['ton_total'].sum() / total:.1f} % de las toneladas (salen + llegan).")
    gdf = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d["lon"], d["lat"]), crs="EPSG:4326")
    return gdf.to_crs(config.CRS_METRICO)


def cargar_referencia_municipios() -> pd.DataFrame:
    """Todos los municipios con coordenadas; solo para nombrar los cruces del grafo de
    análisis por el municipio más cercano."""
    d = _leer_municipios().dropna(subset=["lon", "lat"])
    g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d["lon"], d["lat"]), crs="EPSG:4326")
    g = g.to_crs(config.CRS_METRICO)
    return pd.DataFrame({"nombre": g["nombre"], "x": g.geometry.x, "y": g.geometry.y})


def cargar_od(reporte: list) -> pd.DataFrame:
    """Matriz O-D limpia en R (sin autolazos, códigos de 5 dígitos que existen en DIVIPOLA,
    galones convertidos a kg). Aquí solo se renombra."""
    ruta = config.ARCHIVO_OD
    od = pd.read_csv(ruta, usecols=list(config.COLUMNAS_OD),
                     dtype={"ORIGEN": str, "DESTINO": str})
    od = od.rename(columns=config.COLUMNAS_OD)
    for c in ("cod_origen", "cod_destino"):
        od[c] = od[c].str.zfill(5)
    od = od[od["cod_origen"] != od["cod_destino"]]
    reporte.append(f"[od] {ruta.name}: {len(od)} pares O-D, {od['toneladas'].sum():,.0f} t.")
    return od
