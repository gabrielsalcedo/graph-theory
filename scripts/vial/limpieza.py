"""Limpieza topológica de la red vial.

Orden de las operaciones (cada una se reporta):
  1. Geometrías: descartar nulas, vacías y de longitud cero; separar MultiLineString en
     partes; quitar vértices repetidos; tramos fuera de Colombia (coordenadas invertidas).
  2. Reproyección a CRS métrico.
  3. Duplicados y segundas calzadas: una línea contenida en un buffer de
     TOLERANCIA_DUPLICADO_M alrededor de otra más larga se elimina.
  4. Partición en intersecciones: puntos donde un extremo toca el INTERIOR de otra línea
     (uniones en T) y cruces en X sin vértice común.
  5. Unión de extremos cercanos (< TOLERANCIA_UNION_M) en un solo nodo.

Resultado: segmentos con columnas u, v (ids de nodo), longitud_m y los atributos.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import LineString, Point, box
from shapely.ops import substring
from scipy.spatial import cKDTree

import config


# ---------------------------------------------------------------------------
# 1. Validación de geometrías
# ---------------------------------------------------------------------------
def validar_geometrias(red: gpd.GeoDataFrame, reporte: list) -> gpd.GeoDataFrame:
    n0 = len(red)
    nulas = red.geometry.isna() | red.geometry.is_empty
    red = red[~nulas].copy()

    n_multi = (red.geom_type == "MultiLineString").sum()
    red = red.explode(index_parts=False).reset_index(drop=True)
    red["geometry"] = shapely.remove_repeated_points(red.geometry.values)
    cero = pd.Series(shapely.length(red.geometry.values) == 0, index=red.index)
    red = red[~cero].copy()

    # extensión: ¿cae dentro de Colombia?
    marco = box(*config.LIMITES_COLOMBIA)
    afuera = ~red.geometry.within(marco)
    corregidos, descartados = 0, 0
    for idx in red.index[afuera]:
        g = red.at[idx, "geometry"]
        invertida = LineString([(y, x) for x, y in g.coords])
        if config.CORREGIR_COORDENADAS_INVERTIDAS and invertida.within(marco):
            red.at[idx, "geometry"] = invertida
            corregidos += 1
        else:
            red = red.drop(index=idx)
            descartados += 1

    reporte += [
        f"[limpieza] {nulas.sum()} geometrías nulas o vacías descartadas.",
        f"[limpieza] {n_multi} MultiLineString separados en sus partes.",
        f"[limpieza] {cero.sum()} geometrías de longitud cero descartadas.",
        f"[limpieza] {afuera.sum()} tramos fuera de Colombia: {corregidos} corregidos "
        f"(lat/lon invertidas), {descartados} descartados.",
        f"[limpieza] {n0} filas -> {len(red)} líneas válidas.",
    ]
    return red.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. Duplicados y calzadas dobles
# ---------------------------------------------------------------------------
def quitar_duplicados(red: gpd.GeoDataFrame, reporte: list) -> gpd.GeoDataFrame:
    tol = config.TOLERANCIA_DUPLICADO_M
    red = red.copy()
    largo = red.geometry.length
    orden = largo.sort_values(ascending=False).index
    sidx = red.sindex
    eliminado = pd.Series(False, index=red.index)
    registro = []
    for i in orden:
        if eliminado[i]:
            continue
        gi = red.at[i, "geometry"]
        zona = gi.buffer(tol)
        for j in sidx.query(zona, predicate="contains"):
            j = red.index[j]
            if j == i or eliminado[j] or largo[j] > largo[i]:
                continue
            gj = red.at[j, "geometry"]
            if largo[j] == largo[i] and j < i:
                continue  # dos copias idénticas: se conserva la de menor índice
            dist = gi.hausdorff_distance(gj)
            if dist < 0.5:
                tipo = "duplicado exacto o invertido"
            elif largo[j] > 0.9 * largo[i]:
                tipo = "calzada paralela"
                if config.FUSIONAR_CALZADAS_DOBLES:
                    red.at[i, "calzada"] = "2"
            else:
                tipo = "duplicado parcial"
            if tipo == "calzada paralela" and not config.FUSIONAR_CALZADAS_DOBLES:
                continue
            eliminado[j] = True
            registro.append((red.at[j, "id_tramo"], red.at[i, "id_tramo"], tipo, round(dist, 1)))
    reg = pd.DataFrame(registro, columns=["id_eliminado", "id_conservado", "tipo", "hausdorff_m"])
    for tipo, n in reg["tipo"].value_counts().items():
        reporte.append(f"[limpieza] {n} líneas eliminadas por {tipo}.")
    return red[~eliminado].reset_index(drop=True), reg


# ---------------------------------------------------------------------------
# 4-5. Partición en intersecciones y unión de extremos
# ---------------------------------------------------------------------------
def _agrupar(puntos: np.ndarray, tol: float) -> np.ndarray:
    """Agrupa puntos a menos de 'tol' (unión-búsqueda). Devuelve una etiqueta por punto."""
    padre = np.arange(len(puntos))

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    for a, b in cKDTree(puntos).query_pairs(tol):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[rb] = ra
    raices = np.array([raiz(a) for a in range(len(puntos))])
    _, etiquetas = np.unique(raices, return_inverse=True)
    return etiquetas


def _extremos(geoms):
    ini = np.array([g.coords[0] for g in geoms])
    fin = np.array([g.coords[-1] for g in geoms])
    return ini, fin


def puntos_de_particion(geoms, tol):
    """Distancias (a lo largo de cada línea) donde hay que partirla."""
    cortes = {i: [] for i in range(len(geoms))}
    serie = gpd.GeoSeries(geoms)
    sidx = serie.sindex
    ini, fin = _extremos(geoms)

    # uniones en T: un extremo de la línea i toca el interior de la línea j
    for i, (p0, p1) in enumerate(zip(ini, fin)):
        for p in (Point(p0), Point(p1)):
            for j in sidx.query(p.buffer(tol), predicate="intersects"):
                if j == i:
                    continue
                gj = geoms[j]
                s = gj.project(p)
                if tol < s < gj.length - tol and gj.distance(p) <= tol:
                    cortes[j].append(s)

    # cruces en X sin vértice común
    a, b = sidx.query(serie, predicate="intersects")
    for i, j in zip(a, b):
        if j <= i:
            continue
        inter = geoms[i].intersection(geoms[j])
        pts = [inter] if inter.geom_type == "Point" else [
            g for g in getattr(inter, "geoms", []) if g.geom_type == "Point"]
        for p in pts:
            for k in (i, j):
                s = geoms[k].project(p)
                if tol < s < geoms[k].length - tol:
                    cortes[k].append(s)
    return cortes


def particionar(red: gpd.GeoDataFrame, tol: float):
    geoms = list(red.geometry.values)
    cortes = puntos_de_particion(geoms, tol)
    filas = []
    for i, g in enumerate(geoms):
        s = sorted(set(round(x, 1) for x in cortes[i]))
        limites = [0.0] + s + [g.length]
        for k, (a, b) in enumerate(zip(limites[:-1], limites[1:])):
            if b - a < 1e-6:
                continue
            filas.append((i, k, substring(g, a, b)))
    piezas = red.iloc[[f[0] for f in filas]].copy()
    piezas["parte"] = [f[1] for f in filas]
    piezas["geometry"] = [f[2] for f in filas]
    n_partidas = sum(1 for v in cortes.values() if v)
    return gpd.GeoDataFrame(piezas, geometry="geometry", crs=red.crs).reset_index(drop=True), n_partidas


def unir_extremos(piezas: gpd.GeoDataFrame, tol: float) -> gpd.GeoDataFrame:
    """Asigna ids de nodo a los extremos y mueve cada extremo al centroide de su grupo."""
    geoms = list(piezas.geometry.values)
    ini, fin = _extremos(geoms)
    puntos = np.vstack([ini, fin])
    etiquetas = _agrupar(puntos, tol)
    centros = pd.DataFrame(puntos).groupby(etiquetas).mean().values
    n = len(geoms)
    u, v = etiquetas[:n], etiquetas[n:]
    nuevas = []
    for k, g in enumerate(geoms):
        c = list(g.coords)
        c[0], c[-1] = tuple(centros[u[k]]), tuple(centros[v[k]])
        nuevas.append(LineString(c))
    out = piezas.copy()
    out["geometry"] = nuevas
    out["u"], out["v"] = u, v
    out = out[out["u"] != out["v"]]          # lazos colapsados por la unión
    out["longitud_m"] = out.geometry.length
    out.attrs["nodos_xy"] = centros
    return out.reset_index(drop=True)


def contar_componentes(seg: gpd.GeoDataFrame) -> int:
    import networkx as nx
    G = nx.Graph()
    G.add_edges_from(zip(seg["u"], seg["v"]))
    return nx.number_connected_components(G)


def limpiar(red: gpd.GeoDataFrame, reporte: list):
    """Ejecuta toda la limpieza. Devuelve (segmentos, duplicados, sensibilidad)."""
    red = validar_geometrias(red, reporte)
    red = red.to_crs(config.CRS_METRICO)
    if config.SIMPLIFICAR_GEOMETRIA_M:
        n_antes = int(shapely.get_num_coordinates(red.geometry.values).sum())
        largo_antes = red.length.sum()
        red["geometry"] = red.geometry.simplify(config.SIMPLIFICAR_GEOMETRIA_M)
        reporte.append(
            f"[limpieza] Simplificación Douglas-Peucker ({config.SIMPLIFICAR_GEOMETRIA_M} m): "
            f"{n_antes:,} -> {int(shapely.get_num_coordinates(red.geometry.values).sum()):,} vértices; "
            f"longitud total {100 * (red.length.sum() / largo_antes - 1):+.2f} %.")

    # componentes ANTES: solo extremos exactamente iguales (tolerancia ~ 0)
    antes = unir_extremos(red.assign(parte=0), 1e-6)
    reporte.append(f"[limpieza] Componentes conexas ANTES de limpiar: {contar_componentes(antes)}.")

    red, duplicados = quitar_duplicados(red, reporte)

    sensibilidad = []
    for tol in sorted(set(config.TOLERANCIAS_SENSIBILIDAD_M + [config.TOLERANCIA_UNION_M])):
        piezas, n_part = particionar(red, tol)
        seg = unir_extremos(piezas, tol)
        sensibilidad.append({"tolerancia_m": tol, "componentes": contar_componentes(seg),
                             "segmentos": len(seg), "lineas_partidas": n_part})
        if tol == config.TOLERANCIA_UNION_M:
            elegido = seg
    sens = pd.DataFrame(sensibilidad)
    reporte.append("[limpieza] Sensibilidad a la tolerancia de unión:\n" + sens.to_string(index=False))
    reporte.append(
        f"[limpieza] Con la tolerancia elegida ({config.TOLERANCIA_UNION_M} m): "
        f"{len(elegido)} segmentos, {contar_componentes(elegido)} componentes conexas DESPUÉS.")
    return elegido, duplicados, sens
