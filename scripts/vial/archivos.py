"""
Guardar y leer los grafos (outputs/grafo/).

  guardar_red_detallada()  D en .pkl (para el paso 03) y en CSV (para dibujarla)
  leer_red_detallada()     D desde el .pkl
  guardar_grafo()          G en vertices.csv y aristas.csv, tramos de INVIAS que recorre
                           y matriz O-D entre sus ciudades (od_ciudades.csv)
  cargar_grafo()           G = (V, E, w) desde los CSV
  cargar_od()              la matriz T de toneladas entre ciudades
"""

import pickle

import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely import wkt

import config as c
from vial.reporte import anotar


def guardar_red_detallada(D):
    """Guarda D completa (con geometría) en RED_DETALLADA_PKL y una versión simplificada
    para dibujar en red_detallada.csv."""
    c.GRAFO.mkdir(parents=True, exist_ok=True)
    with open(c.RED_DETALLADA_PKL, "wb") as f:
        pickle.dump(D, f)
    pd.DataFrame([{"u": u, "v": v, "km": d["longitud_m"] / 1000,
                   "geometria": d["geometry"].simplify(c.SIMPLIFICAR_SALIDA_D_M).wkt}
                  for u, v, d in D.edges(data=True)]).to_csv(c.GRAFO / "red_detallada.csv", index=False)


def leer_red_detallada():
    """Devuelve la red detallada D que guardó el paso 02."""
    if not c.RED_DETALLADA_PKL.exists():
        raise FileNotFoundError(f"No existe {c.RED_DETALLADA_PKL}: corra antes 02_red_detallada.py.")
    with open(c.RED_DETALLADA_PKL, "rb") as f:
        return pickle.load(f)


def guardar_grafo(G, mun, od, red):
    """Recibe G, las ciudades con su área (mun), la O-D entre municipios y la red de
    INVIAS. Escribe vertices.csv, aristas.csv, tramos.csv, tramos_por_arista.csv y
    od_ciudades.csv en outputs/grafo/."""
    c.GRAFO.mkdir(parents=True, exist_ok=True)
    ll = gpd.GeoSeries(gpd.points_from_xy([d["x"] for _, d in G.nodes(data=True)],
                                          [d["y"] for _, d in G.nodes(data=True)]),
                       crs=c.CRS_METRICO).to_crs(c.CRS_GEOGRAFICO)
    vert = pd.DataFrame([{"id": n, **d} for n, d in G.nodes(data=True)])
    vert["lon"], vert["lat"] = ll.x.round(5).values, ll.y.round(5).values
    vert = vert[["id", "tipo", "nombre", "cod_mpio", "departamento", "miembros", "ton_total",
                 "x", "y", "lon", "lat"]]
    vert.to_csv(c.GRAFO / "vertices.csv", index=False)

    juntar = lambda t: "; ".join(map(str, t))
    aris = pd.DataFrame([{"id_arista": d["id_arista"], "u": u, "v": v, "nombre": d["nombre"],
                          "km": d["longitud_m"] / 1000, "costo": d["costo"],
                          "codigos_via": juntar(d["codigos_via"]),
                          "ids_tramo": juntar(d["ids_tramo"]), "sectores": juntar(d["sectores"]),
                          "geometria": d["geometry"].simplify(c.SIMPLIFICAR_SALIDA_G_M).wkt}
                         for u, v, d in G.edges(data=True)]).sort_values("id_arista")
    aris.to_csv(c.GRAFO / "aristas.csv", index=False)

    # tramos de INVIAS que recorre el grafo (para simular el cierre de un tramo completo)
    # Para cada arista y cada tramo que toca: cuántos km de la arista recorre el tramo.
    # (Al entrar a una ciudad, varios corredores comparten unos metros del mismo tramo; con
    # esto un cierre solo quita las aristas que el tramo recorre de verdad.)
    usados = {int(t) for _, _, d in G.edges(data=True) for t in d["ids_tramo"]}
    t = red[red["id_tramo"].isin(usados)].to_crs(c.CRS_METRICO).set_index("id_tramo")
    traslape = [{"id_tramo": i, "id_arista": d["id_arista"],
                 "km_en_arista": round(d["geometry"].intersection(
                     t.geometry[i].buffer(c.DUPLICADO_M)).length / 1000, 2)}
                for _, _, d in G.edges(data=True) for i in d["ids_tramo"]]
    pd.DataFrame(traslape).to_csv(c.GRAFO / "tramos_por_arista.csv", index=False)
    t = t.assign(km=t.length / 1000).drop(columns="geometry").reset_index()
    t.round({"km": 1}).sort_values("id_tramo").to_csv(c.GRAFO / "tramos.csv", index=False)

    # matriz O-D agregada a las 25 ciudades (sin la carga interna de cada área)
    rep = dict(zip(mun["cod_mpio"], mun["representante"]))
    nodo = {d["cod_mpio"]: n for n, d in G.nodes(data=True) if d["tipo"] == "ciudad"}
    odc = od.assign(o=od["o"].map(rep).map(nodo), d=od["d"].map(rep).map(nodo)).dropna(subset=["o", "d"])
    odc = odc[odc["o"] != odc["d"]].groupby(["o", "d"], as_index=False)[["toneladas", "viajes"]].sum()
    odc.to_csv(c.GRAFO / "od_ciudades.csv", index=False)
    anotar(f"[E] Carga O-D entre las ciudades del grafo: {odc['toneladas'].sum():,.0f} t "
           f"({100 * odc['toneladas'].sum() / od['toneladas'].sum():.1f} % del total) en {len(odc)} pares.")


def cargar_grafo():
    """Lee vertices.csv y aristas.csv y devuelve el grafo no dirigido de NetworkX."""
    if not (c.GRAFO / "aristas.csv").exists():
        raise FileNotFoundError(f"No existe {c.GRAFO / 'aristas.csv'}: corra antes 03_grafo_analisis.py.")
    vertices = pd.read_csv(c.GRAFO / "vertices.csv", dtype={"cod_mpio": str})
    aristas = pd.read_csv(c.GRAFO / "aristas.csv", dtype={"codigos_via": str})
    G = nx.Graph()
    for v in vertices.itertuples():
        G.add_node(v.id, tipo=v.tipo, nombre=v.nombre, x=v.x, y=v.y, cod_mpio=v.cod_mpio)
    for a in aristas.itertuples():
        G.add_edge(a.u, a.v, id_arista=a.id_arista, nombre=a.nombre, km=a.km, costo=a.costo,
                   codigos_via=str(a.codigos_via), geometry=wkt.loads(a.geometria),
                   ids_tramo=[int(t) for t in str(a.ids_tramo).split("; ")])
    return G


def cargar_od():
    """Matriz T: toneladas al año de cada ciudad o a cada ciudad d (solo pares con carga)."""
    return pd.read_csv(c.GRAFO / "od_ciudades.csv")
