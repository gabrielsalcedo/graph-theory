"""
PASO 07 — Dos formas de medir la importancia de una arista (objetivo específico 3).

  C_B(e)  INTERMEDIACIÓN: cuántos pares de ciudades tienen su ruta más barata por e
          (algoritmo de Brandes, vía networkx). Depende solo del grafo: todos los pares
          pesan lo mismo.
  x_e     CARGA ASIGNADA: toneladas al año que pasan por e (asignación todo o nada con
          la matriz T del RNDC). Es la intermediación ponderada por la demanda.

Si las dos dieran el mismo orden, bastaría con mirar el mapa. La correlación de Spearman
dice qué tanto coinciden, y las diferencias señalan tramos sobrestimados o subestimados.

Si ya corrió el paso 05, compara además los tres ángulos de la hipótesis: posición (C_B),
uso (x_e) y consecuencia de perder la arista (sobrecosto I).

Salidas: outputs/resultados/intermediacion_y_carga.csv  (las 77 aristas)
         outputs/resultados/tres_angulos.csv            (rangos de C_B, x_e e I)
"""

import networkx as nx
import pandas as pd

import config as c
from vial.archivos import cargar_grafo, cargar_od
from vial.centralidad import asignar_carga, intermediacion, tres_angulos
from vial.ciudades import lista_ciudades


def main():
    c.RESULTADOS.mkdir(parents=True, exist_ok=True)
    G = cargar_grafo()
    od = cargar_od()
    C = lista_ciudades(G)
    pares = len(C) * (len(C) - 1) / 2

    cb = intermediacion(G, C)
    x = asignar_carga(G, od)
    puentes = {tuple(sorted(e)) for e in nx.bridges(G)}

    filas = []
    for u, v, d in G.edges(data=True):
        e = tuple(sorted((u, v)))
        filas.append({"id_arista": d["id_arista"], "u": u, "v": v, "nombre": d["nombre"],
                      "codigos_via": d["codigos_via"], "km": round(d["km"], 2),
                      "intermediacion": cb.get((u, v), cb.get((v, u))),
                      "fraccion_pares": cb.get((u, v), cb.get((v, u))) / pares,
                      "carga_t": x[e], "es_puente": e in puentes})
    t = pd.DataFrame(filas)
    t["fraccion_carga"] = t["carga_t"] / od["toneladas"].sum()
    t["rango_intermediacion"] = t["intermediacion"].rank(ascending=False, method="min").astype(int)
    t["rango_carga"] = t["carga_t"].rank(ascending=False, method="min").astype(int)
    t = t.sort_values("rango_intermediacion")
    t.round({"fraccion_pares": 4, "carga_t": 0, "fraccion_carga": 4}).to_csv(
        c.RESULTADOS / "intermediacion_y_carga.csv", index=False)

    rho = t["intermediacion"].corr(t["carga_t"], method="spearman")
    pd.set_option("display.width", 160)
    print(f"Top {c.TOP} por INTERMEDIACIÓN (pares de ciudades sobre {pares:.0f}):")
    print(t.head(c.TOP)[["rango_intermediacion", "id_arista", "nombre", "km",
                          "fraccion_pares", "rango_carga", "es_puente"]].to_string(index=False))
    print(f"\nTop {c.TOP} por CARGA ASIGNADA (millones de t al año):")
    top = t.sort_values("rango_carga").head(c.TOP).assign(Mt=lambda d: (d["carga_t"] / 1e6).round(2))
    print(top[["rango_carga", "id_arista", "nombre", "Mt", "rango_intermediacion",
               "es_puente"]].to_string(index=False))
    print(f"\nCorrelación de Spearman entre intermediación y carga: {rho:.2f}")

    cierres = c.RESULTADOS / "cierres_aristas.csv"
    if cierres.exists():
        m, lineas = tres_angulos(t, pd.read_csv(cierres), top=10)
        m.round({"carga_t": 0, "sobrecosto_cop_anual": 0}).to_csv(
            c.RESULTADOS / "tres_angulos.csv", index=False)
        print("\nPOSICIÓN, USO Y CONSECUENCIA (hipótesis):")
        print("\n".join(lineas))
    else:
        print(f"\n(falta {cierres.name}: corra 05_simulacion_cierres.py para comparar con I)")


if __name__ == "__main__":
    main()
