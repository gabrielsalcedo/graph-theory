"""Rutas de costo mínimo con el algoritmo de Dijkstra (implementación propia).

Se implementa a mano, en vez de llamar nx.dijkstra_path, para que el algoritmo sea
visible en el proyecto. Las pruebas comparan este resultado con networkx.

Dijkstra (1959), con cola de prioridad (montículo binario):
  1. dist[origen] = 0; el resto, infinito.
  2. Sacar de la cola el nodo no visitado con menor distancia tentativa.
  3. Para cada vecino, si dist[nodo] + costo(arista) < dist[vecino], actualizarlo
     ("relajar" la arista) y guardar de dónde vino.
  4. Repetir hasta sacar el destino (o vaciar la cola: no hay ruta).
Exige costos NO negativos: por eso costo.costo_arista nunca debe devolver negativos.
Complejidad: O((n + m) log n).
"""

import heapq
import math

from . import costo as modulo_costo


def dijkstra(G, origen, destino=None, peso="costo"):
    """Devuelve (distancias, predecesores). Si se da 'destino', se detiene al alcanzarlo."""
    dist = {origen: 0.0}
    previo = {origen: None}
    visitados = set()
    cola = [(0.0, 0, origen)]          # (distancia, desempate, nodo)
    contador = 1
    while cola:
        d, _, nodo = heapq.heappop(cola)
        if nodo in visitados:
            continue                    # entrada vieja de la cola
        visitados.add(nodo)
        if nodo == destino:
            break
        for vecino, datos in G[nodo].items():
            c = datos[peso]
            if c < 0:
                raise ValueError(f"Costo negativo en la arista {nodo}-{vecino}: Dijkstra no aplica.")
            nueva = d + c
            if nueva < dist.get(vecino, math.inf):
                dist[vecino] = nueva
                previo[vecino] = nodo
                heapq.heappush(cola, (nueva, contador, vecino))
                contador += 1
    return dist, previo


def reconstruir(previo, destino):
    camino = []
    nodo = destino
    while nodo is not None:
        camino.append(nodo)
        nodo = previo[nodo]
    return camino[::-1]


def ruta_minima(G, origen, destino, peso="costo"):
    """Ruta de menor costo entre dos nodos. Devuelve None si no hay ruta.

    Resultado: dict con costo total, km, lista de nodos y una tabla de aristas recorridas.
    """
    dist, previo = dijkstra(G, origen, destino, peso)
    if destino not in dist:
        return None
    nodos = reconstruir(previo, destino)
    tramos = []
    for a, b in zip(nodos[:-1], nodos[1:]):
        d = G.edges[a, b]
        tramos.append({
            "id_arista": d.get("id_arista"),
            "tipo": d["tipo"],
            "via": ", ".join(d["codigos_via"]) or "-",
            "nombre": " / ".join(d["nombres"]) or "(sin nombre)",
            "km": d["longitud_m"] / 1000,
            "costo": d[peso],
            "calzada": d["calzada"],
            "concesion": ", ".join(d["concesiones"]) or "-",
        })
    return {
        "origen": origen, "destino": destino,
        "costo": dist[destino],
        "unidad": modulo_costo.UNIDAD_COSTO,
        "km": sum(t["km"] for t in tramos),
        "nodos": nodos,
        "tramos": tramos,
    }
