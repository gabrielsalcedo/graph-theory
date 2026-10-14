"""Costo de una arista.

ÚNICO lugar donde se define el costo. Recibe el diccionario de atributos de una
arista y devuelve un número no negativo. Dijkstra, la intermediación y la simulación
de cierres usan el atributo 'costo' que se calcula aquí.

Versión actual (datos reales): costo = km × tarifa (COP por tonelada-km), es decir, lo
que cuesta mover UNA tonelada por esa arista, en pesos de 2015. La tarifa sale del RNDC
(config.COSTO_COP_TON_KM). Si la tarifa es None, el costo queda en km.

OJO para el documento: con una tarifa ÚNICA, el costo es proporcional a los km, así que
las rutas óptimas y la intermediación son las mismas que con km; lo que cambia es la
unidad (los desvíos se leen en pesos por tonelada). El costo empieza a cambiar las rutas
cuando la tarifa depende de la arista (p. ej. más cara en afirmado o en calzada sencilla).
Esa decisión es suya; se cambia solo aquí.
Atributos disponibles en cada arista:
  longitud_m, tipo ("via" o "conector"), superficie_afirmado_frac (0–1),
  calzada, concesiones, codigos_via, rutas, ids_tramo.
"""

import config

TARIFA = config.COSTO_COP_TON_KM
UNIDAD_COSTO = "km" if TARIFA is None else "COP/t"


def costo_arista(atributos: dict) -> float:
    km = atributos["longitud_m"] / 1000.0
    return km if TARIFA is None else km * TARIFA


def asignar_costos(G) -> None:
    for u, v, datos in G.edges(data=True):
        datos["costo"] = costo_arista(datos)
