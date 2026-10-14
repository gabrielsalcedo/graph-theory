"""
PASO 4 — Propiedades y validación del grafo de análisis (las cifras del reporte).

Entradas: outputs/resultados/grafo.pkl y grafo_detallado.pkl (paso 2),
          data/final/matriz_od.csv

Calcula:
  1. Propiedades del grafo: vértices, aristas, grado medio, diámetro, conexidad,
     planaridad, puentes, vértices de corte, conectividad κ(G) y λ(G).
  2. Distancias del grafo de análisis frente a la red detallada (¿cuánto distorsiona
     resumir la red?).
  3. Distancias del grafo frente a los km por viaje que reporta el RNDC, en los 300 pares
     origen-destino con más toneladas.

Salidas en outputs/resultados/:
  validacion.txt             resumen con todas las cifras
  validacion_pares_rndc.csv  los 300 pares: km del grafo vs km del RNDC
"""

import networkx as nx
import numpy as np
import pandas as pd

import config
from vial.archivos import cargar_detallado, cargar_grafo

N_PARES_RNDC = 300


def _km(u, v, d):
    return d["longitud_m"] / 1000


def propiedades(G):
    grados = dict(G.degree())
    puentes = list(nx.bridges(G))
    corte = sorted(nx.articulation_points(G), key=lambda n: G.nodes[n]["nombre"])
    nombre = lambda n: G.nodes[n]["nombre"].split(",")[0].title()
    return [
        "1. PROPIEDADES DEL GRAFO",
        f"   Vértices: {G.number_of_nodes()}   Aristas: {G.number_of_edges()}",
        f"   Ciudades: {sum(d['tipo'] == 'municipio' for _, d in G.nodes(data=True))}   "
        f"Cruces: {sum(d['tipo'] == 'cruce' for _, d in G.nodes(data=True))}",
        f"   Grado medio: {2 * G.number_of_edges() / G.number_of_nodes():.2f}   "
        f"Grado mínimo: {min(grados.values())}   Grado máximo: {max(grados.values())}",
        f"   Conexo: {nx.is_connected(G)}   Planar: {nx.check_planarity(G)[0]}",
        f"   Diámetro (en aristas): {nx.diameter(G)}",
        f"   Conectividad de vértices κ(G): {nx.node_connectivity(G)}   "
        f"de aristas λ(G): {nx.edge_connectivity(G)}",
        f"   Puentes ({len(puentes)}): " + "; ".join(f"{nombre(u)} – {nombre(v)}" for u, v in puentes),
        f"   Vértices de corte ({len(corte)}): " + "; ".join(nombre(n) for n in corte),
        "",
    ]


def frente_a_detallada(G, D, ciudades):
    r = []
    for s in ciudades:
        a = nx.single_source_dijkstra_path_length(G, s, weight="costo")
        b = nx.single_source_dijkstra_path_length(D, s, weight="costo")
        r += [a[t] / b[t] for t in ciudades if t != s and t in a and t in b]
    r = np.array(r)
    return [
        "2. GRAFO DE ANÁLISIS FRENTE A LA RED DETALLADA (costo de la ruta mínima)",
        f"   Pares de ciudades: {len(r)}",
        f"   Razón media: {r.mean():.3f}   máxima: {r.max():.3f}   "
        f"pares exactos (razón = 1): {100 * np.mean(r < 1.0001):.1f} %",
        "",
    ]


def frente_a_rndc(G, ciudades):
    od = pd.read_csv(config.ARCHIVO_OD, dtype={"ORIGEN": str, "DESTINO": str})
    nodo = {G.nodes[n]["cod_mpio"]: n for n in ciudades}
    od = od[od["ORIGEN"].isin(nodo) & od["DESTINO"].isin(nodo) & od["KM_POR_VIAJE"].notna()]
    od = od.nlargest(N_PARES_RNDC, "TONELADAS").copy()
    km = {o: nx.single_source_dijkstra_path_length(G, nodo[o], weight=_km)
          for o in od["ORIGEN"].unique()}
    od["km_grafo"] = [km[o][nodo[d]] for o, d in zip(od["ORIGEN"], od["DESTINO"])]
    od["razon"] = od["km_grafo"] / od["KM_POR_VIAJE"]
    w = od["TONELADAS"]
    ponderada = (od["km_grafo"] * w).sum() / (od["KM_POR_VIAJE"] * w).sum()
    lineas = [
        f"3. GRAFO DE ANÁLISIS FRENTE AL RNDC ({len(od)} pares O-D con más toneladas)",
        f"   Razón km grafo / km reportados: ponderada por toneladas {ponderada:.3f}   "
        f"mediana {od['razon'].median():.3f}   "
        f"p10-p90 {od['razon'].quantile(0.1):.2f}-{od['razon'].quantile(0.9):.2f}",
    ]
    for f in od.head(5).itertuples():
        lineas.append(f"   {f.NOMBRE_ORIGEN} -> {f.NOMBRE_DESTINO}: "
                      f"{f.km_grafo:,.0f} km (RNDC {f.KM_POR_VIAJE:,.0f} km)")
    od[["ORIGEN", "DESTINO", "NOMBRE_ORIGEN", "NOMBRE_DESTINO", "TONELADAS",
        "KM_POR_VIAJE", "km_grafo", "razon"]].round(3).to_csv(
        config.CARPETA_SALIDA / "validacion_pares_rndc.csv", index=False)
    return lineas


def main():
    G = cargar_grafo()
    D = cargar_detallado()
    ciudades = [n for n, d in G.nodes(data=True) if d.get("tipo") == "municipio"]
    lineas = propiedades(G) + frente_a_detallada(G, D, ciudades) + frente_a_rndc(G, ciudades)
    texto = "\n".join(lineas)
    (config.CARPETA_SALIDA / "validacion.txt").write_text(texto, encoding="utf-8")
    print(texto)
    print(f"\nGuardado en {config.CARPETA_SALIDA / 'validacion.txt'}")


if __name__ == "__main__":
    main()
