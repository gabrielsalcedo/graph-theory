# Datos crudos

Qué es cada archivo de esta carpeta, de dónde sale y cómo volver a descargarlo. Donde
dice **PENDIENTE** falta el dato y hay que completarlo; no se inventó ninguna fuente.

| Archivo en el repositorio | Tamaño | ¿Se sube a GitHub? |
|---|---|---|
| `invias/invias_parte_01.geojson` … `invias_parte_11.geojson` | 11 partes de 10–25 MB (250 MB en total) | Sí |
| `invias.geojson` (descarga original) | 250,2 MB | No (`.gitignore`) |
| `base1.zip`, `base2.zip` | 14,9 MB y 14,6 MB | Sí |
| `base1.csv`, `base2.csv` (se obtienen al descomprimir) | 143,7 MB y 155,0 MB | No (`.gitignore`) |
| `divipola.csv` | 0,75 MB | Sí |

## 1. Red vial primaria (INVIAS)

| | |
|---|---|
| Nombre | *Colombia: Roads* |
| Institución | Instituto Nacional de Vías (INVIAS); publicada por OCHA Colombia en Humanitarian Data Exchange (HDX) |
| Enlace | https://data.humdata.org/dataset/colombia-roads |
| Archivo descargado | GeoJSON con la capa `RedVial` (así se llama dentro del archivo). Nombre exacto del recurso en HDX: **PENDIENTE** |
| Versión | **PENDIENTE** (fecha de actualización del recurso en HDX; `references.bib` cita 2024) |
| Fecha de consulta | Octubre de 2026 (según `references.bib`) |
| Contenido | 652 tramos (`MultiLineString`), 20.011 km, CRS EPSG:4326, 24 columnas (`objectid`, `codigotramo`, `sector`, `ruta`, …) |
| Licencia | CC BY 4.0 (según `references.bib`) |
| Carpeta | Descargar como `data/raw/invias.geojson` y partir con `python scripts/dividir_invias.py`, que deja las 11 partes en `data/raw/invias/` |

Las partes son el archivo original cortado por tramos, sin cambiar ningún dato: el paso 02
las une al leerlas. Se comprobó que la descarga de octubre de 2026 es idéntica a las
partes del repositorio (mismos 652 tramos, columnas, geometrías y CRS).

## 2. Registro Nacional de Despachos de Carga (RNDC) 2015

| | |
|---|---|
| Nombre | Registro Nacional de Despachos de Carga por Carretera |
| Institución | Ministerio de Transporte de Colombia |
| Enlace | https://www.datos.gov.co/Transporte/Registro-Nacional-de-Despachos-de-Carga-por-Carret/vn9u-yhwq (conjunto `vn9u-yhwq`, tomado de `references.bib`) |
| Archivos | `base1.csv` y `base2.csv`: los registros de 2015, exportados en dos partes por el límite de filas de Excel (1.048.001 filas en total). Filtro y forma exacta de la exportación: **PENDIENTE** |
| Versión | Registros del año 2015 |
| Fecha de consulta | Octubre de 2026 (según `references.bib`) |
| Carpeta | `data/raw/`. En el repositorio vienen comprimidos; `python scripts/00_preparar_datos.py` los descomprime |

## 3. DIVIPOLA

| | |
|---|---|
| Nombre | Codificación de la División Político-Administrativa de Colombia (DIVIPOLA) |
| Institución | Departamento Administrativo Nacional de Estadística (DANE) |
| Enlace | https://www.dane.gov.co/index.php/sistema-estadistico-nacional-sen/normas-y-estandares/nomenclaturas-y-clasificaciones/nomenclaturas/codificacion-de-la-division-politico-administrativa-de-colombia-divipola (tomado de `references.bib`) |
| Archivo | `divipola.csv`: municipios y centros poblados con código y coordenadas (8.161 filas). Nombre del archivo original en el sitio del DANE: **PENDIENTE** |
| Versión | 2023 |
| Fecha de consulta | Octubre de 2026 (según `references.bib`) |
| Carpeta | `data/raw/divipola.csv` |

## Qué produce cada fuente

`scripts/01_limpieza_rndc.R` lee el RNDC y la DIVIPOLA y escribe en `data/final/`:
`matriz_od.csv` (42.547 pares O-D, 92,99 millones de t), `nodos_demanda.csv` (un punto
por municipio) y `costo_por_config.csv` (costo por tonelada-km por tipo de vehículo).
Esos tres archivos vienen en el repositorio, así que para construir el grafo no hace
falta R ni descomprimir nada.
