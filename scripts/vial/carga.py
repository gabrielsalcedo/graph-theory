"""
Lectura de los datos de entrada.

  leer_red()          red vial de INVIAS (une las 11 partes de data/raw/invias/)
  leer_municipios()   un punto por municipio con sus toneladas (salida de R)
  leer_od()           matriz origen-destino entre municipios (salida de R)
"""

import geopandas as gpd
import pandas as pd

import config as c
from vial.reporte import anotar


def leer_red(reportar=True):
    """Une las partes de la red de INVIAS en el mismo orden, así que el resultado es el
    archivo original. Devuelve un GeoDataFrame (id_tramo, codigo_via, sector, ruta,
    geometry) sin los tramos fuera de servicio."""
    faltan = [p.name for p in c.PARTES_RED_VIAL if not p.exists()]
    if faltan:
        raise FileNotFoundError(f"Faltan partes de la red en {c.CARPETA_PARTES_RED}: "
                                f"{', '.join(faltan)}. Ver data/raw/README.md.")
    red = pd.concat([gpd.read_file(p) for p in c.PARTES_RED_VIAL], ignore_index=True)
    # 'nombretramo' viene vacío: el nombre del tramo está en 'sector'
    red = red.rename(columns={"objectid": "id_tramo", "codigotramo": "codigo_via"})
    for col in ("codigo_via", "sector", "ruta"):                 # " " cuenta como vacío
        red[col] = red[col].astype("string").str.strip().replace("", pd.NA)
        red[col] = red[col].astype(object).where(red[col].notna(), None)
    fuera = red["sector"].fillna("").str.contains(c.EXCLUIR_SECTOR, case=False)
    if reportar:
        anotar(f"[A] {len(red)} tramos de INVIAS ({len(c.PARTES_RED_VIAL)} partes unidas); "
               f"se quitan {fuera.sum()} '{c.EXCLUIR_SECTOR}'.")
    return red.loc[~fuera, ["id_tramo", "codigo_via", "sector", "ruta", "geometry"]]


def leer_municipios():
    """Municipios con coordenadas, en metros (CRS_METRICO). Columnas: cod_mpio, nombre,
    departamento, ton_total (toneladas que salen y llegan), geometry."""
    m = pd.read_csv(c.MUNICIPIOS, dtype={"COD": str})
    m = m.rename(columns={"COD": "cod_mpio", "NOMBRE_MPIO": "nombre",
                          "DEPARTAMENTO": "departamento", "TON_TOTAL": "ton_total"})
    m["cod_mpio"] = m["cod_mpio"].str.zfill(5)
    m = m.dropna(subset=["LON", "LAT"])
    m = gpd.GeoDataFrame(m, geometry=gpd.points_from_xy(m["LON"], m["LAT"]),
                         crs=c.CRS_GEOGRAFICO)
    return m.to_crs(c.CRS_METRICO)


def leer_od():
    """Matriz O-D entre municipios (o, d, toneladas, viajes), sin autolazos."""
    od = pd.read_csv(c.MATRIZ_OD, dtype={"ORIGEN": str, "DESTINO": str})
    od = od.rename(columns={"ORIGEN": "o", "DESTINO": "d", "TONELADAS": "toneladas",
                            "VIAJES": "viajes"})
    od["o"], od["d"] = od["o"].str.zfill(5), od["d"].str.zfill(5)
    return od[od["o"] != od["d"]]
