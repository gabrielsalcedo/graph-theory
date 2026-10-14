"""
PASO 2 — Construye la red detallada y el grafo de análisis.

Entradas : data/raw/invias.geojson (o invias.zip), data/final/nodos_demanda.csv,
           data/final/matriz_od.csv
Salidas  : outputs/resultados/
  grafo.pkl                  GRAFO DE ANÁLISIS (53 vértices): el que usan los pasos 3 a 6
  grafo_detallado.pkl        red detallada (841 nodos)
  reporte_construccion.txt   bitácora de cada etapa (cuántos tramos, nodos, componentes…)
  municipios_conexion.csv    distancia de cada ciudad a la red y si quedó conectada
  duplicados_eliminados.csv  tramos duplicados que se quitaron en la limpieza
  aglomeracion.csv           a qué área metropolitana quedó asignado cada municipio
  od_ciudades.csv            matriz O-D agregada a las ciudades del grafo de análisis
  red_procesada.gpkg         capas para revisar en QGIS (opcional)

Etapas (ver RECUENTO.md):
  A. Carga de datos                       vial/carga.py
  B. Limpieza topológica de la red        vial/limpieza.py
  C. Red detallada                        vial/grafo.py
  D. Grafo de análisis                    vial/ciudades.py
  E. Costo de las aristas                 vial/costo.py (se aplica en C y D)

Ejecutar en Spyder con F5 (tarda ~1 min). Repetir cada vez que cambie config.py.
"""

import pickle
import warnings

import geopandas as gpd

import config
from vial import carga, ciudades, grafo, limpieza

warnings.filterwarnings("ignore", "GeoSeries.notna", UserWarning)


def _capas(G, prefijo):
    """Capas de aristas y nodos en red_procesada.gpkg (para revisar en QGIS)."""
    ruta = config.CARPETA_SALIDA / "red_procesada.gpkg"
    grafo.aristas_gdf(G).to_file(ruta, layer=prefijo + "aristas", driver="GPKG")
    nodos = gpd.GeoDataFrame(
        [{"nodo": n, **{k: v for k, v in d.items() if k not in ("x", "y")}}
         for n, d in G.nodes(data=True)],
        geometry=gpd.points_from_xy([d["x"] for _, d in G.nodes(data=True)],
                                    [d["y"] for _, d in G.nodes(data=True)]),
        crs=config.CRS_METRICO)
    nodos.to_file(ruta, layer=prefijo + "nodos", driver="GPKG")


def main():
    config.CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    reporte = []

    # A. Carga de datos -------------------------------------------------------------
    red = carga.cargar_red(reporte)
    municipios = carga.cargar_municipios(reporte)
    od = carga.cargar_od(reporte)
    total = od["toneladas"].sum()

    # B. Limpieza topológica ----------------------------------------------------------
    segmentos, duplicados, _ = limpieza.limpiar(red, reporte)

    # C. Red detallada ----------------------------------------------------------------
    M = grafo.construir(segmentos)
    estado = grafo.conectar_municipios(M, municipios, reporte)
    M = grafo.simplificar(M, reporte)
    M = grafo.podar(M, reporte)
    M = grafo.simplificar(M, reporte)              # la poda deja vértices de grado 2
    M = grafo.contraer_cortas(M, config.CONTRAER_ARISTAS_MENORES_M, reporte)
    M = grafo.podar(M, reporte)
    M = grafo.simplificar(M, reporte)
    D = grafo.a_grafo_simple(M)                    # aquí se asigna el costo (vial/costo.py)
    paralelas = sum(1 for *_, d in D.edges(data=True) if d["n_paralelas"] > 1)
    reporte.append(f"[red detallada] Grafo simple no dirigido: {D.number_of_nodes()} nodos, "
                   f"{D.number_of_edges()} aristas ({paralelas} con aristas paralelas).")
    conectadas = set(estado.loc[estado["conectado"], "cod_mpio"])
    dentro = od[od["cod_origen"].isin(conectadas) & od["cod_destino"].isin(conectadas)]
    reporte.append(f"[red detallada] Carga O-D entre las {len(conectadas)} ciudades conectadas: "
                   f"{dentro['toneladas'].sum():,.0f} t "
                   f"({100 * dentro['toneladas'].sum() / total:.1f} % del total).")

    # D. Grafo de análisis ------------------------------------------------------------
    referencia = carga.cargar_referencia_municipios()
    G, mun = ciudades.construir(D, config.N_NODOS_CIUDADES, config.RADIO_AGLOMERACION_M,
                                config.RADIO_CRUCES_M, config.EPS_REDUNDANCIA,
                                referencia, reporte)
    odc = ciudades.od_ciudades(od, mun, G)
    reporte.append(f"[análisis] Carga O-D entre las ciudades del grafo: "
                   f"{odc['toneladas'].sum():,.0f} t "
                   f"({100 * odc['toneladas'].sum() / total:.1f} % del total) en {len(odc)} pares.")

    # Salidas -------------------------------------------------------------------------
    with open(config.ARCHIVO_DETALLADO, "wb") as f:
        pickle.dump(D, f)
    with open(config.ARCHIVO_GRAFO, "wb") as f:
        pickle.dump(G, f)
    _capas(D, "detallada_")
    _capas(G, "")
    odc.to_csv(config.CARPETA_SALIDA / "od_ciudades.csv", index=False)
    mun.to_csv(config.CARPETA_SALIDA / "aglomeracion.csv", index=False)
    estado.to_csv(config.CARPETA_SALIDA / "municipios_conexion.csv", index=False)
    duplicados.to_csv(config.CARPETA_SALIDA / "duplicados_eliminados.csv", index=False)
    texto = "\n".join(reporte)
    (config.CARPETA_SALIDA / "reporte_construccion.txt").write_text(texto, encoding="utf-8")
    print(texto)
    print(f"\nGrafos guardados en {config.CARPETA_SALIDA}")


if __name__ == "__main__":
    main()
