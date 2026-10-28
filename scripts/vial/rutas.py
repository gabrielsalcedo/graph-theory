"""
Rutas de menor costo (implementación propia de Dijkstra con montículo binario).

  dijkstra()       costo mínimo desde un origen a todos los vértices
  camino()         reconstruye la ruta a partir de 'previo'
  ruta()           la ruta más barata entre dos vértices
  costos_desde()   c_G(o, d) para todo origen o con carga
"""

import heapq
import math


def dijkstra(G, origen, peso="costo"):
    """Costo mínimo desde 'origen' a todos los vértices (Dijkstra, 1959).

    1. dist[origen] = 0 y el resto infinito.
    2. Se saca de la cola el vértice no visitado con menor distancia.
    3. Para cada vecino: si pasar por este vértice es más barato, se actualiza su
       distancia y se anota de dónde vino (previo).
    4. Se repite hasta vaciar la cola.
    Devuelve (dist, previo). Un vértice que no aparece en dist no es alcanzable.
    """
    dist, previo = {origen: 0.0}, {origen: None}
    visitados = set()
    cola = [(0.0, origen)]
    while cola:
        d, n = heapq.heappop(cola)
        if n in visitados:
            continue
        visitados.add(n)
        for vecino, datos in G[n].items():
            nueva = d + datos[peso]
            if nueva < dist.get(vecino, math.inf):
                dist[vecino], previo[vecino] = nueva, n
                heapq.heappush(cola, (nueva, vecino))
    return dist, previo


def camino(previo, destino):
    """Reconstruye la ruta siguiendo 'previo' desde el destino hasta el origen."""
    nodos = []
    while destino is not None:
        nodos.append(destino)
        destino = previo[destino]
    return nodos[::-1]


def ruta(G, origen, destino):
    """Ruta más barata entre dos vértices: dict con nodos, costo (COP/t) y km.
    Devuelve None si no hay ruta."""
    dist, previo = dijkstra(G, origen)
    if destino not in dist:
        return None
    nodos = camino(previo, destino)
    km = sum(G.edges[a, b]["km"] for a, b in zip(nodos[:-1], nodos[1:]))
    return {"nodos": nodos, "costo": dist[destino], "km": km}


def costos_desde(G, od):
    """c_G(o, d): un Dijkstra por cada ciudad de origen. Devuelve {o: (dist, previo)}."""
    return {o: dijkstra(G, o) for o in od["o"].unique()}
