"""
PASO 5 — Figuras de los grafos: un PNG por grafo, listo para los documentos.

Entradas: outputs/resultados/grafo.pkl y grafo_detallado.pkl (paso 2)
Salidas en outputs/figuras/:
  red_detallada.png         red detallada (INVIAS limpia, 841 nodos)
  grafo_analisis_mapa.png   grafo de análisis con el trazado real de cada corredor
  grafo_analisis.png        grafo de análisis como diagrama de nodos y aristas

Todo se dibuja con matplotlib a partir de los grafos guardados; nada se edita a mano.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import config
from vial.archivos import cargar_detallado, cargar_grafo

CARPETA = config.CARPETA_FIGURAS
NARANJA, AZUL, GRIS, TINTA, TINTA_SUAVE = "#eb6834", "#2a78d6", "#d9d8d3", "#2b2b29", "#6b6a65"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 10, "axes.titlecolor": TINTA})


def _trazado(ax, G, color, lw, aristas=None, z=1):
    for u, v in (aristas if aristas is not None else G.edges()):
        c = np.array(G.edges[u, v]["geometry"].coords) / 1000
        ax.plot(c[:, 0], c[:, 1], color=color, lw=lw, zorder=z, solid_capstyle="round")


def _cerrar(fig, ax, nombre, titulo, leyenda="lower left", ancla=None):
    ax.set_title(titulo, loc="left")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc=leyenda, bbox_to_anchor=ancla, fontsize=7, frameon=False)
    fig.tight_layout()
    CARPETA.mkdir(parents=True, exist_ok=True)
    fig.savefig(CARPETA / nombre, dpi=250, facecolor="white")
    print(f"  {CARPETA / nombre}")


def _etiqueta(nombre):
    return nombre.split(",")[0].title()


def red(G, nombre, titulo, n_etiquetas=0):
    fig, ax = plt.subplots(figsize=(6.5, 8.5))
    _trazado(ax, G, AZUL, 0.6)
    cruces = [(d["x"] / 1000, d["y"] / 1000) for _, d in G.nodes(data=True) if d["tipo"] != "municipio"]
    mun = [(n, d) for n, d in G.nodes(data=True) if d["tipo"] == "municipio"]
    ax.scatter(*zip(*cruces), s=1.5, color=TINTA, zorder=2, label=f"cruce ({len(cruces)})")
    ax.scatter([d["x"] / 1000 for _, d in mun], [d["y"] / 1000 for _, d in mun], s=12,
               color=NARANJA, edgecolor="white", lw=0.4, zorder=3,
               label=f"municipio conectado ({len(mun)})")
    top = sorted(mun, key=lambda t: -t[1].get("ton_total", 0))[:n_etiquetas]
    for _, d in top:
        ax.annotate(_etiqueta(d["nombre"]), (d["x"] / 1000, d["y"] / 1000), xytext=(3, 2),
                    textcoords="offset points", fontsize=6, color=TINTA)
    ax.plot([], [], color=AZUL, lw=0.8, label=f"arista ({G.number_of_edges()})")
    _cerrar(fig, ax, nombre, titulo)


def analisis(G, D):
    ciudades = [n for n, d in G.nodes(data=True) if d["tipo"] == "municipio"]
    cruces = [n for n, d in G.nodes(data=True) if d["tipo"] != "municipio"]
    pos = {n: (d["x"] / 1000, d["y"] / 1000) for n, d in G.nodes(data=True)}
    puentes = [e for e in G.edges() if frozenset(e) in {frozenset(b) for b in nx.bridges(G)}]
    resto = [e for e in G.edges() if e not in puentes]

    def nodos(ax):
        ax.scatter(*zip(*[pos[n] for n in cruces]), s=16, marker="s", color=TINTA, zorder=3,
                   label=f"cruce clave ({len(cruces)})")
        ax.scatter(*zip(*[pos[n] for n in ciudades]), s=46, color=NARANJA, edgecolor="white",
                   zorder=4, label=f"ciudad o área metropolitana ({len(ciudades)})")
        ax.plot([], [], color=AZUL, lw=1.4, label=f"corredor ({G.number_of_edges() - len(puentes)})")
        ax.plot([], [], color=NARANJA, lw=1.8, label=f"puente ({len(puentes)})")

    # mapa: trazado real
    fig, ax = plt.subplots(figsize=(6.5, 8.5))
    if D is not None:
        _trazado(ax, D, GRIS, 0.5)
    _trazado(ax, G, AZUL, 1.3, resto, z=2)
    _trazado(ax, G, NARANJA, 1.8, puentes, z=2)
    nodos(ax)
    for n in ciudades:
        ax.annotate(_etiqueta(G.nodes[n]["nombre"]), pos[n], xytext=(4, 2),
                    textcoords="offset points", fontsize=6, color=TINTA, zorder=5)
    if D is not None:
        ax.plot([], [], color=GRIS, lw=0.8, label="red detallada")
    _cerrar(fig, ax, "grafo_analisis_mapa.png",
            "Grafo de análisis sobre la red vial: trazado real de los corredores")

    # diagrama: aristas rectas, todos los nombres
    fig, ax = plt.subplots(figsize=(6.5, 8.5))
    for (u, v), col, lw in [(e, AZUL, 1.2) for e in resto] + [(e, NARANJA, 1.8) for e in puentes]:
        ax.plot(*zip(pos[u], pos[v]), color=col, lw=lw, zorder=2)
    nodos(ax)
    for n in ciudades:
        ax.annotate(_etiqueta(G.nodes[n]["nombre"]), pos[n], xytext=(4, 2),
                    textcoords="offset points", fontsize=6.5, color=TINTA, zorder=5)
    for n in cruces:
        ax.annotate(G.nodes[n]["nombre"].split("(")[1].rstrip(")"), pos[n], xytext=(3, -7),
                    textcoords="offset points", fontsize=5, color=TINTA_SUAVE, zorder=5)
    _cerrar(fig, ax, "grafo_analisis.png",
            f"Grafo de análisis: {G.number_of_nodes()} vértices, {G.number_of_edges()} aristas "
            f"(conexo y planar)", leyenda="upper left", ancla=(0.64, 0.8))


def main():
    print("Figuras guardadas:")
    G = cargar_grafo()
    D = cargar_detallado()
    red(D, "red_detallada.png",
        f"Red real detallada (INVIAS limpia): {D.number_of_nodes()} nodos, "
        f"{D.number_of_edges()} aristas", n_etiquetas=20)
    analisis(G, D)
    plt.close("all")


if __name__ == "__main__":
    main()
