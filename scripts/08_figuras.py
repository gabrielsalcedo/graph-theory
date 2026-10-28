"""
PASO 08 — Figuras para los documentos. Solo dibuja; nada se edita a mano.

Modelamiento (necesitan los pasos 02 y 03):
  red_detallada.png            red INVIAS limpia
  grafo_analisis_mapa.png      grafo de análisis con el trazado real (Fig. 1 de la entrega 2)
  grafo_analisis.png           grafo de análisis como diagrama
Implementación (solo si ya existen las tablas de los pasos 05 y 07):
  intermediacion.png, carga_vs_intermediacion.png, cuadrantes.png, mapa_criticos.png

Salidas en outputs/figuras/.
"""

import pandas as pd

import config as c
from vial import figuras
from vial.archivos import cargar_grafo


def main():
    print("Figuras guardadas:")
    G = cargar_grafo()
    figuras.red_detallada(G)
    figuras.grafo_analisis(G)

    tabla = c.RESULTADOS / "intermediacion_y_carga.csv"
    if tabla.exists():
        t = pd.read_csv(tabla)
        figuras.intermediacion(G, t)
        figuras.carga_vs_intermediacion(t)
    else:
        print(f"  (falta {tabla.name}: corra 07_intermediacion_y_carga.py)")

    tabla = c.RESULTADOS / "cierres_aristas.csv"
    if tabla.exists():
        cierres = pd.read_csv(tabla)
        figuras.cuadrantes(cierres)
        figuras.mapa_criticos(G, cierres)
    else:
        print(f"  (falta {tabla.name}: corra 05_simulacion_cierres.py)")


if __name__ == "__main__":
    main()
