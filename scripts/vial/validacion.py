"""
Descripción estructural del grafo de análisis y validación contra el RNDC.

  propiedades()    orden, tamaño, grados, conexidad, planaridad, diámetro, κ(G), λ(G),
                   puentes y vértices de corte (Tarjan, vía networkx)
  frente_a_rndc()  km de la ruta más corta del grafo vs km por viaje del RNDC
"""

import networkx as nx
import pandas as pd

import config as c
from vial.ciudades import lista_ciudades, nombre_corto


def propiedades(G):
    """Devuelve las líneas de texto con las propiedades de G."""
    grados = [g for _, g in G.degree()]
    puentes = list(nx.bridges(G))                      # Tarjan: O(n + m)
    corte = sorted(nx.articulation_points(G), key=lambda n: G.nodes[n]["nombre"])
    n_ciudades = len(lista_ciudades(G))
    return [
        "1. PROPIEDADES DEL GRAFO",
        f"   Vértices: {G.number_of_nodes()}   Aristas: {G.number_of_edges()}",
        f"   Ciudades: {n_ciudades}   Cruces: {G.number_of_nodes() - n_ciudades}",
        f"   Grado medio: {2 * G.number_of_edges() / G.number_of_nodes():.2f}   "
        f"Grado mínimo: {min(grados)}   Grado máximo: {max(grados)}",
        f"   Conexo: {nx.is_connected(G)}   Planar: {nx.check_planarity(G)[0]}",
        f"   Diámetro (en aristas): {nx.diameter(G)}",
        f"   Conectividad de vértices κ(G): {nx.node_connectivity(G)}   "
        f"de aristas λ(G): {nx.edge_connectivity(G)}",
        f"   Puentes ({len(puentes)}): "
        + "; ".join(f"{nombre_corto(G, u)} – {nombre_corto(G, v)}" for u, v in puentes),
        f"   Vértices de corte ({len(corte)}): " + "; ".join(nombre_corto(G, n) for n in corte),
        "",
    ]


def frente_a_rndc(G):
    """En los N_PARES_VALIDACION pares O-D con más toneladas compara los km del grafo con
    los km por viaje del RNDC. Escribe validacion_pares_rndc.csv y devuelve las líneas
    del resumen."""
    od = pd.read_csv(c.MATRIZ_OD, dtype={"ORIGEN": str, "DESTINO": str})
    nodo = {G.nodes[n]["cod_mpio"]: n for n in lista_ciudades(G)}
    od = od[od["ORIGEN"].isin(nodo) & od["DESTINO"].isin(nodo) & od["KM_POR_VIAJE"].notna()]
    od = od.nlargest(c.N_PARES_VALIDACION, "TONELADAS").copy()
    km = {o: nx.single_source_dijkstra_path_length(G, nodo[o], weight="km")
          for o in od["ORIGEN"].unique()}
    od["km_grafo"] = [km[o][nodo[d]] for o, d in zip(od["ORIGEN"], od["DESTINO"])]
    od["razon"] = od["km_grafo"] / od["KM_POR_VIAJE"]
    ponderada = (od["km_grafo"] * od["TONELADAS"]).sum() / (od["KM_POR_VIAJE"] * od["TONELADAS"]).sum()
    od[["ORIGEN", "DESTINO", "NOMBRE_ORIGEN", "NOMBRE_DESTINO", "TONELADAS", "KM_POR_VIAJE",
        "km_grafo", "razon"]].round(3).to_csv(c.RESULTADOS / "validacion_pares_rndc.csv", index=False)
    lineas = [
        f"2. GRAFO FRENTE AL RNDC ({len(od)} pares O-D con más toneladas)",
        f"   Razón km grafo / km reportados: ponderada por toneladas {ponderada:.3f}   "
        f"mediana {od['razon'].median():.3f}   "
        f"p10-p90 {od['razon'].quantile(0.1):.2f}-{od['razon'].quantile(0.9):.2f}",
    ]
    for f in od.head(5).itertuples():
        lineas.append(f"   {f.NOMBRE_ORIGEN} -> {f.NOMBRE_DESTINO}: "
                      f"{f.km_grafo:,.0f} km (RNDC {f.KM_POR_VIAJE:,.0f} km)")
    return lineas
