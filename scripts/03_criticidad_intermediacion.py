"""
PASO 3 — Corredores críticos según la INTERMEDIACIÓN de aristas (algoritmo de Brandes).

Entrada : outputs/resultados/grafo.pkl (paso 2)
Salidas : outputs/resultados/
  intermediacion_aristas.csv    todas las aristas con su intermediación
  criticas_intermediacion.csv   las TOP_ARISTAS_CRITICAS primeras
  criticas_por_via.csv          el mismo ranking agrupado por código de vía
  mapa_intermediacion.png       red coloreada por intermediación, top numeradas
  barras_intermediacion.png     ranking del top

Lectura: 'fraccion_pares' = proporción de pares de ciudades cuya ruta más barata pasa
por la arista. Alta intermediación NO implica que el cierre sea costoso; eso lo mide la
simulación de cierres (ver vial/centralidad.py).
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize

import config
from vial.archivos import cargar_grafo
from vial import centralidad
from vial.costo import UNIDAD_COSTO

# Rampa secuencial de un solo tono (azul claro -> oscuro)
RAMPA = LinearSegmentedColormap.from_list(
    "azul", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
GRIS_RED = "#c9c8c2"
NARANJA = "#eb6834"
TINTA = "#2b2b29"
TINTA_SUAVE = "#6b6a65"


def _segmentos(G, aristas):
    return [np.array(G.edges[u, v]["geometry"].coords) / 1000 for u, v in aristas]


def mapa(G, tabla, top, ruta_png):
    fig, ax = plt.subplots(figsize=(8.5, 10.5))
    todas = [(u, v) for u, v in G.edges()]
    ax.add_collection(LineCollection(_segmentos(G, todas), colors=GRIS_RED, linewidths=0.6))

    viales = tabla.sort_values("intermediacion_municipios")
    norm = Normalize(0, viales["intermediacion_municipios"].max())
    lc = LineCollection(_segmentos(G, zip(viales["u"], viales["v"])),
                        colors=RAMPA(norm(viales["intermediacion_municipios"].values)),
                        linewidths=0.8 + 3.2 * norm(viales["intermediacion_municipios"].values))
    ax.add_collection(lc)

    xs = [d["x"] / 1000 for n, d in G.nodes(data=True) if d["tipo"] == "municipio"]
    ys = [d["y"] / 1000 for n, d in G.nodes(data=True) if d["tipo"] == "municipio"]
    ax.scatter(xs, ys, s=6, color=TINTA_SUAVE, zorder=3, label="cabecera municipal")

    for fila in top.itertuples():
        g = G.edges[fila.u, fila.v]["geometry"]
        p = g.interpolate(0.5, normalized=True)
        ax.annotate(str(fila.rango), (p.x / 1000, p.y / 1000), fontsize=8, color=TINTA,
                    ha="center", va="center", zorder=5,
                    bbox=dict(boxstyle="circle,pad=0.25", fc="white",
                              ec=NARANJA if fila.es_puente else TINTA_SUAVE, lw=1.2))

    sm = plt.cm.ScalarMappable(cmap=RAMPA, norm=norm)
    cb = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.02)
    cb.set_label("pares de ciudades cuya ruta más barata usa la arista", color=TINTA_SUAVE)
    ax.set_title(f"Intermediación de aristas (Brandes) — top {len(top)} numeradas;\n"
                 f"círculo naranja = puente (su cierre desconecta la red)",
                 fontsize=10, color=TINTA)
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    # encuadre: componente conexa principal (las vías aisladas lejanas aplastan el mapa)
    import networkx as nx
    principal = max(nx.connected_components(G), key=len)
    cajas = [d["geometry"].bounds for _, _, d in G.subgraph(principal).edges(data=True)]
    xs_p = [b[0] / 1000 for b in cajas] + [b[2] / 1000 for b in cajas]
    ys_p = [b[1] / 1000 for b in cajas] + [b[3] / 1000 for b in cajas]
    mx, my = 0.04 * (max(xs_p) - min(xs_p)), 0.04 * (max(ys_p) - min(ys_p))
    ax.set_xlim(min(xs_p) - mx, max(xs_p) + mx); ax.set_ylim(min(ys_p) - my, max(ys_p) + my)
    ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout(); fig.savefig(ruta_png, dpi=150)
    return fig


def barras(top, ruta_png):
    fig, ax = plt.subplots(figsize=(9, 0.42 * len(top) + 1.4))
    t = top.iloc[::-1]
    etiquetas = [f"{r}. {n[:40]} ({i})" for r, n, i in zip(t["rango"], t["nombres"], t["id_arista"])]
    colores = [NARANJA if p else "#2a78d6" for p in t["es_puente"]]
    ax.barh(etiquetas, t["fraccion_pares"] * 100, color=colores, height=0.6)
    for y, val in enumerate(t["fraccion_pares"] * 100):
        ax.text(val, y, f" {val:.1f} %", va="center", fontsize=8, color=TINTA)
    ax.set_xlabel("% de pares de municipios cuya ruta más barata pasa por la arista",
                  color=TINTA_SUAVE)
    ax.tick_params(colors=TINTA_SUAVE, labelsize=8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="x", color="#e6e5e0", lw=0.6); ax.set_axisbelow(True)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#2a78d6", label="tiene alternativa"),
                       Patch(color=NARANJA, label="puente (sin alternativa)")],
              loc="lower right", fontsize=8, frameon=False)
    ax.set_title("Aristas viales con mayor intermediación", fontsize=10, color=TINTA, loc="left")
    fig.tight_layout(); fig.savefig(ruta_png, dpi=150)
    return fig


def main():
    G = cargar_grafo()
    tabla, top, rho = centralidad.ranking_criticas(G, top=config.TOP_ARISTAS_CRITICAS)
    salida = config.CARPETA_SALIDA
    tabla.to_csv(salida / "intermediacion_aristas.csv", index=False)
    top.to_csv(salida / "criticas_intermediacion.csv", index=False)
    por_via = centralidad.ranking_por_via(tabla, config.TOP_ARISTAS_CRITICAS)
    por_via.to_csv(salida / "criticas_por_via.csv", index=False)

    import pandas as pd
    with pd.option_context("display.max_colwidth", 40, "display.width", 160):
        print(top[["rango", "id_arista", "codigos_via", "nombres", "km",
                   "intermediacion_municipios", "fraccion_pares", "es_puente"]].to_string(index=False))
        print("\nAgrupado por código de vía (corredor):")
        print(por_via.round(3).to_string(index=False))
    n_puentes_top = int(top["es_puente"].sum())
    print(f"\nPeso usado: costo ({UNIDAD_COSTO}). {n_puentes_top} de las {len(top)} primeras son puentes.")
    print(f"Correlación de Spearman entre la versión 'municipios' y la clásica 'todos los nodos': {rho:.2f}")
    print("Recuerde: intermediación alta = mucho tráfico potencial, no necesariamente "
          "desvío caro. Contrastar con la simulación de cierres.")

    mapa(G, tabla, top, salida / "mapa_intermediacion.png")
    barras(top, salida / "barras_intermediacion.png")
    print(f"\nArchivos guardados en {salida}")
    plt.show()


if __name__ == "__main__":
    main()
