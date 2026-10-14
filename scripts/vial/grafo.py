"""Red detallada: construcción del grafo, conexión de municipios, simplificación y poda.

Decisiones de modelado
- NO DIRIGIDO: la red INVIAS no trae sentido de circulación útil a esta escala y las
  vías troncales son de doble sentido. La matriz O-D sí es dirigida; eso se maneja en la
  asignación, no en el grafo.
- MULTIGRAFO al construir, porque dos vías distintas pueden unir los mismos dos cruces.
  Al final se pasa a grafo simple conservando la arista de menor costo y anotando cuántas
  paralelas había ('n_paralelas'). OJO: una arista con n_paralelas > 1 NUNCA es puente
  en la red real, aunque en el grafo simple lo parezca; el diagnóstico debe mirarlo.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import substring

import config
from . import costo


# ---------------------------------------------------------------------------
# Atributos de arista
# ---------------------------------------------------------------------------
def _atributos_segmento(fila) -> dict:
    largo = fila.geometry.length
    sup = fila.get("superficie")
    return {
        "tipo": "via",
        "longitud_m": largo,
        "ids_tramo": (int(fila["id_tramo"]),),
        "codigos_via": (fila["codigo_via"],) if isinstance(fila["codigo_via"], str) else (),
        "rutas": (fila["ruta"],) if isinstance(fila.get("ruta"), str) else (),
        "nombres": (fila["nombre_tramo"],) if isinstance(fila["nombre_tramo"], str) else (),
        "superficie_afirmado_frac": 1.0 if sup == config.SUPERFICIE_AFIRMADO else 0.0,
        "superficie_desconocida_m": largo if not isinstance(sup, str) else 0.0,
        "calzada": fila["calzada"] if isinstance(fila["calzada"], str) else "?",
        "concesiones": (fila["concesion"],) if isinstance(fila["concesion"], str) else (),
        "geometry": fila.geometry,
    }


def _unicos(*tuplas):
    vistos = []
    for t in tuplas:
        for x in t:
            if x not in vistos:
                vistos.append(x)
    return tuple(vistos)


def _fusionar(a: dict, b: dict, geom: LineString) -> dict:
    la, lb = a["longitud_m"], b["longitud_m"]
    return {
        "tipo": "via",
        "longitud_m": la + lb,
        "ids_tramo": _unicos(a["ids_tramo"], b["ids_tramo"]),
        "codigos_via": _unicos(a["codigos_via"], b["codigos_via"]),
        "rutas": _unicos(a.get("rutas", ()), b.get("rutas", ())),
        "nombres": _unicos(a["nombres"], b["nombres"]),
        "superficie_afirmado_frac": (a["superficie_afirmado_frac"] * la
                                     + b["superficie_afirmado_frac"] * lb) / (la + lb),
        "superficie_desconocida_m": a["superficie_desconocida_m"] + b["superficie_desconocida_m"],
        "calzada": a["calzada"] if a["calzada"] == b["calzada"] else "mixta",
        "concesiones": _unicos(a["concesiones"], b["concesiones"]),
        "geometry": geom,
    }


def _orientar(geom: LineString, desde_xy) -> LineString:
    """Devuelve la línea orientada para que empiece en el extremo más cercano a desde_xy."""
    c = list(geom.coords)
    d0 = (c[0][0] - desde_xy[0]) ** 2 + (c[0][1] - desde_xy[1]) ** 2
    d1 = (c[-1][0] - desde_xy[0]) ** 2 + (c[-1][1] - desde_xy[1]) ** 2
    return geom if d0 <= d1 else LineString(c[::-1])


# ---------------------------------------------------------------------------
# 4. Construcción
# ---------------------------------------------------------------------------
def construir(segmentos: gpd.GeoDataFrame) -> nx.MultiGraph:
    G = nx.MultiGraph(crs=str(segmentos.crs))
    for fila in segmentos.itertuples(index=False):
        fila = fila._asdict()
        g = fila["geometry"]
        u, v = f"n{fila['u']}", f"n{fila['v']}"
        for nodo, xy in ((u, g.coords[0]), (v, g.coords[-1])):
            if nodo not in G:
                G.add_node(nodo, x=xy[0], y=xy[1], tipo="cruce")
        G.add_edge(u, v, **_atributos_segmento(pd.Series(fila)))
    return G


# ---------------------------------------------------------------------------
# 6. Conexión de municipios (antes de simplificar, para no perder precisión)
# ---------------------------------------------------------------------------
def conectar_municipios(G: nx.MultiGraph, municipios: gpd.GeoDataFrame, reporte: list):
    """Une cada cabecera al PUNTO más cercano de la red (no al nodo más cercano: los
    nodos pueden estar a decenas de km, mientras la vía pasa a 1 km). Si ese punto cae
    en el interior de una arista, la arista se parte allí."""
    aristas = [(u, v, k, d["geometry"]) for u, v, k, d in G.edges(keys=True, data=True)]
    serie = gpd.GeoSeries([a[3] for a in aristas], crs=config.CRS_METRICO)
    idx_m, idx_a = serie.sindex.nearest(municipios.geometry, return_all=False)
    asignacion = {}
    estado = []

    # Travesías urbanas: INVIAS no digitaliza las calles dentro de las ciudades, así que
    # las vías que llegan a una ciudad pueden quedar sueltas (otra componente) o unidas
    # solo por un rodeo largo. Si la opción está activa, la ciudad se conecta al punto más
    # cercano de CADA ruta nacional (y de cada componente) que pase dentro de su radio;
    # el nodo ciudad hace de cruce urbano entre las vías que llegan a ella.
    grupo_de_arista = None
    if config.CONECTAR_TODAS_LAS_RUTAS_CERCANAS:
        etiqueta = {}
        for i, c in enumerate(nx.connected_components(G)):
            for n in c:
                etiqueta[n] = i
        grupo_de_arista = [(etiqueta[u], (G.edges[u, v, k].get("rutas") or ("?",))[0])
                           for u, v, k, _ in aristas]

    for im, ia in zip(idx_m, idx_a):
        m = municipios.iloc[im]
        radio = config.RADIO_CONEXION_ESPECIAL_M.get(m["cod_mpio"], config.DISTANCIA_MAX_CONEXION_M)
        dist = aristas[ia][3].distance(m.geometry)
        conectado = dist <= radio
        elegidas = [ia]
        if conectado and grupo_de_arista is not None:
            cerca = serie.sindex.query(m.geometry, predicate="dwithin", distance=radio)
            mejor = {}
            for j in cerca:
                g, d = grupo_de_arista[j], aristas[j][3].distance(m.geometry)
                if g not in mejor or d < mejor[g][0]:
                    mejor[g] = (d, j)
            elegidas = [j for _, j in mejor.values()]
        estado.append({"cod_mpio": m["cod_mpio"], "nombre": m["nombre"],
                       "departamento": m["departamento"], "distancia_red_m": round(dist, 1),
                       "conectado": conectado,
                       "vias_unidas": len(elegidas) if conectado else 0})
        if conectado:
            for j in elegidas:
                asignacion.setdefault(j, []).append((aristas[j][3].project(m.geometry), m))

    for ia, lista in asignacion.items():
        u, v, k, g = aristas[ia]
        datos = G.edges[u, v, k]
        g = _orientar(g, (G.nodes[u]["x"], G.nodes[u]["y"]))
        lista.sort(key=lambda t: t[0])
        cortes, anclas = [], []
        for s, m in lista:
            if s < 1.0:
                anclas.append((u, m))
            elif s > g.length - 1.0:
                anclas.append((v, m))
            else:
                cortes.append(s)
                anclas.append((None, m, s))
        cortes = sorted(set(cortes))
        if cortes:
            G.remove_edge(u, v, k)
            limites = [0.0] + cortes + [g.length]
            nodos = [u] + [f"p{ia}_{i}" for i in range(len(cortes))] + [v]
            for i, s in enumerate(cortes):
                p = g.interpolate(s)
                G.add_node(nodos[i + 1], x=p.x, y=p.y, tipo="anclaje")
            for i in range(len(limites) - 1):
                pieza = substring(g, limites[i], limites[i + 1])
                d = dict(datos)
                d["longitud_m"] = pieza.length
                d["superficie_desconocida_m"] = datos["superficie_desconocida_m"] * pieza.length / g.length
                d["geometry"] = pieza
                G.add_edge(nodos[i], nodos[i + 1], **d)
            posicion = dict(zip(cortes, nodos[1:-1]))
        for a in anclas:
            if a[0] is None:
                _, m, s = a
                ancla = posicion[s]
            else:
                ancla, m = a
            nodo_m = f"M{m['cod_mpio']}"
            G.add_node(nodo_m, x=m.geometry.x, y=m.geometry.y, tipo="municipio",
                       cod_mpio=m["cod_mpio"], nombre=m["nombre"], departamento=m["departamento"],
                       ton_total=float(m["ton_total"]) if "ton_total" in m else 0.0)
            xa, ya = G.nodes[ancla]["x"], G.nodes[ancla]["y"]
            recta = LineString([(m.geometry.x, m.geometry.y), (xa, ya)])
            G.add_edge(nodo_m, ancla, tipo="conector",
                       longitud_m=recta.length * config.FACTOR_SINUOSIDAD_CONECTOR,
                       ids_tramo=(), codigos_via=(), rutas=(), nombres=("conector " + m["nombre"],),
                       superficie_afirmado_frac=0.0, superficie_desconocida_m=0.0,
                       calzada="-", concesiones=(), geometry=recta)

    estado = pd.DataFrame(estado)
    no = estado[~estado["conectado"]]
    reporte.append(f"[municipios] {estado['conectado'].sum()} conectados; {len(no)} sin conectar "
                   f"(distancia > {config.DISTANCIA_MAX_CONEXION_M / 1000:.0f} km).")
    if grupo_de_arista is not None:
        varias = estado[estado["vias_unidas"] > 1]
        reporte.append(f"[municipios] {len(varias)} ciudades unen varias rutas o componentes "
                       f"(travesía urbana; entre paréntesis, cuántas): "
                       + ", ".join(f"{r.nombre} ({r.vias_unidas})" for r in varias.itertuples()))
    return estado


# ---------------------------------------------------------------------------
# 5. Simplificación: contraer vértices de grado 2
# ---------------------------------------------------------------------------
def simplificar(G: nx.MultiGraph, reporte: list) -> nx.MultiGraph:
    G = G.copy()
    n0, m0 = G.number_of_nodes(), G.number_of_edges()
    cambio = True
    while cambio:
        cambio = False
        for n in list(G.nodes):
            if n not in G or G.nodes[n]["tipo"] == "municipio" or G.degree(n) != 2:
                continue
            ed = list(G.edges(n, keys=True, data=True))
            if len(ed) != 2:          # un lazo cuenta grado 2 con una sola arista
                continue
            (_, a, ka, da), (_, b, kb, db) = ed
            if a == b or a == n or b == n or da["tipo"] != "via" or db["tipo"] != "via":
                continue
            xy = lambda q: (G.nodes[q]["x"], G.nodes[q]["y"])
            ga = _orientar(da["geometry"], xy(a))   # a -> n
            gb = _orientar(db["geometry"], xy(n))   # n -> b
            geom = LineString(list(ga.coords) + list(gb.coords)[1:])
            G.remove_node(n)
            G.add_edge(a, b, **_fusionar(da, db, geom))
            cambio = True
    reporte.append(f"[simplificación] {n0} nodos y {m0} aristas -> "
                   f"{G.number_of_nodes()} nodos y {G.number_of_edges()} aristas.")
    return G


# ---------------------------------------------------------------------------
# 5b. Poda: quitar lo que ninguna ruta entre ciudades puede usar
# ---------------------------------------------------------------------------
def podar(G: nx.MultiGraph, reporte: list) -> nx.MultiGraph:
    """1) Elimina las componentes conexas sin ninguna ciudad.
    2) Elimina, repetidamente, los cruces con UN solo vecino (ramales sin salida).
    Una ruta de costo mínimo entre dos ciudades nunca entra a un ramal sin salida (tendría
    que devolverse por la misma arista), así que la poda no cambia ninguna ruta, ningún
    desvío ni la intermediación entre ciudades; solo hace el grafo más pequeño y legible."""
    G = G.copy()
    n0, m0 = G.number_of_nodes(), G.number_of_edges()
    km0 = sum(d["longitud_m"] for *_, d in G.edges(data=True)) / 1000
    for c in list(nx.connected_components(G)):
        if not any(G.nodes[n].get("tipo") == "municipio" for n in c):
            G.remove_nodes_from(c)
    cola = [n for n in G if G.nodes[n]["tipo"] != "municipio"]
    while cola:
        n = cola.pop()
        if n in G and G.nodes[n]["tipo"] != "municipio" and len(set(G.neighbors(n)) - {n}) <= 1:
            vecinos = set(G.neighbors(n)) - {n}
            G.remove_node(n)
            cola.extend(vecinos)
    km1 = sum(d["longitud_m"] for *_, d in G.edges(data=True)) / 1000
    reporte.append(f"[poda] Componentes sin ciudades y ramales sin salida: {n0} nodos y {m0} aristas "
                   f"-> {G.number_of_nodes()} nodos y {G.number_of_edges()} aristas "
                   f"({km0:,.0f} km -> {km1:,.0f} km).")
    return G


# ---------------------------------------------------------------------------
# 5c. Contracción de aristas cortas (intercambiadores y dobles calzadas)
# ---------------------------------------------------------------------------
def contraer_cortas(G: nx.MultiGraph, umbral_m: float, reporte: list) -> nx.MultiGraph:
    """Contrae (funde en un nodo) los extremos de cada arista vial más corta que umbral_m.
    Las dobles calzadas digitalizadas como dos líneas y los intercambiadores generan muchos
    nodos a pocos metros entre sí que no aportan nada a escala nacional.
    Reglas: nunca se funden dos ciudades; si el grupo tiene una ciudad, la ciudad lo
    representa; si no, el nodo queda en el centroide del grupo."""
    padre = {n: n for n in G}

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    ciudad = {n: n for n in G if G.nodes[n]["tipo"] == "municipio"}   # ciudad del grupo
    # caja (xmin, ymin, xmax, ymax) de cada grupo: un grupo nunca puede medir más que el
    # umbral; si no, una doble calzada larga hecha de tramos cortos colapsaría en un punto
    caja = {n: (G.nodes[n]["x"], G.nodes[n]["y"], G.nodes[n]["x"], G.nodes[n]["y"]) for n in G}
    for u, v, d in sorted(G.edges(data=True), key=lambda e: e[2]["longitud_m"]):
        if d["longitud_m"] >= umbral_m or d["tipo"] != "via" and not (
                G.nodes[u]["tipo"] == "municipio" or G.nodes[v]["tipo"] == "municipio"):
            continue
        ru, rv = raiz(u), raiz(v)
        if ru == rv or (ru in ciudad and rv in ciudad):
            continue
        a, b = caja[ru], caja[rv]
        union = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
        if np.hypot(union[2] - union[0], union[3] - union[1]) > umbral_m:
            continue
        if rv in ciudad:
            ru, rv = rv, ru
        padre[rv] = ru
        caja[ru] = union

    grupos = {}
    for n in G:
        grupos.setdefault(raiz(n), []).append(n)
    H = nx.MultiGraph(**G.graph)
    for r, miembros in grupos.items():
        if r in ciudad:
            H.add_node(r, **G.nodes[r])
        else:
            H.add_node(r, tipo="cruce",
                       x=float(np.mean([G.nodes[n]["x"] for n in miembros])),
                       y=float(np.mean([G.nodes[n]["y"] for n in miembros])))
    for u, v, d in G.edges(data=True):
        ru, rv = raiz(u), raiz(v)
        if ru != rv:
            H.add_edge(ru, rv, **d)
    reporte.append(f"[contracción] Aristas < {umbral_m / 1000:g} km contraídas (ningún grupo "
                   f"mide más de {umbral_m / 1000:g} km): {G.number_of_nodes()} nodos "
                   f"y {G.number_of_edges()} aristas -> {H.number_of_nodes()} nodos y "
                   f"{H.number_of_edges()} aristas.")
    return H


def a_grafo_simple(M: nx.MultiGraph) -> nx.Graph:
    """Conserva la arista de menor costo entre cada par de nodos."""
    costo.asignar_costos(M)
    G = nx.Graph(**M.graph)
    G.add_nodes_from(M.nodes(data=True))
    for u, v, d in M.edges(data=True):
        if u == v:
            continue
        if G.has_edge(u, v):
            G.edges[u, v]["n_paralelas"] += 1
            if d["costo"] < G.edges[u, v]["costo"]:
                n = G.edges[u, v]["n_paralelas"]
                G.edges[u, v].update(d)
                G.edges[u, v]["n_paralelas"] = n
        else:
            G.add_edge(u, v, **d, n_paralelas=1)
    for i, (u, v, d) in enumerate(G.edges(data=True), start=1):
        d["id_arista"] = f"a{i:05d}"
    return G


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def municipios_en_grafo(G) -> pd.DataFrame:
    filas = [{"nodo": n, **{k: d[k] for k in ("cod_mpio", "nombre", "departamento")}}
             for n, d in G.nodes(data=True) if d.get("tipo") == "municipio"]
    return pd.DataFrame(filas).sort_values(["nombre", "departamento"]).reset_index(drop=True)


def aristas_gdf(G) -> gpd.GeoDataFrame:
    filas = []
    for u, v, d in G.edges(data=True):
        f = {"u": u, "v": v}
        for k, val in d.items():
            f[k] = "; ".join(map(str, val)) if isinstance(val, tuple) else val
        filas.append(f)
    return gpd.GeoDataFrame(filas, geometry="geometry", crs=G.graph.get("crs"))
