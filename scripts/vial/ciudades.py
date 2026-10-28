"""
Grafo de análisis G: 25 ciudades (o áreas metropolitanas) + cruces donde se separan las
rutas. Se construye a partir de la red detallada D.

  areas_metropolitanas()  municipios a menos de 25 km se funden con la ciudad mayor
  subgrafo_de_rutas()     vías de las rutas óptimas entre ciudades y de sus desvíos
  cruces_clave()          bifurcaciones agrupadas a 25 km
  corredores()            arista entre dos vértices si hay una vía que no pasa por otro
  depurar()               quita cruces de grado 2 y aristas que otro camino iguala
  grafo_de_analisis()     todo lo anterior, en orden
  lista_ciudades()        los vértices de tipo ciudad de G
  nombre_corto()          nombre de un vértice para tablas y figuras
"""

import heapq
import math

import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString

import config as c
from vial.grafo import orientar, unicos
from vial.reporte import anotar


def lista_ciudades(G):
    """Lista de los vértices de G que son ciudades (no cruces)."""
    return [n for n, d in G.nodes(data=True) if d["tipo"] == "ciudad"]


def nombre_corto(G, n):
    """'Cruce 3 (Honda)' -> 'Honda'; 'BOGOTA, BOGOTA D. C.' -> 'Bogota'."""
    nombre = G.nodes[n]["nombre"]
    return nombre.split("(")[1][:-1] if G.nodes[n]["tipo"] == "cruce" else nombre.split(",")[0].title()


def areas_metropolitanas(mun):
    """De mayor a menor carga: un municipio a menos de 25 km de una ciudad ya vista se
    une a ella (Bogotá + Soacha + Funza...). Devuelve {cod_mpio: cod de su ciudad}."""
    rep, principales = {}, []
    for f in mun.sort_values("ton_total", ascending=False).itertuples():
        rep[f.cod_mpio] = next((p.cod_mpio for p in principales
                                if math.hypot(f.x - p.x, f.y - p.y) <= c.RADIO_AREA_M), None)
        if rep[f.cod_mpio] is None:
            principales.append(f)
            rep[f.cod_mpio] = f.cod_mpio
    return rep


def aristas_de(camino):
    """Conjunto de aristas (ordenadas) de un camino dado como lista de nodos."""
    return {tuple(sorted(e)) for e in zip(camino[:-1], camino[1:])}


def rutas_minimas(G, ciudades, pares=None):
    """Ruta más barata entre cada par de ciudades s < t (o solo los 'pares' dados).
    Devuelve {(s, t): lista de nodos}."""
    out = {}
    for s in ciudades:
        caminos = nx.single_source_dijkstra_path(G, s, weight="costo")
        for t in ciudades:
            if s < t and t in caminos and (pares is None or (s, t) in pares):
                out[(s, t)] = caminos[t]
    return out


def subgrafo_de_rutas(D, ciudades):
    """Las vías que usa alguna ruta óptima entre ciudades, más los desvíos óptimos cuando
    se cierra cada tramo de esas rutas. Así el grafo ya contiene todo desvío posible.
    Devuelve ese subgrafo de D."""
    P = rutas_minimas(D, ciudades)
    usadas = set().union(*(aristas_de(p) for p in P.values()))
    K = D.edge_subgraph(usadas)
    fijos = {n for n in K if n in ciudades or K.degree(n) != 2}
    vistas, desvios = set(), set()
    for n in sorted(fijos):
        for m in K[n]:
            if tuple(sorted((n, m))) in vistas:
                continue
            tramo = [n, m]                        # se sigue la vía hasta el próximo cruce
            while tramo[-1] not in fijos:
                tramo.append(next(x for x in K[tramo[-1]] if x != tramo[-2]))
            E = aristas_de(tramo)
            vistas |= E
            H = D.copy()
            H.remove_edges_from(E)
            afectados = {k for k, p in P.items() if aristas_de(p) & E}
            for p in rutas_minimas(H, ciudades, afectados).values():
                desvios |= aristas_de(p)
    return D.edge_subgraph(usadas | desvios).copy()


def cruces_clave(U, ciudades):
    """Bifurcaciones (grado >= 3). Las que están a menos de 25 km de una ciudad se le
    asignan a la ciudad; las demás se agrupan a 25 km y cada grupo es un vértice.
    Devuelve (grupo: {nodo de U: vértice de G}, lista de cruces)."""
    xy = lambda n: np.array([U.nodes[n]["x"], U.nodes[n]["y"]])
    grupo = {ci: ci for ci in ciudades}
    for ci in ciudades:                           # donde la ciudad se engancha a las vías
        for v, d in U[ci].items():
            if d["tipo"] == "conector":
                grupo.setdefault(v, ci)
    cruces = []
    for n in sorted((n for n in U if n not in grupo and U.degree(n) >= 3),
                    key=lambda n: -U.degree(n)):
        dist = {ci: np.hypot(*(xy(n) - xy(ci))) for ci in ciudades}
        cerca = min(dist, key=dist.get)
        if dist[cerca] <= c.RADIO_CRUCES_M:
            grupo[n] = cerca
            continue
        grupo[n] = next((r for r in cruces if np.hypot(*(xy(n) - xy(r))) <= c.RADIO_CRUCES_M), n)
        if grupo[n] == n:
            cruces.append(n)
    return grupo, cruces


def corredores(U, grupo):
    """Arista entre dos vértices si hay una vía entre ellos que no pasa por otro vértice
    (búsqueda desde cada vértice que se detiene al tocar otro). Peso = ruta mínima.
    Devuelve un grafo cuyas aristas guardan el camino por U y su costo."""
    pares = set()
    for v in sorted(set(grupo.values())):
        fuentes = [n for n, g in grupo.items() if g == v]
        dist = {f: 0.0 for f in fuentes}
        cola = [(0.0, i, f) for i, f in enumerate(fuentes)]
        k, vistos = len(cola), set()
        while cola:
            d, _, n = heapq.heappop(cola)
            if n in vistos:
                continue
            vistos.add(n)
            if grupo.get(n, v) != v:
                pares.add(tuple(sorted((v, grupo[n]))))
                continue
            for m, dd in U[n].items():
                if d + dd["costo"] < dist.get(m, math.inf):
                    dist[m] = d + dd["costo"]
                    k += 1
                    heapq.heappush(cola, (dist[m], k, m))
    A = nx.Graph()
    A.add_nodes_from(sorted(set(grupo.values())))
    for a, b in sorted(pares):
        p = nx.dijkstra_path(U, a, b, weight="costo")
        A.add_edge(a, b, camino=p, costo=sum(U.edges[e]["costo"] for e in zip(p[:-1], p[1:])))
    return A


def depurar(A, cruces):
    """1) Un cruce que quedó con dos vecinos ya no es bifurcación: se funden sus aristas.
    2) Se quita una arista si otro camino cuesta lo mismo (no cambia ninguna ruta).
    Devuelve el grafo depurado."""
    cambio = True
    while cambio:
        cambio = False
        for n in list(A):
            if n in cruces and A.degree(n) == 2:
                a, b = list(A[n])
                pa, pb = A.edges[a, n]["camino"], A.edges[n, b]["camino"]
                pa = pa if pa[-1] == n else pa[::-1]
                pb = pb if pb[0] == n else pb[::-1]
                costo = A.edges[a, n]["costo"] + A.edges[n, b]["costo"]
                if not A.has_edge(a, b) or A.edges[a, b]["costo"] > costo:
                    A.remove_node(n)
                    A.add_edge(a, b, camino=pa + pb[1:], costo=costo)
                    cambio = True
    H = nx.Graph()
    H.add_nodes_from(A)
    for a, b, d in sorted(A.edges(data=True), key=lambda e: e[2]["costo"]):
        try:
            otro = nx.dijkstra_path_length(H, a, b, weight="costo")
        except nx.NetworkXNoPath:
            otro = math.inf
        if otro > d["costo"] * (1 + 1e-9):
            H.add_edge(a, b, **d)
    anotar(f"[D] Aristas que otro camino iguala en costo: {A.number_of_edges() - H.number_of_edges()} eliminadas.")
    return H


def corredor(D, camino):
    """Une los tramos de la red detallada que recorre un corredor. Devuelve los atributos
    de la arista de G (longitud, costo, tramos de INVIAS, geometría)."""
    tramos = [D.edges[e] for e in zip(camino[:-1], camino[1:])]
    coords = []
    for a, b in zip(camino[:-1], camino[1:]):
        g = orientar(D.edges[a, b]["geometry"], D.nodes[a]["x"], D.nodes[a]["y"])
        coords += list(g.coords) if not coords else list(g.coords)[1:]
    return dict(longitud_m=sum(t["longitud_m"] for t in tramos),
                costo=sum(t["costo"] for t in tramos),
                ids_tramo=unicos(*(t["ids_tramo"] for t in tramos)),
                codigos_via=unicos(*(t["codigos_via"] for t in tramos)),
                sectores=unicos(*(t["sectores"] for t in tramos)),
                geometry=LineString(coords))


def grafo_de_analisis(D, todos):
    """Recibe la red detallada D y todos los municipios; devuelve (G, mun), donde mun son
    las ciudades de D con el código de su área metropolitana ('representante')."""
    mun = pd.DataFrame([{"nodo": n, **d} for n, d in D.nodes(data=True)
                        if d["tipo"] == "municipio"])
    mun["representante"] = mun["cod_mpio"].map(areas_metropolitanas(mun))
    areas = (mun.groupby("representante")
                .agg(ton_total=("ton_total", "sum"), miembros=("nombre", ", ".join))
                .sort_values("ton_total", ascending=False).head(c.N_VERTICES_CIUDAD))
    nodo_de = dict(zip(mun["cod_mpio"], mun["nodo"]))
    ciudades = [nodo_de[cod] for cod in areas.index]
    anotar(f"[D] {len(mun)} ciudades -> {mun['representante'].nunique()} áreas; se toman "
           f"las {len(ciudades)} con más carga.")

    U = subgrafo_de_rutas(D, ciudades)
    grupo, cruces = cruces_clave(U, ciudades)
    A = depurar(corredores(U, grupo), cruces)
    cruces = [x for x in cruces if x in A]

    G = nx.Graph()
    for cod, f in areas.iterrows():
        n = nodo_de[cod]
        G.add_node(n, **{k: D.nodes[n][k] for k in ("x", "y", "cod_mpio", "nombre", "departamento")},
                   tipo="ciudad", ton_total=f["ton_total"], miembros=f["miembros"])
    for i, x in enumerate(sorted(cruces, key=lambda x: -D.nodes[x]["y"]), start=1):
        xs, ys = D.nodes[x]["x"], D.nodes[x]["y"]
        cerca = todos.iloc[int(np.argmin(np.hypot(todos.geometry.x - xs, todos.geometry.y - ys)))]
        G.add_node(x, tipo="cruce", nombre=f"Cruce {i} ({cerca['nombre'].title()})", x=xs, y=ys)
    for a, b, d in A.edges(data=True):
        G.add_edge(a, b, **corredor(D, d["camino"]))
    corto = lambda n: ("cr. " if G.nodes[n]["tipo"] == "cruce" else "") + nombre_corto(G, n)
    for i, (u, v, d) in enumerate(sorted(G.edges(data=True), key=lambda e: -e[2]["longitud_m"]), 1):
        d["id_arista"], d["nombre"] = f"e{i:02d}", f"{corto(u)} – {corto(v)}"
    anotar(f"[D] GRAFO DE ANÁLISIS: {G.number_of_nodes()} vértices ({len(ciudades)} ciudades "
           f"+ {len(cruces)} cruces), {G.number_of_edges()} aristas; conexo = "
           f"{nx.is_connected(G)}; planar = {nx.check_planarity(G)[0]}.")

    # comparación con la red detallada: ¿cuánto se distorsionan las distancias al resumir?
    razon = [nx.dijkstra_path_length(G, s, t, weight="costo") /
             nx.dijkstra_path_length(D, s, t, weight="costo")
             for s in ciudades for t in ciudades if s != t]
    anotar(f"[D] Costo de las rutas en el grafo de análisis / en la red detallada: media "
           f"{np.mean(razon):.3f}, máxima {np.max(razon):.3f}, exactas {100 * np.mean(np.array(razon) < 1.0001):.1f} %.")
    return G, mun
