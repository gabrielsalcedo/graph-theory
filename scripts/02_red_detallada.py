"""
PASO 02 — De la capa de INVIAS a la red detallada D (841 nodos, 970 aristas).

  A  Leer la red (une las 11 partes de data/raw/invias/) y los municipios
  B  Limpiar el mapa: duplicados, cruces sin vértice común, extremos separados
  C  Red detallada: grafo de la red limpia con las 50 ciudades conectadas

Entradas: data/raw/invias/invias_parte_*.geojson, data/final/nodos_demanda.csv
Salidas : outputs/grafo/red_detallada.pkl (la lee el paso 03), red_detallada.csv (dibujo)
          outputs/resultados/reporte_red_detallada.txt
"""

import config as c
from vial import archivos, carga, grafo, limpieza
from vial.reporte import anotar, guardar_reporte


def main():
    red, todos = carga.leer_red(), carga.leer_municipios()
    ciudades = todos.nlargest(c.N_CIUDADES, "ton_total")
    anotar(f"[A] Las {c.N_CIUDADES} ciudades con más carga suman "
           f"{100 * ciudades['ton_total'].sum() / todos['ton_total'].sum():.1f} % de las toneladas.")
    seg = limpieza.limpiar(red)
    D = grafo.red_detallada(seg, ciudades)
    archivos.guardar_red_detallada(D)
    guardar_reporte(c.REPORTE_RED)
    print(f"\nRed detallada guardada en {c.RED_DETALLADA_PKL}")


if __name__ == "__main__":
    main()
