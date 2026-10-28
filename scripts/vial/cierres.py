"""
Simulación de cierres (Algoritmo 1 del documento).

  simular_cierre()     I(S) y D(S) al cerrar un conjunto de aristas S
  aristas_por_tramo()  qué aristas de G cierra cada tramo de INVIAS
  clasificar()         grupo de cada arista según su carga y su alternativa
"""

import pandas as pd

import config as c
from vial.rutas import dijkstra


def simular_cierre(G, od, base, cerradas):
    """Algoritmo 1: cierra las aristas 'cerradas' y mide el daño.

    I = sobrecosto (COP/año) de la carga que sí encuentra ruta alterna:
        suma de T_od x [c_{G-S}(o,d) - c_G(o,d)]
    D = demanda insatisfecha (t/año): toneladas que se quedan sin ninguna ruta.
    Devuelve (I, D).
    """
    H = G.copy()
    H.remove_edges_from(cerradas)
    I, D = 0.0, 0.0
    for o, grupo in od.groupby("o"):
        dist_nueva, _ = dijkstra(H, o)
        for f in grupo.itertuples():
            if f.d not in dist_nueva:
                D += f.toneladas
            else:
                I += f.toneladas * (dist_nueva[f.d] - base[o][0][f.d])
    return I, D


def aristas_por_tramo(G, tramos, traslape):
    """Recibe G, tramos.csv y tramos_por_arista.csv. Un tramo cierra una arista si la
    recorre al menos KM_MIN_TRAMO_EN_ARISTA km (o FRACCION_MIN_TRAMO del tramo, si es más
    corto). Devuelve {id_tramo: [aristas (u, v)]}."""
    km_tramo = dict(zip(tramos["id_tramo"], tramos["km"]))
    arista = {d["id_arista"]: (u, v) for u, v, d in G.edges(data=True)}
    usa = {}
    for f in traslape.itertuples():
        if f.km_en_arista >= min(c.KM_MIN_TRAMO_EN_ARISTA, c.FRACCION_MIN_TRAMO * km_tramo[f.id_tramo]):
            usa.setdefault(f.id_tramo, []).append(arista[f.id_arista])
    return usa


def clasificar(t):
    """Cuatro grupos con dos preguntas: ¿mueve mucha carga? (x_e sobre la mediana) y ¿su
    alternativa es mala? (sobrecosto por tonelada desviada sobre la mediana, o es puente).
    Recibe la tabla de cierres por arista; devuelve una Serie con el grupo de cada una."""
    con_carga = t[t["carga_t"] > 0]
    mucha = t["carga_t"] > con_carga["carga_t"].median()
    mala = t["es_puente"] | (t["cop_por_t_desviada"] > con_carga["cop_por_t_desviada"].median())
    grupo = pd.Series("Secundario", index=t.index)
    grupo[mucha & ~mala] = "Importante con respaldo"
    grupo[~mucha & mala] = "Vulnerable local"
    grupo[mucha & mala] = "Crítico"
    grupo[t["carga_t"] == 0] = "Sin carga"
    return grupo
