"""
Red detallada D: el grafo de la red limpia con las 50 ciudades conectadas.

  red_como_grafo()      multigrafo: nodos = extremos, aristas = segmentos de vía
  conectar_ciudades()   cada ciudad se une a cada ruta nacional cercana
  quitar_grado_2()      funde las aristas que solo parten una vía en pedazos
  podar()               quita componentes sin ciudades y ramales sin salida
  contraer_cortas()     funde aristas de menos de 1 km (intercambiadores)
  grafo_simple()        deja la arista más barata entre cada par de nodos
  red_detallada()       todo lo anterior, en orden
"""

import math

import geopandas as gpd
import networkx as nx
import numpy as np
from shapely.geometry import LineString
from shapely.ops import substring

import config as c
from vial.costo import costo_arista
from vial.reporte import anotar


def via(g, tramos, codigos, rutas, sectores):
    """Atributos de una arista vial. Las tuplas guardan qué tramos de INVIAS recorre."""
    return dict(tipo="via", longitud_m=g.length, geometry=g, ids_tramo=tramos,
                codigos_via=codigos, rutas=rutas, sectores=sectores)


def unicos(*tuplas):
    """Une varias tuplas sin repetir elementos y conservando el orden."""
    return tuple(dict.fromkeys(x for t in tuplas for x in t))


def orientar(g, x, y):
    """La línea g, orientada para que empiece en el extremo más cercano a (x, y)."""
    c0, c1 = g.coords[0], g.coords[-1]
    return g if (c0[0] - x) ** 2 + (c0[1] - y) ** 2 <= (c1[0] - x) ** 2 + (c1[1] - y) ** 2 \
        else LineString(g.coords[::-1])


def red_como_grafo(seg):
    """Recibe los segmentos limpios; devuelve un multigrafo (dos vías pueden unir los
    mismos dos cruces)."""
    G = nx.MultiGraph()
    for f in seg.itertuples():
        g = f.geometry
        u, v = f"n{f.u}", f"n{f.v}"
        G.add_node(u, x=g.coords[0][0], y=g.coords[0][1], tipo="cruce")
        G.add_node(v, x=g.coords[-1][0], y=g.coords[-1][1], tipo="cruce")
        tupla = lambda x: (x,) if isinstance(x, str) else ()
        G.add_edge(u, v, **via(g, (int(f.id_tramo),), tupla(f.codigo_via), tupla(f.ruta),
                              tupla(f.sector)))
    return G


def conectar_ciudades(G, ciudades):
    """Une cada ciudad al punto más cercano de CADA ruta nacional que pase a menos de
    10 km (20 km Bogotá). INVIAS no digitaliza calles urbanas: la ciudad hace de cruce
    entre las vías que llegan a ella. Si el punto cae a mitad de una arista, se parte.
    Modifica G."""
    aristas = list(G.edges(keys=True, data=True))
    geoms = gpd.GeoSeries([d["geometry"] for *_, d in aristas], crs=c.CRS_METRICO)
    componente = {n: i for i, comp in enumerate(nx.connected_components(G)) for n in comp}
    grupo = [(componente[u], (d["rutas"] or ("?",))[0]) for u, _, _, d in aristas]
    tol = c.ANCLAJE_EXTREMO_M

    anclas = {}                                   # arista -> [(posición, ciudad)]
    fila, cercana = geoms.sindex.nearest(ciudades.geometry, return_all=False)
    for i, j0 in zip(fila, cercana):
        m = ciudades.iloc[i]
        radio = c.RADIO_BOGOTA_M if m["cod_mpio"] == c.COD_BOGOTA else c.RADIO_CONEXION_M
        if geoms[j0].distance(m.geometry) > radio:
            continue
        mejor = {}                                # la arista más cercana de cada ruta
        for j in geoms.sindex.query(m.geometry, predicate="dwithin", distance=radio):
            d = geoms[j].distance(m.geometry)
            if grupo[j] not in mejor or d < mejor[grupo[j]][0]:
                mejor[grupo[j]] = (d, j)
        for _, j in mejor.values():
            anclas.setdefault(j, []).append((geoms[j].project(m.geometry), m))

    for j, lista in anclas.items():
        u, v, k, datos = aristas[j]
        g = orientar(datos["geometry"], G.nodes[u]["x"], G.nodes[u]["y"])
        cortes = sorted({s for s, _ in lista if tol <= s <= g.length - tol})
        nodo_en = {}
        if cortes:                                # partir la arista en los puntos de anclaje
            G.remove_edge(u, v, k)
            nodos = [u] + [f"p{j}_{i}" for i in range(len(cortes))] + [v]
            limites = [0.0] + cortes + [g.length]
            for i, s in enumerate(cortes):
                p = g.interpolate(s)
                G.add_node(nodos[i + 1], x=p.x, y=p.y, tipo="anclaje")
                nodo_en[s] = nodos[i + 1]
            for i in range(len(limites) - 1):
                pieza = substring(g, limites[i], limites[i + 1])
                G.add_edge(nodos[i], nodos[i + 1], **{**datos, "longitud_m": pieza.length,
                                                      "geometry": pieza})
        for s, m in sorted(lista, key=lambda t: t[0]):
            ancla = u if s < tol else v if s > g.length - tol else nodo_en[s]
            ciudad = f"M{m['cod_mpio']}"
            G.add_node(ciudad, x=m.geometry.x, y=m.geometry.y, tipo="municipio",
                       cod_mpio=m["cod_mpio"], nombre=m["nombre"],
                       departamento=m["departamento"], ton_total=float(m["ton_total"]))
            recta = LineString([(m.geometry.x, m.geometry.y),
                                (G.nodes[ancla]["x"], G.nodes[ancla]["y"])])
            G.add_edge(ciudad, ancla, tipo="conector", geometry=recta,
                       longitud_m=recta.length * c.SINUOSIDAD_CONECTOR, ids_tramo=(),
                       codigos_via=(), rutas=(), sectores=())
    n = sum(1 for _, d in G.nodes(data=True) if d["tipo"] == "municipio")
    anotar(f"[C] {n} de {len(ciudades)} ciudades conectadas a la red.")


def quitar_grado_2(G):
    """Un cruce con solo dos vías no es un cruce: sus dos aristas se funden en una.
    Modifica G."""
    cambio = True
    while cambio:
        cambio = False
        for n in list(G.nodes):
            if n not in G or G.nodes[n]["tipo"] == "municipio" or G.degree(n) != 2:
                continue
            e = list(G.edges(n, keys=True, data=True))
            if len(e) != 2:
                continue
            (_, a, _, da), (_, b, _, db) = e
            if a == b or n in (a, b) or da["tipo"] != "via" or db["tipo"] != "via":
                continue
            ga = orientar(da["geometry"], G.nodes[a]["x"], G.nodes[a]["y"])
            gb = orientar(db["geometry"], G.nodes[n]["x"], G.nodes[n]["y"])
            G.remove_node(n)
            nueva = via(LineString(list(ga.coords) + list(gb.coords)[1:]),
                        *(unicos(da[k], db[k]) for k in ("ids_tramo", "codigos_via", "rutas", "sectores")))
            nueva["longitud_m"] = da["longitud_m"] + db["longitud_m"]   # se suman los largos
            G.add_edge(a, b, **nueva)
            cambio = True


def podar(G):
    """Quita las componentes sin ciudades y los ramales sin salida. Una ruta mínima entre
    dos ciudades nunca entra a un callejón sin salida, así que no cambia ninguna ruta.
    Modifica G."""
    for comp in list(nx.connected_components(G)):
        if not any(G.nodes[n]["tipo"] == "municipio" for n in comp):
            G.remove_nodes_from(comp)
    cola = [n for n in G if G.nodes[n]["tipo"] != "municipio"]
    while cola:
        n = cola.pop()
        if n in G and G.nodes[n]["tipo"] != "municipio" and len(set(G[n]) - {n}) <= 1:
            vecinos = set(G[n]) - {n}
            G.remove_node(n)
            cola.extend(vecinos)


def contraer_cortas(G):
    """Funde los extremos de las aristas de menos de 1 km (intercambiadores y 'escaleras'
    entre dos calzadas). Nunca une dos ciudades y ningún grupo mide más de 1 km.
    Devuelve un multigrafo nuevo."""
    padre = {n: n for n in G}

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    es_ciudad = {n for n in G if G.nodes[n]["tipo"] == "municipio"}
    caja = {n: (G.nodes[n]["x"], G.nodes[n]["y"]) * 2 for n in G}
    for u, v, d in sorted(G.edges(data=True), key=lambda e: e[2]["longitud_m"]):
        if d["longitud_m"] >= c.CONTRAER_M:
            break
        ru, rv = raiz(u), raiz(v)
        if ru == rv or (ru in es_ciudad and rv in es_ciudad):
            continue
        a, b = caja[ru], caja[rv]
        union = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
        if math.hypot(union[2] - union[0], union[3] - union[1]) > c.CONTRAER_M:
            continue
        if rv in es_ciudad:
            ru, rv = rv, ru
        padre[rv], caja[ru] = ru, union
    grupos = {}
    for n in G:
        grupos.setdefault(raiz(n), []).append(n)
    H = nx.MultiGraph()
    for r, miembros in grupos.items():
        if r in es_ciudad:
            H.add_node(r, **G.nodes[r])
        else:
            H.add_node(r, tipo="cruce", x=float(np.mean([G.nodes[n]["x"] for n in miembros])),
                       y=float(np.mean([G.nodes[n]["y"] for n in miembros])))
    for u, v, d in G.edges(data=True):
        if raiz(u) != raiz(v):
            H.add_edge(raiz(u), raiz(v), **d)
    return H


def grafo_simple(M):
    """Entre dos nodos se deja solo la arista más barata. Aquí se asigna el costo.
    Recibe un multigrafo; devuelve un grafo simple."""
    D = nx.Graph()
    D.add_nodes_from(M.nodes(data=True))
    for u, v, d in M.edges(data=True):
        d["costo"] = costo_arista(d["longitud_m"])
        if u != v and (not D.has_edge(u, v) or d["costo"] < D.edges[u, v]["costo"]):
            D.add_edge(u, v, **d)
    return D


def red_detallada(seg, ciudades):
    """Recibe los segmentos limpios y las ciudades; devuelve la red detallada D (conexa)."""
    M = red_como_grafo(seg)
    conectar_ciudades(M, ciudades)
    for paso in (quitar_grado_2, podar, quitar_grado_2):
        paso(M)
    M = contraer_cortas(M)
    for paso in (podar, quitar_grado_2):
        paso(M)
    D = grafo_simple(M)
    km = sum(d["longitud_m"] for *_, d in D.edges(data=True)) / 1000
    anotar(f"[C] Red detallada: {D.number_of_nodes()} nodos, {D.number_of_edges()} aristas, "
           f"{km:,.0f} km, conexa = {nx.is_connected(D)}.")
    return D
