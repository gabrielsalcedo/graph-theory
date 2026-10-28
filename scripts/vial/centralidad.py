"""
Dos formas de medir la importancia de una arista.

  intermediacion()   C_B(e): pares de ciudades cuya ruta más barata usa e (Brandes)
  asignar_carga()    x_e: toneladas que pasan por e (asignación todo o nada), es decir,
                     la intermediación ponderada por la demanda
  tres_angulos()     posición (C_B), uso (x_e) y consecuencia (I) de cada arista
"""

import networkx as nx
import pandas as pd

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


def tres_angulos(t, cierres, top):
    """Recibe la tabla de intermediación y carga (t) y la de cierres por arista. Devuelve
    (tabla con los rangos de C_B, x_e e I por arista, líneas de resumen). Los puentes se
    dejan fuera de las comparaciones con I, porque su daño se mide en D, no en I."""
    m = t.merge(cierres[["id_arista", "sobrecosto_cop_anual", "sin_ruta_t", "grupo"]],
                on="id_arista")
    m["rango_sobrecosto"] = m["sobrecosto_cop_anual"].rank(ascending=False, method="min").astype(int)
    m = m[["id_arista", "nombre", "es_puente", "rango_intermediacion", "rango_carga",
           "rango_sobrecosto", "intermediacion", "carga_t", "sobrecosto_cop_anual",
           "sin_ruta_t", "grupo"]].sort_values("rango_sobrecosto")
    sin = m[~m["es_puente"]]
    primeras = lambda col: set(sin.nlargest(top, col)["nombre"])
    comunes = primeras("intermediacion") & primeras("carga_t") & primeras("sobrecosto_cop_anual")
    rho = lambda a, b: sin[a].corr(sin[b], method="spearman")
    lineas = [f"Spearman sin puentes: C_B vs I {rho('intermediacion', 'sobrecosto_cop_anual'):.2f}, "
              f"x_e vs I {rho('carga_t', 'sobrecosto_cop_anual'):.2f}",
              f"Aristas en el top {top} de las tres medidas a la vez: {len(comunes)} "
              f"({'; '.join(sorted(comunes))})",
              f"Top {top} comunes: C_B y x_e {len(primeras('intermediacion') & primeras('carga_t'))}, "
              f"x_e e I {len(primeras('carga_t') & primeras('sobrecosto_cop_anual'))}, "
              f"C_B e I {len(primeras('intermediacion') & primeras('sobrecosto_cop_anual'))}"]
    return m, lineas
