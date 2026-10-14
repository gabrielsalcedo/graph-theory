"""
PASO 6 — Pruebas automáticas de Dijkstra y de la intermediación.

1-5. Grafo de juguete (data/pruebas/grafo_juguete.json): respuestas escritas a mano.
6.   Grafo de análisis real: nuestro Dijkstra (vial/rutas.py) contra networkx en 200 pares.

Ejecutar en Spyder con F5 (o `pytest 06_pruebas.py`). Deben salir 6/6.
"""

import json
import random

import networkx as nx

import config
from vial import centralidad, rutas

JUGUETE = json.loads(config.ARCHIVO_JUGUETE.read_text(encoding="utf-8"))
RESPUESTAS = JUGUETE["respuestas"]


def grafo_juguete():
    G = nx.Graph()
    for n, (x, y) in JUGUETE["nodos"].items():
        G.add_node(n, tipo="municipio", x=x, y=y, nombre=n)
    for a in JUGUETE["aristas"]:
        G.add_edge(a["u"], a["v"], id_arista=a["id"], tipo="via", costo=float(a["km"]),
                   longitud_m=a["km"] * 1000.0, codigos_via=(a["id"],),
                   nombres=(f"{a['u']}-{a['v']}",), calzada=a["calzada"],
                   concesiones=(a["concesion"],) if a["concesion"] else ())
    return G


def test_dijkstra_costos_base():
    G = grafo_juguete()
    for par, esperado in RESPUESTAS["costo_base_por_par"].items():
        o, d = par.split("->")
        r = rutas.ruta_minima(G, o, d)
        assert abs(r["costo"] - esperado) < 1e-9, (par, r["costo"], esperado)


def test_dijkstra_camino_A_H():
    r = rutas.ruta_minima(grafo_juguete(), "A", "H")
    assert r["nodos"] == ["A", "B", "C", "D", "G", "H"], r["nodos"]


def test_dijkstra_sin_ruta():
    assert rutas.ruta_minima(grafo_juguete(), "A", "K") is None


def test_desvio_barato_y_caro():
    G = grafo_juguete()
    G.remove_edge("B", "C")
    assert rutas.ruta_minima(G, "B", "C")["costo"] == 12      # desvío B-E-C
    G = grafo_juguete()
    G.remove_edge("C", "D")
    assert rutas.ruta_minima(G, "C", "D")["costo"] == 100     # desvío C-B-A-F-D


def test_intermediacion_juguete():
    """D-G separa {A,B,C,D,E,F} de {G,H,I,J}: 6 × 4 = 24 pares. B-E: pares B-E y A-E
    (2) más medio par E-F, que tiene dos rutas de 56 km empatadas -> 2,5."""
    G = grafo_juguete()
    t = centralidad.intermediacion_aristas(G, version="municipios").set_index("id_arista")
    assert t.at["e08", "intermediacion"] == 24
    assert t.at["e03", "intermediacion"] == 2.5
    assert t.at["e08", "es_puente"] and not t.at["e02", "es_puente"]
    assert set(t.index[t["es_puente"]]) == {"e08", "e12", "e13", "e14"}


def test_dijkstra_igual_a_networkx_en_red():
    """Compara la implementación propia con networkx en 200 pares al azar del grafo real."""
    from vial.archivos import cargar_grafo
    G = cargar_grafo()
    mun = [n for n, d in G.nodes(data=True) if d["tipo"] == "municipio"]
    azar = random.Random(1)
    for _ in range(200):
        o, d = azar.sample(mun, 2)
        propio = rutas.ruta_minima(G, o, d)
        try:
            ref = nx.dijkstra_path_length(G, o, d, weight="costo")
        except nx.NetworkXNoPath:
            ref = None
        if ref is None:
            assert propio is None
        else:
            assert abs(propio["costo"] - ref) < 1e-6, (o, d, propio["costo"], ref)


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    fallas = 0
    for p in pruebas:
        try:
            p()
            print(f"OK     {p.__name__}")
        except AssertionError as e:
            fallas += 1
            print(f"FALLA  {p.__name__}: {e}")
    print(f"\n{len(pruebas) - fallas}/{len(pruebas)} pruebas superadas.")
