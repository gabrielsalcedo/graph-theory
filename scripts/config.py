"""
PARÁMETROS DEL PROYECTO (único archivo que se cambia).

Todas las rutas, parámetros del modelo y constantes de los scripts están aquí.
Si cambia un parámetro de las secciones 3 a 6, vuelva a correr ejecutar_todo.py.
La justificación de cada valor está en RECUENTO.md.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # carpeta raíz del repositorio

# ---------------------------------------------------------------- 1. Datos de entrada
CARPETA_RAW = RAIZ / "data/raw"
# Red vial de INVIAS (HDX "Colombia: Roads"). El archivo descargado pesa 250 MB y no se
# sube: se parte en 11 archivos de < 25 MB con dividir_invias.py y el paso 02 los une.
RED_VIAL_COMPLETA = CARPETA_RAW / "invias.geojson"
CARPETA_PARTES_RED = CARPETA_RAW / "invias"
N_PARTES_RED = 11
PARTES_RED_VIAL = [CARPETA_PARTES_RED / f"invias_parte_{i:02d}.geojson"
                   for i in range(1, N_PARTES_RED + 1)]
TAMANO_MAX_PARTE = 25_000_000                        # bytes por parte (GitHub avisa > 50 MB)
# RNDC 2015, comprimido (el .csv pesa > 100 MB). 00_preparar_datos.py lo descomprime.
ZIPS_RNDC = [CARPETA_RAW / "base1.zip", CARPETA_RAW / "base2.zip"]

MUNICIPIOS = RAIZ / "data/final/nodos_demanda.csv"   # salida de 01_limpieza_rndc.R
MATRIZ_OD = RAIZ / "data/final/matriz_od.csv"        # salida de 01_limpieza_rndc.R
JUGUETE = RAIZ / "data/pruebas/grafo_juguete.json"   # grafo pequeño para las pruebas

# ---------------------------------------------------------------- 2. Salidas
GRAFO = RAIZ / "outputs/grafo"            # el grafo de análisis en CSV (paso 03)
RESULTADOS = RAIZ / "outputs/resultados"  # tablas y reportes
FIGURAS = RAIZ / "outputs/figuras"        # figuras de los documentos
# Red detallada D con su geometría: la produce el paso 02 y la lee el paso 03.
# Pesa poco, pero se regenera siempre, así que no se sube (.gitignore: *.pkl).
RED_DETALLADA_PKL = GRAFO / "red_detallada.pkl"
REPORTE_RED = RESULTADOS / "reporte_red_detallada.txt"      # lo que anota el paso 02
REPORTE_GRAFO = RESULTADOS / "reporte_grafo_analisis.txt"   # lo que anota el paso 03

# Proyección oficial de Colombia (MAGNA-SIRGAS Origen Nacional): mide en metros.
CRS_METRICO = "EPSG:9377"
CRS_GEOGRAFICO = "EPSG:4326"              # longitud y latitud (DIVIPOLA, tablas de salida)

# ---------------------------------------------------------------- 3. Limpieza de la red
EXCLUIR_SECTOR = "fuera de servicio"      # tramos que se descartan (texto en 'sector')
SIMPLIFICAR_M = 5        # Douglas-Peucker: quita vértices sobrantes (-0,28 % de km)
DUPLICADO_M = 30         # línea dentro de 30 m de otra más larga = duplicado o 2.ª calzada
UNION_M = 50             # extremos a menos de 50 m se unen (con 10 m quedan 114 componentes)

# ---------------------------------------------------------------- 4. Red detallada
N_CIUDADES = 50          # municipios con más carga que se conectan a la red (74,5 % de t)
RADIO_CONEXION_M = 10_000            # una ciudad se une a las vías a menos de 10 km
COD_BOGOTA = "11001"
RADIO_BOGOTA_M = 20_000              # Bogotá: las troncales del norte empiezan a ~19 km
SINUOSIDAD_CONECTOR = 1.3            # km del conector = línea recta x 1,3
ANCLAJE_EXTREMO_M = 1.0              # un anclaje a < 1 m del extremo usa el nodo existente
CONTRAER_M = 1_000                   # aristas < 1 km (intercambiadores) se funden

# ---------------------------------------------------------------- 5. Grafo de análisis
N_VERTICES_CIUDAD = 25   # ciudades o áreas metropolitanas con más carga
RADIO_AREA_M = 25_000    # municipios a menos de 25 km forman un área metropolitana
RADIO_CRUCES_M = 25_000  # bifurcaciones a menos de 25 km se agrupan en un cruce

# ---------------------------------------------------------------- 6. Costo
# Flete promedio del RNDC (COP de 2015 por tonelada-km), ponderado por toneladas, de las
# 7 configuraciones de vehículo confiables de data/final/costo_por_config.csv.
TARIFA_COP_TKM = 248.6
# peso de cada arista: w = km x TARIFA = costo de mover una tonelada por ella

# ---------------------------------------------------------------- 7. Validación
N_PARES_VALIDACION = 300  # pares O-D con más toneladas que se comparan con el RNDC

# ---------------------------------------------------------------- 8. Cierres
DIAS_CIERRE = 14          # cierre corto de ejemplo (p. ej. un derrumbe de dos semanas)
# Un tramo de INVIAS cierra una arista si recorre al menos 1 km de ella, o la mitad del
# tramo si este es más corto (así no cuentan los metros compartidos al entrar a una ciudad).
KM_MIN_TRAMO_EN_ARISTA = 1.0
FRACCION_MIN_TRAMO = 0.5

# ---------------------------------------------------------------- 9. Resultados y figuras
TOP = 15                  # cuántas aristas se muestran en los rankings
SIMPLIFICAR_SALIDA_G_M = 50     # trazado de las aristas de G en aristas.csv (solo dibujo)
SIMPLIFICAR_SALIDA_D_M = 200    # trazado de la red detallada en red_detallada.csv (solo dibujo)
DPI_FIGURAS = 250

# ---------------------------------------------------------------- 10. Pruebas
N_PARES_PRUEBA = 200      # pares al azar en que se compara el Dijkstra propio con networkx
SEMILLA_PRUEBA = 1
