"""
PASO 06 — Pruebas: cada cálculo se comprueba en un grafo pequeño con respuestas a mano.

Grafo de juguete (data/pruebas/grafo_juguete.json), pesos en km:

    camino principal  A -10- B -10- C -10- D -15- G -5- H
    desvío corto      B -6- E -6- C          (12 km en vez de 10)
    desvío largo      A -40- F -40- D        (80 km en vez de 30)
    al otro lado      G -5- I -5- H,  I -20- J
    aparte            K -8- L -8- M          (otra componente)

Demanda de prueba T: A->H 100 t, B->C 50 t, K->M 10 t.

Ejecutar con `python 06_pruebas.py` (o `pytest 06_pruebas.py`). Deben salir 9/9.
Necesita el grafo real (paso 03) para la última prueba.
"""

import json
import random
import sys

import networkx as nx
import pandas as pd

import config as c
from vial.archivos import cargar_grafo
from vial.centralidad import asignar_carga
from vial.cierres import simular_cierre
from vial.ciudades import lista_ciudades
from vial.rutas import costos_desde, ruta

JUGUETE = json.loads(c.JUGUETE.read_text(encoding="utf-8"))
T = pd.DataFrame({"o": ["A", "B", "K"], "d": ["H", "C", "M"], "toneladas": [100.0, 50.0, 10.0]})


def juguete():
    G = nx.Graph()
    for a in JUGUETE["aristas"]:
        G.add_edge(a["u"], a["v"], id_arista=a["id"], km=a["km"], costo=float(a["km"]))
    return G


# --------------------------------------------------------------- Dijkstra
def test_dijkstra_costos():
    for par, esperado in JUGUETE["respuestas"]["costo_base_por_par"].items():
        o, d = par.split("->")
        assert ruta(juguete(), o, d)["costo"] == esperado, par


def test_dijkstra_camino_y_sin_ruta():
    assert ruta(juguete(), "A", "H")["nodos"] == ["A", "B", "C", "D", "G", "H"]
    assert ruta(juguete(), "A", "K") is None             # componentes distintas


def test_puentes_tarjan():
    puentes = {frozenset(e) for e in nx.bridges(juguete())}
    assert puentes == {frozenset(p) for p in JUGUETE["respuestas"]["puentes"]}


# --------------------------------------------------------------- carga asignada
def test_asignacion_todo_o_nada():
    """B-C la usan A->H (100 t) y B->C (50 t): 150 t. D-G solo A->H: 100 t. B-E nadie."""
    x = asignar_carga(juguete(), T)
    assert x[("B", "C")] == 150 and x[("D", "G")] == 100 and x[("B", "E")] == 0
    assert x[("K", "L")] == 10


# --------------------------------------------------------------- cierres (Algoritmo 1)
def test_cierre_con_desvio_barato():
    """Cerrar B-C: B->C pasa por E (12 km en vez de 10: +2) y A->H también (+2).
    I = 50 x 2 + 100 x 2 = 300; nadie queda sin ruta."""
    G = juguete()
    assert simular_cierre(G, T, costos_desde(G, T), [("B", "C")]) == (300, 0)


def test_cierre_con_desvio_caro():
    """Cerrar C-D: A->H debe ir por F (A-F-D = 80 en vez de A-B-C-D = 30: +50).
    I = 100 x 50 = 5.000."""
    G = juguete()
    assert simular_cierre(G, T, costos_desde(G, T), [("C", "D")]) == (5000, 0)


def test_cierre_de_puente():
    """Cerrar D-G (puente): A->H se queda sin ruta. I = 0 y D = 100 t."""
    G = juguete()
    assert simular_cierre(G, T, costos_desde(G, T), [("D", "G")]) == (0, 100)


def test_cierre_de_varias_aristas():
    """Cerrar a la vez B-C y C-D (un 'tramo' de dos aristas): A->H va por F (+50) y
    B->C por E (+2). I = 100 x 50 + 50 x 2 = 5.100."""
    G = juguete()
    assert simular_cierre(G, T, costos_desde(G, T), [("B", "C"), ("C", "D")]) == (5100, 0)


# --------------------------------------------------------------- grafo real
def test_dijkstra_propio_igual_a_networkx():
    """En 200 pares al azar del grafo real, nuestro Dijkstra da lo mismo que networkx."""
    G = cargar_grafo()
    azar = random.Random(c.SEMILLA_PRUEBA)
    for _ in range(c.N_PARES_PRUEBA):
        o, d = azar.sample(lista_ciudades(G), 2)
        assert abs(ruta(G, o, d)["costo"] - nx.dijkstra_path_length(G, o, d, weight="costo")) < 1e-6


if __name__ == "__main__":
    pruebas = [f for n, f in dict(globals()).items() if n.startswith("test_")]
    fallas = 0
    for p in pruebas:
        try:
            p()
            print(f"OK     {p.__name__}")
        except AssertionError as e:
            fallas += 1
            print(f"FALLA  {p.__name__} {e}")
    print(f"\n{len(pruebas) - fallas}/{len(pruebas)} pruebas superadas.")
    sys.exit(1 if fallas else 0)          # así ejecutar_todo.py se detiene si algo falla
