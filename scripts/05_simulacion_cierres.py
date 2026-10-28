"""
PASO 05 — Simulación de cierres (objetivo específico 4, Algoritmo 1 del documento).

Se cierra, una por una, cada arista del grafo y cada tramo de INVIAS (un tramo puede
recorrer varias aristas), y se mide el daño:
  I  sobrecosto (COP/año) que paga la carga que sí encuentra ruta alterna
  D  demanda insatisfecha (t/año): carga que se queda sin ruta (solo pasa en puentes)

Luego cada arista se clasifica en uno de cuatro grupos con dos preguntas:
  ¿mueve mucha carga?               x_e por encima de la mediana
  ¿su alternativa es mala?          sobrecosto por tonelada desviada (I / x_e) por encima
                                    de la mediana, o es un puente (no hay alternativa)
                     alternativa buena            alternativa mala
  mucha carga        Importante con respaldo      CRÍTICO
  poca carga         Secundario                   Vulnerable local

Salidas en outputs/resultados/:
  cierres_aristas.csv   las 77 aristas: x_e, I, D, sobrecosto por tonelada, grupo
  cierres_tramos.csv    cierre de cada tramo de INVIAS (conjunto de aristas S)
"""

import networkx as nx
import pandas as pd

import config as c
from vial.archivos import cargar_grafo, cargar_od
from vial.centralidad import asignar_carga
from vial.cierres import aristas_por_tramo, clasificar, simular_cierre
from vial.rutas import costos_desde

COL_DIAS = f"sobrecosto_{c.DIAS_CIERRE}_dias"


def main():
    c.RESULTADOS.mkdir(parents=True, exist_ok=True)
    G = cargar_grafo()
    od = cargar_od()
    base = costos_desde(G, od)                 # situación normal: c_G(o, d)
    x = asignar_carga(G, od, base)
    puentes = {tuple(sorted(e)) for e in nx.bridges(G)}

    # ---- 1. cierre de cada arista
    filas = []
    for u, v, d in G.edges(data=True):
        e = tuple(sorted((u, v)))
        I, D = simular_cierre(G, od, base, [(u, v)])
        filas.append({"id_arista": d["id_arista"], "nombre": d["nombre"], "km": round(d["km"], 1),
                      "es_puente": e in puentes, "carga_t": x[e], "sobrecosto_cop_anual": I,
                      "sin_ruta_t": D})
    t = pd.DataFrame(filas)
    desviada = t["carga_t"] - t["sin_ruta_t"]          # carga que sí toma la ruta alterna
    t["cop_por_t_desviada"] = (t["sobrecosto_cop_anual"] / desviada).where(desviada > 0)
    t[COL_DIAS] = t["sobrecosto_cop_anual"] * c.DIAS_CIERRE / 365
    t["grupo"] = clasificar(t)
    t = t.sort_values(["sin_ruta_t", "sobrecosto_cop_anual"], ascending=False)
    t.insert(0, "rango", range(1, len(t) + 1))
    t.round(1).to_csv(c.RESULTADOS / "cierres_aristas.csv", index=False)

    # ---- 2. cierre de cada tramo de INVIAS: se quitan todas las aristas que lo recorren
    tramos = pd.read_csv(c.GRAFO / "tramos.csv", dtype={"codigo_via": str})
    usa = aristas_por_tramo(G, tramos, pd.read_csv(c.GRAFO / "tramos_por_arista.csv"))
    calculado = {}                               # varios tramos cierran las mismas aristas
    filas = []
    for f in tramos[tramos["id_tramo"].isin(usa)].itertuples():
        S = usa[f.id_tramo]
        clave = frozenset(frozenset(e) for e in S)
        if clave not in calculado:
            calculado[clave] = simular_cierre(G, od, base, S)
        I, D = calculado[clave]
        filas.append({"id_tramo": f.id_tramo, "codigo_via": f.codigo_via, "sector": f.sector,
                      "km_tramo": f.km, "aristas_cerradas": ", ".join(G.edges[e]["id_arista"] for e in S),
                      "sobrecosto_cop_anual": I, "sin_ruta_t": D})
    tr = pd.DataFrame(filas).sort_values(["sin_ruta_t", "sobrecosto_cop_anual"], ascending=False)
    tr.round(1).to_csv(c.RESULTADOS / "cierres_tramos.csv", index=False)

    # ---- resumen en pantalla
    pd.set_option("display.width", 170)
    mm = lambda s: (s / 1e9).round(1)          # miles de millones de COP
    print("PUENTES (su cierre deja carga sin ruta):")
    p = t[t["es_puente"]]
    print(pd.DataFrame({"arista": p["nombre"], "sin ruta (Mt/año)": (p["sin_ruta_t"] / 1e6).round(2),
                        "sobrecosto resto (mil M COP/año)": mm(p["sobrecosto_cop_anual"])}).to_string(index=False))
    print(f"\nTop {c.TOP} aristas con alternativa, por SOBRECOSTO anual (miles de millones COP):")
    r = t[~t["es_puente"]].head(c.TOP)
    print(pd.DataFrame({"arista": r["nombre"], "carga Mt": (r["carga_t"] / 1e6).round(2),
                        "sobrecosto anual": mm(r["sobrecosto_cop_anual"]),
                        f"{c.DIAS_CIERRE} días": mm(r[COL_DIAS]),
                        "COP por t desviada": r["cop_por_t_desviada"].round(0),
                        "grupo": r["grupo"]}).to_string(index=False))
    print("\nAristas por grupo:")
    print(t["grupo"].value_counts().to_string())
    print(f"\nTramos de INVIAS simulados: {len(tr)} ({len(calculado)} cierres distintos).")
    print(f"Archivos en {c.RESULTADOS}")


if __name__ == "__main__":
    main()
