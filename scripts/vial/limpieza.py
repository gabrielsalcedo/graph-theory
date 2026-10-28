"""
Limpieza topológica del mapa de INVIAS: que las vías que se tocan en la realidad también
se toquen en el grafo.

  quitar_duplicados()   líneas repetidas o segunda calzada de la misma vía
  partir_en_cruces()    vértice común donde dos vías se tocan (T) o se cruzan (X)
  unir_extremos()       extremos a menos de 'tol' metros se vuelven un solo nodo
  n_componentes()       componentes conexas de un conjunto de segmentos
  limpiar()             todo lo anterior, en orden
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import substring

import config as c
from vial.reporte import anotar


def quitar_duplicados(red):
    """Si una línea queda dentro de una franja de 30 m alrededor de otra más larga, es un
    duplicado o la segunda calzada de la misma vía: se elimina. Devuelve la red sin ellas."""
    largo = red.geometry.length
    sidx = red.sindex
    borrar = set()
    for i in largo.sort_values(ascending=False).index:      # de la más larga a la más corta
        if i in borrar:
            continue
        for j in sidx.query(red.geometry[i].buffer(c.DUPLICADO_M), predicate="contains"):
            if j == i or j in borrar or largo[j] > largo[i] or (largo[j] == largo[i] and j < i):
                continue
            borrar.add(j)
    anotar(f"[B] {len(borrar)} líneas duplicadas o de segunda calzada eliminadas.")
    return red.drop(index=list(borrar)).reset_index(drop=True)


def partir_en_cruces(red, tol):
    """Parte cada línea donde otra la toca (unión en T) o la cruza (cruce en X), para que
    en esos puntos exista un vértice común. Devuelve las piezas."""
    geoms = list(red.geometry)
    serie = gpd.GeoSeries(geoms)
    sidx = serie.sindex
    cortes = {i: [] for i in range(len(geoms))}
    for i, g in enumerate(geoms):                             # uniones en T
        for p in (Point(g.coords[0]), Point(g.coords[-1])):
            for j in sidx.query(p.buffer(tol), predicate="intersects"):
                s = geoms[j].project(p)
                if j != i and tol < s < geoms[j].length - tol and geoms[j].distance(p) <= tol:
                    cortes[j].append(s)
    a, b = sidx.query(serie, predicate="intersects")         # cruces en X
    for i, j in zip(a, b):
        if j <= i:
            continue
        inter = geoms[i].intersection(geoms[j])
        puntos = [inter] if inter.geom_type == "Point" else [
            p for p in getattr(inter, "geoms", []) if p.geom_type == "Point"]
        for p in puntos:
            for k in (i, j):
                s = geoms[k].project(p)
                if tol < s < geoms[k].length - tol:
                    cortes[k].append(s)
    filas, piezas = [], []
    for i, g in enumerate(geoms):
        limites = [0.0] + sorted(set(round(x, 1) for x in cortes[i])) + [g.length]
        for s0, s1 in zip(limites[:-1], limites[1:]):
            if s1 - s0 > 1e-6:
                filas.append(i)
                piezas.append(substring(g, s0, s1))
    out = red.iloc[filas].copy()
    out["geometry"] = piezas
    return gpd.GeoDataFrame(out, geometry="geometry", crs=red.crs).reset_index(drop=True)


def unir_extremos(piezas, tol):
    """Extremos a menos de 'tol' metros se vuelven un solo nodo (en su punto medio).
    Agrupa con unión-búsqueda: si a está cerca de b y b de c, los tres quedan juntos.
    Devuelve los segmentos con sus nodos u, v (sin los que quedan de un solo punto)."""
    ini = np.array([g.coords[0] for g in piezas.geometry])
    fin = np.array([g.coords[-1] for g in piezas.geometry])
    puntos = np.vstack([ini, fin])
    padre = np.arange(len(puntos))

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    for a, b in cKDTree(puntos).query_pairs(tol):
        padre[raiz(b)] = raiz(a)
    _, grupo = np.unique([raiz(a) for a in range(len(puntos))], return_inverse=True)
    centro = pd.DataFrame(puntos).groupby(grupo).mean().values
    n = len(piezas)
    out = piezas.copy()
    out["u"], out["v"] = grupo[:n], grupo[n:]
    out["geometry"] = [LineString([tuple(centro[u])] + list(g.coords)[1:-1] + [tuple(centro[v])])
                       for g, u, v in zip(piezas.geometry, out["u"], out["v"])]
    out = out[out["u"] != out["v"]].reset_index(drop=True)
    out.attrs["xy"] = centro
    return out


def n_componentes(seg):
    """Número de componentes conexas de los segmentos (columnas u, v)."""
    return nx.number_connected_components(nx.Graph(list(zip(seg["u"], seg["v"]))))


def limpiar(red):
    """Recibe la red de INVIAS y devuelve los segmentos limpios, en metros, con nodos u, v."""
    red = red.explode(index_parts=False).reset_index(drop=True)    # MultiLineString -> partes
    red["geometry"] = shapely.remove_repeated_points(red.geometry.values)
    red = red.to_crs(c.CRS_METRICO)
    red["geometry"] = red.geometry.simplify(c.SIMPLIFICAR_M)
    anotar(f"[B] {len(red)} líneas; componentes conexas antes de limpiar: "
           f"{n_componentes(unir_extremos(red, 1e-6))}.")
    red = quitar_duplicados(red)
    seg = unir_extremos(partir_en_cruces(red, c.UNION_M), c.UNION_M)
    anotar(f"[B] Con tolerancia de {c.UNION_M} m: {len(seg)} segmentos y "
           f"{n_componentes(seg)} componentes conexas.")
    return seg
