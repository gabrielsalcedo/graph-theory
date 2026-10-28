"""
Figuras de los documentos. Solo dibujan: leen el grafo y las tablas de los pasos 02 a 07.

  red_detallada()            red INVIAS limpia (paso 02)
  grafo_analisis()           grafo de análisis sobre el mapa y como diagrama (paso 03)
  intermediacion()           mapa: aristas por intermediación, top numerado (paso 07)
  carga_vs_intermediacion()  posición en la red vs carga que realmente pasa (paso 07)
  cuadrantes()               carga vs costo de la alternativa, los cuatro grupos (paso 05)
  mapa_criticos()            mapa de las aristas por grupo (paso 05)
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from shapely import wkt

import config as c
from vial.ciudades import lista_ciudades, nombre_corto

AZUL, NARANJA, AQUA, GRIS, GRIS_CLARO = "#2a78d6", "#eb6834", "#1baf7a", "#9a9993", "#d9d8d3"
TINTA, TINTA_SUAVE = "#2b2b29", "#6b6a65"
COLOR_GRUPO = {"Crítico": NARANJA, "Importante con respaldo": AZUL, "Vulnerable local": AQUA,
               "Secundario": GRIS, "Sin carga": GRIS_CLARO}
plt.rcParams.update({"font.size": 8, "axes.titlesize": 10, "axes.titlecolor": TINTA,
                     "axes.edgecolor": TINTA_SUAVE, "xtick.color": TINTA_SUAVE,
                     "ytick.color": TINTA_SUAVE, "axes.labelcolor": TINTA_SUAVE})


def lineas(G, aristas):
    """Trazado de las aristas dadas, en km, para un LineCollection."""
    return [np.array(G.edges[e]["geometry"].coords) / 1000 for e in aristas]


def guardar(fig, nombre):
    """Guarda la figura en outputs/figuras/ y la cierra."""
    c.FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(c.FIGURAS / nombre, dpi=c.DPI_FIGURAS, facecolor="white")
    plt.close(fig)
    print("  " + str(c.FIGURAS / nombre))


def mapa_base(titulo):
    """Figura vacía con proporción de mapa y sin ejes."""
    fig, ax = plt.subplots(figsize=(6.5, 8.5))
    ax.set_title(titulo, loc="left")
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def ciudades_en(ax, G, etiquetas=True):
    """Dibuja las ciudades de G (con su nombre si etiquetas=True)."""
    C = lista_ciudades(G)
    ax.scatter([G.nodes[n]["x"] / 1000 for n in C], [G.nodes[n]["y"] / 1000 for n in C], s=30,
               color=TINTA, edgecolor="white", lw=0.6, zorder=4, label=f"ciudad ({len(C)})")
    if etiquetas:
        for n in C:
            ax.annotate(nombre_corto(G, n), (G.nodes[n]["x"] / 1000, G.nodes[n]["y"] / 1000),
                        xytext=(4, 2), textcoords="offset points", fontsize=6, color=TINTA, zorder=5)


def numerar(ax, G, aristas, color_borde):
    """Un círculo con el número de cada arista en su punto medio."""
    for i, e in enumerate(aristas, start=1):
        p = G.edges[e]["geometry"].interpolate(0.5, normalized=True)
        ax.annotate(str(i), (p.x / 1000, p.y / 1000), fontsize=6.5, ha="center", va="center",
                    color=TINTA, zorder=6,
                    bbox=dict(boxstyle="circle,pad=0.2", fc="white", ec=color_borde, lw=1))


def trazo_red_detallada():
    """Líneas de la red detallada (red_detallada.csv), en km."""
    r = pd.read_csv(c.GRAFO / "red_detallada.csv")
    return r, [np.array(wkt.loads(g).coords) / 1000 for g in r["geometria"]]


# ------------------------------------------------------------------ grafos (modelamiento)
def red_detallada(G):
    """red_detallada.png: la red INVIAS limpia con las ciudades."""
    r, trazo = trazo_red_detallada()
    n = len(set(r["u"]) | set(r["v"]))
    fig, ax = mapa_base(f"Red real detallada (INVIAS limpia): {n} nodos, {len(r)} aristas")
    ax.add_collection(LineCollection(trazo, colors=AZUL, linewidths=0.6))
    ciudades_en(ax, G)
    ax.autoscale()
    ax.plot([], [], color=AZUL, label="vía")
    ax.legend(loc="lower left", frameon=False)
    guardar(fig, "red_detallada.png")


def grafo_analisis(G):
    """grafo_analisis_mapa.png (trazado real) y grafo_analisis.png (diagrama)."""
    puentes = list(nx.bridges(G))
    resto = [e for e in G.edges() if e not in puentes and e[::-1] not in puentes]
    cruces = [n for n in G if G.nodes[n]["tipo"] == "cruce"]
    pos = {n: (d["x"] / 1000, d["y"] / 1000) for n, d in G.nodes(data=True)}

    def leyenda(ax):
        ax.scatter(*zip(*[pos[n] for n in cruces]), s=14, marker="s", color=GRIS, zorder=3,
                   label=f"cruce ({len(cruces)})")
        ax.plot([], [], color=AZUL, lw=1.4, label=f"corredor ({len(resto)})")
        ax.plot([], [], color=NARANJA, lw=1.8, label=f"puente ({len(puentes)})")
        ax.legend(loc="lower left", frameon=False)

    fig, ax = mapa_base("Grafo de análisis sobre la red vial: trazado real de los corredores")
    ax.add_collection(LineCollection(trazo_red_detallada()[1], colors=GRIS_CLARO, linewidths=0.5))
    ax.add_collection(LineCollection(lineas(G, resto), colors=AZUL, linewidths=1.3, zorder=2))
    ax.add_collection(LineCollection(lineas(G, puentes), colors=NARANJA, linewidths=1.8, zorder=2))
    ciudades_en(ax, G)
    leyenda(ax)
    ax.autoscale()
    guardar(fig, "grafo_analisis_mapa.png")

    fig, ax = mapa_base(f"Grafo de análisis: {G.number_of_nodes()} vértices, "
                        f"{G.number_of_edges()} aristas (conexo y planar)")
    for e, color, lw in [(e, AZUL, 1.2) for e in resto] + [(e, NARANJA, 1.8) for e in puentes]:
        ax.plot(*zip(pos[e[0]], pos[e[1]]), color=color, lw=lw, zorder=2)
    ciudades_en(ax, G)
    for n in cruces:
        ax.annotate(nombre_corto(G, n), pos[n], xytext=(3, -7), textcoords="offset points",
                    fontsize=5, color=TINTA_SUAVE)
    leyenda(ax)
    guardar(fig, "grafo_analisis.png")


# ------------------------------------------------------------------ resultados (implementación)
def intermediacion(G, t):
    """intermediacion.png: mapa de C_B(e), con el top numerado. t = intermediacion_y_carga.csv."""
    arista = {d["id_arista"]: (u, v) for u, v, d in G.edges(data=True)}
    t = t.sort_values("intermediacion")
    fig, ax = mapa_base(f"Intermediación de aristas: % de pares de ciudades cuya ruta más "
                        f"barata la usa\n(top {c.TOP} numeradas; borde naranja = puente)")
    escala = t["fraccion_pares"] / t["fraccion_pares"].max()
    lc = LineCollection(lineas(G, [arista[i] for i in t["id_arista"]]),
                        cmap=plt.get_cmap("Blues"), linewidths=0.8 + 3.2 * escala)
    lc.set_array(t["fraccion_pares"].values * 100)
    lc.set_clim(0, t["fraccion_pares"].max() * 100)
    ax.add_collection(lc)
    ciudades_en(ax, G, etiquetas=False)
    top = t.sort_values("rango_intermediacion").head(c.TOP)
    for i, f in enumerate(top.itertuples(), start=1):    # borde naranja si es puente
        p = G.edges[arista[f.id_arista]]["geometry"].interpolate(0.5, normalized=True)
        ax.annotate(str(i), (p.x / 1000, p.y / 1000), fontsize=6.5, ha="center", va="center",
                    zorder=6, color=TINTA, bbox=dict(boxstyle="circle,pad=0.2", fc="white",
                                                     ec=NARANJA if f.es_puente else TINTA_SUAVE))
    fig.colorbar(lc, ax=ax, shrink=0.4, pad=0.01).set_label("% de pares de ciudades")
    ax.autoscale()
    guardar(fig, "intermediacion.png")


def carga_vs_intermediacion(t):
    """carga_vs_intermediacion.png: dispersión C_B(e) vs x_e con la correlación de Spearman."""
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    normal = t[~t["es_puente"]]
    puente = t[t["es_puente"]]
    ax.scatter(normal["fraccion_pares"] * 100, normal["carga_t"] / 1e6, s=30, color=AZUL,
               edgecolor="white", lw=0.8, label="arista con alternativa", zorder=3)
    ax.scatter(puente["fraccion_pares"] * 100, puente["carga_t"] / 1e6, s=40, color=NARANJA,
               edgecolor="white", lw=0.8, label="puente", zorder=3)
    # se rotulan las que más se apartan: mucha carga y poca intermediación o al revés
    for f in t.nlargest(5, "carga_t").itertuples():
        ax.annotate(f.nombre, (f.fraccion_pares * 100, f.carga_t / 1e6), xytext=(4, 2),
                    textcoords="offset points", fontsize=6, color=TINTA)
    for f in t[t["carga_t"] < t["carga_t"].median()].nlargest(2, "fraccion_pares").itertuples():
        ax.annotate(f.nombre, (f.fraccion_pares * 100, f.carga_t / 1e6), xytext=(4, 2),
                    textcoords="offset points", fontsize=6, color=TINTA)
    rho = t["intermediacion"].corr(t["carga_t"], method="spearman")
    ax.set_title(f"Posición en la red vs. carga que realmente pasa (Spearman = {rho:.2f})", loc="left")
    ax.set_xlabel("Intermediación: % de pares de ciudades cuya ruta más barata la usa")
    ax.set_ylabel("Carga asignada (millones de t al año)")
    ax.grid(color="#e6e5e0", lw=0.6)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    guardar(fig, "carga_vs_intermediacion.png")


def cuadrantes(t):
    """cuadrantes.png: carga vs sobrecosto por tonelada desviada. t = cierres_aristas.csv."""
    con = t[t["carga_t"] > 0].copy()
    techo = con["cop_por_t_desviada"].max() * 1.15         # los puentes van arriba: sin alternativa
    con["y"] = con["cop_por_t_desviada"].fillna(techo)
    con.loc[con["es_puente"], "y"] = techo
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    for g, color in COLOR_GRUPO.items():
        s = con[con["grupo"] == g]
        if len(s):
            ax.scatter(s["carga_t"] / 1e6, s["y"] / 1000, s=32, color=color, edgecolor="white",
                       lw=0.8, label=f"{g} ({len(s)})", zorder=3)
    ax.axvline(con["carga_t"].median() / 1e6, color=TINTA_SUAVE, lw=0.8, ls="--")
    ax.axhline(con.loc[~con["es_puente"], "cop_por_t_desviada"].median() / 1000, color=TINTA_SUAVE,
               lw=0.8, ls="--")
    ax.axhline(techo / 1000 * 0.96, color=GRIS_CLARO, lw=0.6)
    ax.text(con["carga_t"].max() / 1e6, techo / 1000 * 1.02,
            "puentes: sin ruta alterna", ha="right", fontsize=6.5, color=TINTA_SUAVE)
    for f in con.nlargest(6, "sobrecosto_cop_anual").itertuples():
        ax.annotate(f.nombre, (f.carga_t / 1e6, f.y / 1000), xytext=(4, 2),
                    textcoords="offset points", fontsize=6, color=TINTA)
    for i, f in enumerate(con[con["es_puente"]].sort_values("carga_t").itertuples()):
        ax.annotate(f.nombre, (f.carga_t / 1e6, f.y / 1000), xytext=(4, -8 - 8 * (i % 2)),
                    textcoords="offset points", fontsize=6, color=TINTA)
    ax.set_title("¿Cuánta carga mueve y qué tan mala es su alternativa?", loc="left")
    ax.set_xlabel("Carga asignada (millones de t al año)")
    ax.set_ylabel("Sobrecosto por tonelada desviada (miles de COP/t)")
    ax.grid(color="#e6e5e0", lw=0.6)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1, 1))
    guardar(fig, "cuadrantes.png")


def mapa_criticos(G, t):
    """mapa_criticos.png: aristas por grupo, con el top 10 numerado. t = cierres_aristas.csv."""
    arista = {d["id_arista"]: (u, v) for u, v, d in G.edges(data=True)}
    fig, ax = mapa_base("Aristas por grupo; números = top por sobrecosto o carga sin ruta")
    for g, color in list(COLOR_GRUPO.items())[::-1]:
        s = t[t["grupo"] == g]
        ancho = 2.4 if g == "Crítico" else 1.4
        ax.add_collection(LineCollection(lineas(G, [arista[i] for i in s["id_arista"]]),
                                         colors=color, linewidths=ancho, zorder=2,
                                         label=f"{g} ({len(s)})"))
    ciudades_en(ax, G)
    numerar(ax, G, [arista[i] for i in t.sort_values("rango").head(10)["id_arista"]], TINTA_SUAVE)
    ax.autoscale()
    ax.legend(loc="upper left", frameon=False)
    guardar(fig, "mapa_criticos.png")
