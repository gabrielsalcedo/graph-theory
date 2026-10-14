"""
CONFIGURACIÓN ÚNICA DEL PROYECTO.

Todos los parámetros del modelo están aquí. Si se cambia uno, hay que volver a correr
ejecutar_todo.py (o desde 02_construir_grafo.py en adelante). Los marcados PROVISIONAL son
decisiones de modelamiento; su justificación está en RECUENTO.md y en
outputs/reporte_modelamiento/.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # carpeta graphs-appl/
DATOS = RAIZ / "data"
SALIDAS = RAIZ / "outputs"

# ---------------------------------------------------------------------------
# 1. Archivos
# ---------------------------------------------------------------------------
# Red vial primaria de INVIAS (HDX "Colombia: Roads"). Si no está el .geojson
# (250 MB, no cabe en GitHub) se lee el comprimido invias.zip directamente.
ARCHIVO_RED = (DATOS / "raw" / "invias.geojson"
               if (DATOS / "raw" / "invias.geojson").exists()
               else DATOS / "raw" / "invias.zip")
# Salidas de scripts/01_limpieza_rndc.R
ARCHIVO_MUNICIPIOS = DATOS / "final" / "nodos_demanda.csv"   # un punto por municipio + toneladas
ARCHIVO_OD = DATOS / "final" / "matriz_od.csv"               # matriz origen-destino limpia
# Grafo de juguete con respuestas conocidas (lo usa 06_pruebas.py)
ARCHIVO_JUGUETE = DATOS / "pruebas" / "grafo_juguete.json"

CARPETA_SALIDA = SALIDAS / "resultados"
CARPETA_FIGURAS = SALIDAS / "figuras"
ARCHIVO_GRAFO = CARPETA_SALIDA / "grafo.pkl"                 # grafo de análisis
ARCHIVO_DETALLADO = CARPETA_SALIDA / "grafo_detallado.pkl"   # red detallada

# ---------------------------------------------------------------------------
# 2. Columnas: nombre en el archivo -> nombre interno
# ---------------------------------------------------------------------------
COLUMNAS_RED = {
    "objectid":      "id_tramo",
    "codigotramo":   "codigo_via",     # p. ej. "4510" = ruta 45, tramo 10
    "nombreruta":    "cod_tramo",      # nombre del corredor ("Troncal del Magdalena")
    "sector":        "nombre_tramo",   # "Aguachica – Gamarra" (nombretramo viene vacío)
    "ruta":          "ruta",
    "administrador": "administrador",
    "superficie":    "superficie",
    "calzada":       "calzada",
}
COLUMNAS_MUNICIPIOS = {
    "COD":          "cod_mpio",
    "NOMBRE_MPIO":  "nombre",
    "DEPARTAMENTO": "departamento",
    "LON":          "lon",
    "LAT":          "lat",
    "TON_TOTAL":    "ton_total",       # toneladas que salen + llegan
}
COLUMNAS_OD = {
    "ORIGEN":    "cod_origen",
    "DESTINO":   "cod_destino",
    "VIAJES":    "viajes",
    "TONELADAS": "toneladas",
}

# Código de 'superficie' que significa AFIRMADO (sin pavimentar). PROVISIONAL: el archivo
# trae 1, 2, 3 sin diccionario; 567 de 652 tramos son "3" (supuesto: pavimentado).
SUPERFICIE_AFIRMADO = "1"
# Tramos que se descartan (búsqueda en el nombre del tramo).
EXCLUIR_TRAMOS_CON_NOMBRE = "fuera de servicio"

# ---------------------------------------------------------------------------
# 3. Sistemas de referencia
# ---------------------------------------------------------------------------
CRS_ENTRADA_RED = "EPSG:4326"      # solo se usa si el archivo no trae CRS
# EPSG:9377 = MAGNA-SIRGAS 2018 / Origen-Nacional: proyección oficial de Colombia, en
# METROS y con poca deformación en todo el país.
CRS_METRICO = "EPSG:9377"
LIMITES_COLOMBIA = (-82.0, -4.5, -66.5, 13.6)   # lon_min, lat_min, lon_max, lat_max

# ---------------------------------------------------------------------------
# 4. Limpieza topológica de la red (vial/limpieza.py)
# ---------------------------------------------------------------------------
SIMPLIFICAR_GEOMETRIA_M = 5.0           # Douglas-Peucker: 5,7 M -> 148 mil vértices, -0,28 % km
TOLERANCIA_UNION_M = 50.0               # PROVISIONAL: con 10 m quedan 114 componentes
TOLERANCIA_DUPLICADO_M = 30.0           # línea contenida en este buffer de otra = duplicado
FUSIONAR_CALZADAS_DOBLES = True         # dos calzadas -> una arista calzada = "2"
CORREGIR_COORDENADAS_INVERTIDAS = True  # (lat, lon) invertidas se corrigen si caen en Colombia
TOLERANCIAS_SENSIBILIDAD_M = [5, 10, 25, 50, 100]   # se reportan componentes con cada una

# ---------------------------------------------------------------------------
# 5. Red detallada (vial/grafo.py)
# ---------------------------------------------------------------------------
N_CIUDADES = 50                         # municipios con más carga que se conectan (74,5 % t)
DISTANCIA_MAX_CONEXION_M = 10_000       # PROVISIONAL: radio de conexión de una cabecera
RADIO_CONEXION_ESPECIAL_M = {"11001": 20_000}   # Bogotá: troncales del norte a ~19 km
FACTOR_SINUOSIDAD_CONECTOR = 1.3        # km del conector = línea recta × factor
CONECTAR_TODAS_LAS_RUTAS_CERCANAS = True  # travesías urbanas (INVIAS no tiene calles)
PODAR_RAMAS_SIN_CIUDAD = True           # quita componentes sin ciudad y ramales sin salida
CONTRAER_ARISTAS_MENORES_M = 1_000      # PROVISIONAL: dobles calzadas e intercambiadores

# ---------------------------------------------------------------------------
# 6. Grafo de análisis (vial/ciudades.py) — el grafo que se estudia
# ---------------------------------------------------------------------------
N_NODOS_CIUDADES = 25                   # PROVISIONAL: ciudades/áreas metropolitanas
RADIO_AGLOMERACION_M = 25_000           # PROVISIONAL: municipios que se funden en un área
RADIO_CRUCES_M = 25_000                 # PROVISIONAL: bifurcaciones que se agrupan
EPS_REDUNDANCIA = 0.0                   # spanner: se quita A–B si otro camino cuesta <= (1+eps)·w

# ---------------------------------------------------------------------------
# 7. Costo económico (vial/costo.py)
# ---------------------------------------------------------------------------
# COP de 2015 por tonelada-km: promedio de COSTO_TKM_PONDERADO de
# data/final/costo_por_config.csv, ponderado por toneladas, configuraciones CONFIABLE.
COSTO_COP_TON_KM = 248.6                # PROVISIONAL

# ---------------------------------------------------------------------------
# 8. Centralidad
# ---------------------------------------------------------------------------
TOP_ARISTAS_CRITICAS = 15
