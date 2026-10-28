"""
Dos formas de medir la importancia de una arista.

  intermediacion()   C_B(e): pares de ciudades cuya ruta más barata usa e (Brandes)
  asignar_carga()    x_e: toneladas que pasan por e (asignación todo o nada), es decir,
                     la intermediación ponderada por la demanda
"""

import networkx as nx

from vial.rutas import camino, costos_desde


def intermediacion(G, ciudades):
    """C_B(e) entre las ciudades (algoritmo de Brandes, vía networkx), sin normalizar.
    Devuelve {(u, v): número de pares de ciudades}; si hay empates, cuentan en proporción."""
    return nx.edge_betweenness_centrality_subset(G, sources=ciudades, targets=ciudades,
                                                 normalized=False, weight="costo")


def asignar_carga(G, od, base=None):
    """Asignación todo o nada: las toneladas de cada pareja (o, d) viajan completas por su
    ruta más barata. x_e = suma de las toneladas de las parejas cuya ruta usa la arista e.
    Devuelve {arista ordenada: toneladas}."""
    base = base or costos_desde(G, od)
    x = {tuple(sorted(e)): 0.0 for e in G.edges()}
    for f in od.itertuples():
        nodos = camino(base[f.o][1], f.d)
        for e in zip(nodos[:-1], nodos[1:]):
            x[tuple(sorted(e))] += f.toneladas
    return x
