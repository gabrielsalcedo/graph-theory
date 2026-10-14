"""Grafo de análisis: ciudades + cruces clave.

La red detallada (02_construir_grafo.py: ~840 nodos, casi todos cruces de intercambiadores y
dobles calzadas) sirve para MEDIR distancias, pero es demasiado grande para aplicar los
conceptos del curso. Este módulo la resume en un grafo pequeño y planar:

  VÉRTICES = las N_NODOS_CIUDADES ciudades (o áreas metropolitanas) con más carga
             + los CRUCES CLAVE donde se bifurcan las rutas entre ellas.
  ARISTAS  = corredores: tramos de la red entre dos vértices que no pasan por otro.
  PESO     = costo de la ruta mínima por la red detallada entre los dos vértices.

Pasos:
  1. aglomerar: municipios a menos de RADIO_AGLOMERACION_M de una ciudad con más carga
     se funden con ella (Bogotá + Soacha + Funza..., Medellín + Itagüí + Bello...).
  2. subgrafo_rutas: se conservan solo las aristas de la red detallada que usa alguna
     ruta óptima entre ciudades, o el DESVÍO óptimo cuando se cierra un corredor de
     esas rutas. Lo demás no interviene ni en las rutas ni en los cierres.
  3. cruces clave: en ese subgrafo, los vértices de grado >= 3 son bifurcaciones. Las que
     están a menos de RADIO_CRUCES_M de una ciudad se asignan a la ciudad; las demás se
     agrupan (radio RADIO_CRUCES_M) y cada grupo es un vértice.
  4. aristas: búsqueda desde cada vértice hasta tocar otro vértice; el peso es la ruta
     mínima entre ambos representantes. Se eliminan los cruces que quedan con grado 2 y
     las aristas que otro camino iguala en costo (spanner con t = 1 + EPS_REDUNDANCIA).

Cada arista guarda los tramos INVIAS (ids_tramo) que recorre: un CIERRE de un tramo físico
se simula quitando las aristas que lo usan (aristas_que_usan).
"""

import heapq
import math

import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString



# ---------------------------------------------------------------------------
# 1. Aglomeración
# ---------------------------------------------------------------------------
def aglomerar(municipios: pd.DataFrame, radio_m: float) -> dict:
    """Devuelve {cod_mpio: cod_representante}. Recorre de mayor a menor carga; cada
    municipio se une a la primera ciudad principal (ya recorrida) a menos de radio_m."""
    m = municipios.sort_values("ton_total", ascending=False)
    rep, principales = {}, []
    for f in m.itertuples():
        destino = f.cod_mpio
        for p in principales:
            if math.hypot(f.x - p.x, f.y - p.y) <= radio_m:
                destino = p.cod_mpio
                break
        else:
            principales.append(f)
        rep[f.cod_mpio] = destino
    return rep


def _camino(previo, destino):
    c = []
    while destino is not None:
        c.append(destino)
        destino = previo[destino]
    return c[::-1]


def _orientada(G, a, b):
    g = G.edges[a, b]["geometry"]
    xa, ya = G.nodes[a]["x"], G.nodes[a]["y"]
    c = list(g.coords)
    d0 = (c[0][0] - xa) ** 2 + (c[0][1] - ya) ** 2
    d1 = (c[-1][0] - xa) ** 2 + (c[-1][1] - ya) ** 2
    return c if d0 <= d1 else c[::-1]


def _atributos_corredor(G, nodos):
    tramos = [G.edges[a, b] for a, b in zip(nodos[:-1], nodos[1:])]
    largo = sum(t["longitud_m"] for t in tramos)

    def unicos(campo):
        vistos = []
        for t in tramos:
            for x in t.get(campo, ()):
                if x not in vistos:
                    vistos.append(x)
        return tuple(vistos)

    coords = []
    for a, b in zip(nodos[:-1], nodos[1:]):
        c = _orientada(G, a, b)
        coords += c if not coords else c[1:]
    doble = sum(t["longitud_m"] for t in tramos if t.get("calzada") == "2")
    return {
        "tipo": "via",
        "longitud_m": largo,
        "costo": sum(t["costo"] for t in tramos),
        "ids_tramo": unicos("ids_tramo"),
        "codigos_via": unicos("codigos_via"),
        "rutas": unicos("rutas"),
        "sectores": unicos("nombres"),
        "superficie_afirmado_frac": sum(t["superficie_afirmado_frac"] * t["longitud_m"]
                                        for t in tramos) / largo,
        "frac_doble_calzada": doble / largo,
        "calzada": "2" if doble / largo >= 0.5 else "1",
        "concesiones": unicos("concesiones"),
        "n_paralelas": 1,
        "geometry": LineString(coords),
    }


# ---------------------------------------------------------------------------
# 2. Subgrafo de rutas óptimas y desvíos
# ---------------------------------------------------------------------------
def _ek(u, v):
    return (u, v) if u < v else (v, u)


def _rutas(G, ciudades, pares=None):
    out = {}
    for s in ciudades:
        _, P = nx.single_source_dijkstra(G, s, weight="costo")
        for t in ciudades:
            if s < t and (pares is None or (s, t) in pares) and t in P:
                out[(s, t)] = P[t]
    return out


def _aristas(camino):
    return {_ek(a, b) for a, b in zip(camino[:-1], camino[1:])}


def subgrafo_rutas(D, ciudades):
    """Aristas de D usadas por alguna ruta óptima entre ciudades o por su desvío cuando se
    cierra un corredor (cadena de aristas entre bifurcaciones) de esas rutas."""
    P = _rutas(D, ciudades)
    S = set().union(*(_aristas(p) for p in P.values()))
    K = D.edge_subgraph(S)
    fijos = {n for n in K if n in ciudades or K.degree(n) != 2}
    vistas, desvios = set(), set()
    for n in sorted(fijos):                    # orden fijo: resultados reproducibles
        for m in K[n]:
            if _ek(n, m) in vistas:
                continue
            c = [n, m]
            while c[-1] not in fijos:
                c.append(next(x for x in K[c[-1]] if x != c[-2]))
            E = _aristas(c)
            vistas |= E
            afectados = {k for k, p in P.items() if _aristas(p) & E}
            H = D.copy()
            H.remove_edges_from(E)
            for p in _rutas(H, ciudades, afectados).values():
                desvios |= _aristas(p)
    return D.edge_subgraph(S | desvios).copy()


# ---------------------------------------------------------------------------
# 3-4. Construcción
# ---------------------------------------------------------------------------
def _xy(G, n):
    return np.array([G.nodes[n]["x"], G.nodes[n]["y"]])


def construir(D: nx.Graph, n_nodos: int, radio_m: float, radio_cruces_m: float,
              eps: float, referencia: pd.DataFrame, reporte: list):
    """D = grafo detallado. referencia = municipios con x, y, nombre (para nombrar cruces).
    Devuelve (A, tabla_municipios)."""
    # 1. ciudades
    mun = pd.DataFrame([{"nodo": n, "x": d["x"], "y": d["y"], **{k: d[k] for k in
                         ("cod_mpio", "nombre", "departamento", "ton_total")}}
                        for n, d in D.nodes(data=True) if d.get("tipo") == "municipio"])
    mun["representante"] = mun["cod_mpio"].map(aglomerar(mun, radio_m))
    grupos = (mun.groupby("representante")
                 .agg(ton_total=("ton_total", "sum"),
                      miembros=("nombre", lambda s: ", ".join(s)),
                      n_miembros=("nombre", "size"))
                 .sort_values("ton_total", ascending=False))
    elegidos = grupos.head(n_nodos)
    nodo_de = dict(zip(mun["cod_mpio"], mun["nodo"]))
    ciudades = [nodo_de[c] for c in elegidos.index]

    # 2. subgrafo de rutas y desvíos
    U = subgrafo_rutas(D, ciudades)

    # 3. cruces clave
    grupo = {c: c for c in ciudades}
    for c in ciudades:                         # puntos de enganche de la ciudad
        for v, d in U[c].items():
            if d["tipo"] == "conector":
                grupo.setdefault(v, c)
    bif = [n for n in U if n not in grupo and U.degree(n) >= 3]
    cruces = []
    for n in sorted(bif, key=lambda n: -U.degree(n)):
        dc = {c: np.hypot(*(_xy(U, n) - _xy(U, c))) for c in ciudades}
        cerca = min(dc, key=dc.get)
        if dc[cerca] <= radio_cruces_m:
            grupo[n] = cerca
            continue
        for r in cruces:
            if np.hypot(*(_xy(U, n) - _xy(U, r))) <= radio_cruces_m:
                grupo[n] = r
                break
        else:
            cruces.append(n)
            grupo[n] = n
    vertices = set(grupo.values())

    # 4. aristas: búsqueda multi-origen hasta tocar otro vértice
    caminos = {}
    for v in sorted(vertices):
        fuentes = [n for n, g in grupo.items() if g == v]
        dist = {f: 0.0 for f in fuentes}
        cola = [(0.0, i, f) for i, f in enumerate(fuentes)]
        k, vistos = len(cola), set()
        while cola:
            d, _, n = heapq.heappop(cola)
            if n in vistos:
                continue
            vistos.add(n)
            g = grupo.get(n)
            if g is not None and g != v:
                caminos.setdefault(_ek(v, g), None)
                continue
            for m, dd in U[n].items():
                nd = d + dd["costo"]
                if nd < dist.get(m, math.inf):
                    dist[m] = nd
                    k += 1
                    heapq.heappush(cola, (nd, k, m))
    A = nx.Graph()
    A.add_nodes_from(sorted(vertices))
    for a, b in sorted(caminos):
        p = nx.dijkstra_path(U, a, b, weight="costo")
        A.add_edge(a, b, camino=p, costo=sum(U.edges[x, y]["costo"] for x, y in zip(p[:-1], p[1:])))

    # cruces que quedaron de grado 2: ya no son bifurcaciones
    cambio = True
    while cambio:
        cambio = False
        for n in list(A):
            if n in cruces and A.degree(n) == 2:
                a, b = list(A[n])
                pa, pb = A.edges[a, n], A.edges[n, b]
                ca = pa["camino"] if pa["camino"][-1] == n else pa["camino"][::-1]
                cb = pb["camino"] if pb["camino"][0] == n else pb["camino"][::-1]
                costo = pa["costo"] + pb["costo"]
                if not A.has_edge(a, b) or A.edges[a, b]["costo"] > costo:
                    A.remove_node(n)
                    A.add_edge(a, b, camino=ca + cb[1:], costo=costo)
                    cambio = True
    cruces = [c for c in cruces if c in A]

    # spanner: se quita una arista si otro camino cuesta <= t veces lo mismo
    t = 1 + eps
    H = nx.Graph()
    H.add_nodes_from(A)
    for a, b, d in sorted(A.edges(data=True), key=lambda e: e[2]["costo"]):
        try:
            actual = nx.dijkstra_path_length(H, a, b, weight="costo")
        except nx.NetworkXNoPath:
            actual = math.inf
        if actual > t * d["costo"] * (1 + 1e-9):
            H.add_edge(a, b, **d)
    m_antes, A = A.number_of_edges(), H

    # atributos finales (los que usan rutas.py, centralidad.py y los mapas)
    G = nx.Graph(**D.graph)
    ref = referencia.reset_index(drop=True)
    for cod, g in elegidos.iterrows():
        n = nodo_de[cod]
        d = D.nodes[n]
        G.add_node(n, tipo="municipio", cod_mpio=cod, nombre=d["nombre"],
                   departamento=d["departamento"], x=d["x"], y=d["y"],
                   ton_total=float(g["ton_total"]), miembros=g["miembros"],
                   n_miembros=int(g["n_miembros"]))
    for i, c in enumerate(sorted(cruces, key=lambda c: -D.nodes[c]["y"]), start=1):
        x, y = D.nodes[c]["x"], D.nodes[c]["y"]
        j = int(np.argmin(np.hypot(ref["x"] - x, ref["y"] - y)))
        G.add_node(c, tipo="cruce", nombre=f"Cruce {i} ({ref.at[j, 'nombre'].title()})",
                   x=x, y=y)
    for a, b, d in A.edges(data=True):
        G.add_edge(a, b, **_atributos_corredor(D, d["camino"]))
    def corto(n):
        nom = G.nodes[n]["nombre"]
        if G.nodes[n]["tipo"] == "cruce":            # "Cruce 26 (Zarzal)" -> "cr. Zarzal"
            return "cr. " + nom.split("(")[1].rstrip(")")
        return nom.split(",")[0].title()
    for i, (u, v, d) in enumerate(sorted(G.edges(data=True),
                                         key=lambda e: -e[2]["longitud_m"]), start=1):
        d["id_arista"] = f"e{i:02d}"
        d["nombres"] = (f"{corto(u)} – {corto(v)}",)

    reporte += [
        f"[análisis] Aglomeración a {radio_m / 1000:.0f} km: {len(mun)} municipios -> "
        f"{len(grupos)} grupos; vértices = los {len(elegidos)} con más carga.",
        "[análisis] Áreas metropolitanas fundidas: " + "; ".join(
            r.miembros for r in elegidos.itertuples() if r.n_miembros > 1),
        f"[análisis] Subgrafo de rutas óptimas y desvíos: {U.number_of_nodes()} nodos, "
        f"{U.number_of_edges()} aristas de la red detallada.",
        f"[análisis] Cruces clave (bifurcaciones agrupadas a {radio_cruces_m / 1000:.0f} km): "
        f"{len(cruces)}.",
        f"[análisis] Spanner (t = {t:.2f}): {m_antes} -> {G.number_of_edges()} aristas.",
        f"[análisis] GRAFO DE ANÁLISIS: {G.number_of_nodes()} vértices ({len(elegidos)} ciudades + "
        f"{len(cruces)} cruces), {G.number_of_edges()} aristas; conexo = {nx.is_connected(G)}; "
        f"planar = {nx.check_planarity(G)[0]}.",
    ]
    return G, mun


def aristas_que_usan(C: nx.Graph, id_tramo: int):
    """Aristas del grafo de ciudades que recorren el tramo INVIAS id_tramo (para cierres)."""
    return [(u, v) for u, v, d in C.edges(data=True) if id_tramo in d["ids_tramo"]]


def od_ciudades(od: pd.DataFrame, mun: pd.DataFrame, C: nx.Graph) -> pd.DataFrame:
    """Matriz O-D agregada a los vértices del grafo (sin flujos internos de un área)."""
    rep = dict(zip(mun["cod_mpio"], mun["representante"]))
    nodo = {d["cod_mpio"]: n for n, d in C.nodes(data=True) if d.get("tipo") == "municipio"}
    o = od.assign(o=od["cod_origen"].map(rep).map(nodo), d=od["cod_destino"].map(rep).map(nodo))
    o = o.dropna(subset=["o", "d"])
    o = o[o["o"] != o["d"]]
    return o.groupby(["o", "d"], as_index=False)[["toneladas", "viajes"]].sum()
