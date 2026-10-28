"""
PASO 03 — De la red detallada D al grafo de análisis G (53 vértices, 77 aristas).

  D  Grafo de análisis: 25 ciudades + cruces donde se separan las rutas
  E  Guardar G en CSV, los tramos de INVIAS que recorre y la matriz O-D entre ciudades

Entradas: outputs/grafo/red_detallada.pkl (paso 02), data/raw/invias/ (para los tramos),
          data/final/nodos_demanda.csv, data/final/matriz_od.csv
Salidas : outputs/grafo/vertices.csv, aristas.csv, od_ciudades.csv, tramos.csv,
          tramos_por_arista.csv; outputs/resultados/reporte_grafo_analisis.txt
"""

import config as c
from vial import archivos, carga, ciudades
from vial.reporte import guardar_reporte


def main():
    D = archivos.leer_red_detallada()
    todos, od = carga.leer_municipios(), carga.leer_od()
    G, mun = ciudades.grafo_de_analisis(D, todos)
    archivos.guardar_grafo(G, mun, od, carga.leer_red(reportar=False))
    guardar_reporte(c.REPORTE_GRAFO)
    print(f"\nGrafo guardado en {c.GRAFO}")


if __name__ == "__main__":
    main()
