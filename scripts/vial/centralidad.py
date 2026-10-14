"""Intermediación de aristas (edge betweenness, algoritmo de Brandes 2001/2008).

Intermediación de una arista e:
    B(e) = Σ_{s<t}  σ_st(e) / σ_st
σ_st = número de rutas de costo mínimo entre s y t; σ_st(e) = cuántas de ellas usan e.
Con costos reales casi nunca hay empates, así que B(e) ≈ número de pares (s, t) cuya ruta
más barata pasa por e.

Dos versiones:
- 'municipios': s y t recorren SOLO las cabeceras municipales. Es la versión con sentido
  económico: los nodos de cruce son artificiales (dependen de cómo se digitalizó la red)
  y no generan ni atraen carga.
- 'todos': s y t recorren todos los nodos (definición clásica). Se reporta para comparar.

LIMITACIÓN (importante para el documento): una intermediación alta indica que muchas rutas
óptimas PASAN por la arista, no que cerrarla sea costoso. Si hay un desvío casi igual de
barato, la arista es central pero poco vulnerable. La criticidad en el sentido de
Jenelius et al. (2006) exige simular el cierre de la arista. Además, esta intermediación
trata todos los pares por igual: no pondera por toneladas del RNDC.
"""

import networkx as nx
import pandas as pd


def intermediacion_aristas(G, peso="costo", version="municipios"):
    """Devuelve un DataFrame con la intermediación de cada arista vial."""
    municipios = [n for n, d in G.nodes(data=True) if d.get("tipo") == "municipio"]
    if version == "municipios":
        b = nx.edge_betweenness_centrality_subset(
            G, sources=municipios, targets=municipios, normalized=False, weight=peso)
        n_ref = len(municipios)
    else:
        b = nx.edge_betweenness_centrality(G, normalized=False, weight=peso)
        n_ref = G.number_of_nodes()
    pares = n_ref * (n_ref - 1) / 2

    puentes = {frozenset(e) for e in nx.bridges(G)}
    filas = []
    for (u, v), valor in b.items():
        d = G.edges[u, v]
        filas.append({
            "id_arista": d["id_arista"],
            "u": u, "v": v,
            "tipo": d["tipo"],
            "codigos_via": ", ".join(d["codigos_via"]),
            "nombres": " / ".join(d["nombres"]),
            "km": round(d["longitud_m"] / 1000, 2),
            "costo": round(d[peso], 3),
            "intermediacion": valor,
            "fraccion_pares": valor / pares if pares else 0.0,
            "es_puente": frozenset((u, v)) in puentes,
            "n_paralelas": d.get("n_paralelas", 1),
        })
    return pd.DataFrame(filas)


def ranking_criticas(G, peso="costo", top=15):
    """Ranking de aristas VIALES (sin conectores) por intermediación entre municipios.
    Incluye la versión clásica para comparar."""
    m = intermediacion_aristas(G, peso, "municipios")
    t = intermediacion_aristas(G, peso, "todos")[["id_arista", "intermediacion"]]
    m = m.merge(t.rename(columns={"intermediacion": "intermediacion_todos"}), on="id_arista")
    m = m.rename(columns={"intermediacion": "intermediacion_municipios"})
    viales = m[m["tipo"] == "via"].sort_values("intermediacion_municipios", ascending=False)
    viales.insert(0, "rango", range(1, len(viales) + 1))
    correlacion = viales["intermediacion_municipios"].corr(
        viales["intermediacion_todos"], method="spearman")
    return viales.reset_index(drop=True), viales.head(top).reset_index(drop=True), correlacion


def ranking_por_via(viales: pd.DataFrame, top=15) -> pd.DataFrame:
    """Agrupa por código de vía. Un corredor queda partido en varias aristas (en cada
    cruce y en cada punto donde se conecta un municipio) y esas piezas tienen casi la misma
    intermediación; agrupar evita que un solo corredor ocupe todo el ranking."""
    v = viales.assign(codigo=viales["codigos_via"].str.split(", ")).explode("codigo")
    v = v[v["codigo"].fillna("") != ""]
    g = v.groupby("codigo").agg(
        nombre=("nombres", lambda x: x.value_counts().index[0]),
        intermediacion_max=("intermediacion_municipios", "max"),
        fraccion_pares_max=("fraccion_pares", "max"),
        km_total=("km", "sum"),
        aristas=("id_arista", "nunique"),
        algun_puente=("es_puente", "any"),
    ).sort_values("intermediacion_max", ascending=False).reset_index()
    g.insert(0, "rango", range(1, len(g) + 1))
    return g.head(top)
