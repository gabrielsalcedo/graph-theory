# Vulnerabilidad de la red vial primaria de carga de Colombia

Proyecto del curso **Teoría de Grafos** (prof. Daniel Bojacá, MACC, Universidad del
Rosario, 2026-II). Autores: David Catral, Gabriel Salcedo e Isaac Suárez (Escuela de
Economía y Negocios).

**Pregunta.** ¿Qué tramos de la red vial primaria de carga causan el mayor daño
económico cuando se cierran, medido como (a) el sobrecosto de transporte, en pesos, de la
carga que encuentra un desvío y (b) las toneladas que se quedan sin ninguna ruta?

**Hipótesis.** La posición de un tramo en la red (intermediación), su uso (la carga que
lo atraviesa) y la consecuencia de perderlo (el sobrecosto) no coinciden; en esas
diferencias están los tramos sobrestimados o subestimados.

**Modelo.** La red se representa con un grafo simple, no dirigido y ponderado: los
vértices son las 25 ciudades (o áreas metropolitanas) con más carga y 28 cruces donde se
separan las rutas; las aristas son 77 corredores viales. El peso de cada arista es el
costo de mover una tonelada por ella, `w = 248,6 COP/t-km × km`. La demanda es la matriz
origen-destino de toneladas del RNDC 2015. El paso a paso y las decisiones están en
[AUDITORIA.md](AUDITORIA.md).

![Grafo de análisis](outputs/figuras/grafo_analisis_mapa.png)

## Estructura

```
graph-theory/
├── README.md                  este archivo
├── AUDITORIA.md               revisión del repositorio, diferencias y decisiones
├── environment.yml            entorno de Python con versiones fijas (conda)
├── requirements.txt           las mismas versiones, para pip (Google Colab)
├── graphs-appl-ports.Rproj    proyecto de RStudio (para el script de R)
├── data/
│   ├── raw/                   datos crudos; ver data/raw/README.md
│   │   ├── invias/            red vial de INVIAS partida en 11 archivos
│   │   ├── base1.zip, base2.zip   RNDC 2015 comprimido
│   │   └── divipola.csv       municipios del DANE
│   ├── final/                 salidas de 01_limpieza_rndc.R (las lee Python)
│   └── pruebas/               grafo de juguete con respuestas calculadas a mano
├── scripts/
│   ├── config.py              ÚNICO archivo de parámetros y rutas
│   ├── 00_preparar_datos.py   descomprime el RNDC (solo ruta completa)
│   ├── 01_limpieza_rndc.R     limpia RNDC y DIVIPOLA -> data/final/
│   ├── 02_red_detallada.py    red INVIAS limpia con 50 ciudades: red detallada D
│   ├── 03_grafo_analisis.py   grafo de análisis G (53 vértices, 77 aristas)
│   ├── 04_validacion_y_descripcion.py  propiedades de G y validación con el RNDC
│   ├── 05_simulacion_cierres.py        cierre de cada arista y tramo: I y D
│   ├── 06_pruebas.py          9 pruebas con respuestas a mano
│   ├── 07_intermediacion_y_carga.py    intermediación vs carga asignada
│   ├── 08_figuras.py          todas las figuras
│   ├── ejecutar_todo.py       corre del 02 al 08 en orden
│   ├── app_rutas.py           herramienta: origen, destino y cierres -> ruta alterna
│   ├── dividir_invias.py      parte la red vial descargada en 11 archivos
│   └── vial/                  módulos (una responsabilidad cada uno)
│       ├── carga.py           leer red, municipios y matriz O-D
│       ├── limpieza.py        limpieza topológica del mapa
│       ├── grafo.py           red detallada D
│       ├── costo.py           peso de las aristas
│       ├── ciudades.py        grafo de análisis G
│       ├── archivos.py        guardar y leer los grafos
│       ├── rutas.py           Dijkstra propio (montículo binario)
│       ├── centralidad.py     intermediación (Brandes) y asignación todo o nada
│       ├── validacion.py      propiedades y comparación con el RNDC
│       ├── cierres.py         simulación de cierres (Algoritmo 1)
│       ├── figuras.py         dibujo de las figuras
│       └── reporte.py         reportes de construcción
├── outputs/
│   ├── grafo/                 G en CSV (vertices.csv, aristas.csv), O-D entre ciudades
│   ├── resultados/            reportes y tablas
│   └── figuras/               figuras de los documentos
└── informe/                   documentos en LaTeX (entregas)
```

## Cómo reproducir el proyecto

Hay dos rutas. La **rápida** parte de `data/final/` (ya incluido) y no necesita R ni
descargas. La **completa** parte de los datos crudos y repite también la limpieza en R.
Las dos dan los mismos archivos.

### Instalar el entorno (una vez)

**En un computador** (Windows, macOS o Linux) con [Miniconda](https://docs.conda.io/en/latest/miniconda.html):

```bash
git clone https://github.com/gabrielsalcedo/graph-theory.git
cd graph-theory
conda env create -f environment.yml
conda activate vial
```

> Active siempre el entorno con `conda activate vial` antes de correr los scripts. En
> Windows, si se llama a `python.exe` del entorno sin activarlo, numpy se cierra sin
> mensaje en el paso 07 (no encuentra las librerías de MKL).

**En Google Colab** (no verificado aún con estas versiones; ver la nota de abajo):

```python
!git clone https://github.com/gabrielsalcedo/graph-theory.git
%cd graph-theory
!pip install -r requirements.txt
# Si Colab pide reiniciar la sesión, reinicie y vuelva a: %cd /content/graph-theory
```

Nota: con pip, shapely trae su propia versión de GEOS. Si la red detallada no da
842 nodos y 972 aristas, las cifras pueden diferir un poco; use conda para replicar
exactamente. La herramienta `app_rutas.py` abre una ventana y no funciona en Colab.

### Ruta rápida (desde `data/final/`)

```bash
python scripts/ejecutar_todo.py
```

Tarda cerca de 2,5 minutos y corre, en orden, los pasos 02 a 08. Se detiene si algo falla
(también si falla una prueba). Cada paso se puede correr solo, en el mismo orden:

| Paso | Comando | Produce | Tiempo |
|---|---|---|---|
| 02 | `python scripts/02_red_detallada.py` | `outputs/grafo/red_detallada.pkl`, `red_detallada.csv`; `outputs/resultados/reporte_red_detallada.txt` | ~40 s |
| 03 | `python scripts/03_grafo_analisis.py` | `outputs/grafo/vertices.csv`, `aristas.csv`, `od_ciudades.csv`, `tramos.csv`, `tramos_por_arista.csv`; `reporte_grafo_analisis.txt` | ~2 min |
| 04 | `python scripts/04_validacion_y_descripcion.py` | `outputs/resultados/validacion.txt`, `validacion_pares_rndc.csv` | 2 s |
| 05 | `python scripts/05_simulacion_cierres.py` | `outputs/resultados/cierres_aristas.csv`, `cierres_tramos.csv` | 3 s |
| 06 | `python scripts/06_pruebas.py` | en pantalla: `9/9 pruebas superadas` | 2 s |
| 07 | `python scripts/07_intermediacion_y_carga.py` | `outputs/resultados/intermediacion_y_carga.csv` | 30 s |
| 08 | `python scripts/08_figuras.py` | `outputs/figuras/*.png` | 10 s |

**La etapa de modelamiento** (red detallada, grafo de análisis, validación y descripción
estructural) son los pasos 02, 03 y 04. Los pasos 05 y 07 son la siguiente etapa
(implementación: cierres, intermediación y carga); su código ya está y corre, y sus
resultados todavía no están en los documentos entregados.

### Ruta completa (desde los datos crudos)

1. Si quiere descargar de nuevo la red vial, siga `data/raw/README.md`, guárdela como
   `data/raw/invias.geojson` y córtela con `python scripts/dividir_invias.py`. Si no, use
   las 11 partes que ya vienen en `data/raw/invias/`.
2. Descomprima el RNDC: `python scripts/00_preparar_datos.py` (crea `data/raw/base1.csv`
   y `base2.csv`, que no se suben a GitHub).
3. Limpie el RNDC y DIVIPOLA en R (paquetes `here`, `dplyr`, `readr`, `stringr`). Abra
   `graphs-appl-ports.Rproj` en RStudio y corra `scripts/01_limpieza_rndc.R`, o desde la
   carpeta raíz:

   ```bash
   Rscript scripts/01_limpieza_rndc.R
   ```

   Tarda unos 20 s y reescribe `data/final/` con los mismos archivos que trae el
   repositorio (comprobado byte a byte con R 4.5.2).
4. Siga con la ruta rápida: `python scripts/ejecutar_todo.py`.

### La herramienta

```bash
cd scripts
python app_rutas.py
```

Se elige el origen, el destino y una o varias vías cerradas (Ctrl + clic). La ventana
muestra la ruta normal, la ruta alterna, los km extra, el sobrecosto por tonelada y, con
las toneladas del RNDC de esa pareja, el sobrecosto al año y en N días. Si no queda ruta,
lo dice. Necesita haber corrido hasta el paso 03.

## Resultados esperados

Si replica el proyecto, estas son las cifras que debe obtener (entorno de
`environment.yml`). Todas salen de los scripts; ninguna está escrita a mano.

| Cifra | Valor | Dónde aparece |
|---|---|---|
| Tramos y km de la capa de INVIAS | 652 tramos, 20.011 km (12 fuera de servicio, 9 km) | `reporte_red_detallada.txt` [A] |
| Carga de las 50 ciudades con más carga | 74,5 % de las toneladas | `reporte_red_detallada.txt` [A] |
| Componentes conexas antes / después de limpiar | 464 / 22 | `reporte_red_detallada.txt` [B] |
| Red detallada D | 842 nodos, 972 aristas, 11.866 km, conexa | `reporte_red_detallada.txt` [C] |
| Áreas metropolitanas | 50 ciudades → 38 áreas → 25 vértices ciudad | `reporte_grafo_analisis.txt` [D] |
| Grafo de análisis G | 53 vértices (25 ciudades + 28 cruces), 77 aristas, conexo, planar | `reporte_grafo_analisis.txt` [D], `validacion.txt` |
| Distancias de G frente a D | +4,0 % en promedio, máximo +21,4 % | `reporte_grafo_analisis.txt` [D] |
| Carga O-D entre las ciudades de G | 43,7 millones de t, 47,0 % del total, 571 pares | `reporte_grafo_analisis.txt` [E] |
| Grado medio, mínimo, máximo | 2,91; 1; 5 | `validacion.txt` |
| Diámetro (en aristas) | 14 | `validacion.txt` |
| κ(G), λ(G) | 1, 1 | `validacion.txt` |
| Puentes (3) | Buenaventura–Dagua, Villavicencio–Puerto Gaitán, Sonsón–Rionegro | `validacion.txt` |
| Vértices de corte (3) | Dagua, Rionegro, Villavicencio | `validacion.txt` |
| km del grafo / km del RNDC (300 pares) | 1,041 ponderado por toneladas; mediana 1,028 | `validacion.txt` |
| Pruebas | 9/9 | `06_pruebas.py` |
| Intermediación: primera arista | Buga–Zarzal, 32 % de los pares de ciudades | `intermediacion_y_carga.csv` |
| Spearman intermediación vs carga | 0,76 | `07_intermediacion_y_carga.py` |
| Cierre con más sobrecosto | Buga–Zarzal, 908,6 mil millones COP/año | `cierres_aristas.csv` |
| Tramos de INVIAS simulados | 243 (100 cierres distintos) | `05_simulacion_cierres.py` |

## De dónde sale cada cifra y figura de la entrega 2

| En el documento (`informe/entrega2/`) | Valor | Fuente |
|---|---|---|
| Viajes y toneladas de 2015 (Sección II) | ~6 millones de viajes; ver AUDITORIA.md sobre las toneladas | `01_limpieza_rndc.R`, sección 6 de su salida |
| Red de INVIAS (Sección V) | 652 tramos, 20.011 km | paso 02 |
| Tolerancia de unión | 50 m | `config.py` (`UNION_M`) |
| Ciudades y cruces | 25 ciudades, 28 cruces, 77 corredores | paso 03 |
| Parejas O-D entre municipios | 42.547 | `01_limpieza_rndc.R` (`matriz_od.csv`) |
| Carga entre las 25 ciudades | 47 % | paso 03 |
| Tarifa `c` | 248,6 COP/t-km | promedio de `COSTO_TKM_PONDERADO` en `data/final/costo_por_config.csv`, ponderado por `TONELADAS`, filas con `CONFIABLE = TRUE` (da 248,63) |
| Diferencia con los km del RNDC | 4 % | paso 04 |
| Puentes | Buenaventura–Dagua, Villavicencio–Puerto Gaitán, Rionegro–Sonsón | paso 04 |
| Fig. 1 | `outputs/figuras/grafo_analisis_mapa.png` | paso 08 |

Las demás figuras: `red_detallada.png` y `grafo_analisis.png` (paso 08, modelamiento);
`intermediacion.png`, `carga_vs_intermediacion.png`, `cuadrantes.png` y
`mapa_criticos.png` (paso 08, a partir de los pasos 05 y 07).

## Supuestos del modelo

Demanda fija; sin congestión (el sobrecosto es un mínimo); tarifa única en toda la red
(la ruta más barata es la más corta); entre dos nodos se conserva solo el corredor más
barato; se simulan cierres de una arista o de un tramo a la vez.

## Fuentes de datos

- **Red vial:** INVIAS, publicada por OCHA Colombia en HDX como
  [Colombia: Roads](https://data.humdata.org/dataset/colombia-roads).
- **Carga:** Registro Nacional de Despachos de Carga (RNDC) 2015, Ministerio de Transporte.
- **Municipios:** DIVIPOLA, DANE.

Detalles de cada archivo (versión, fecha, tamaño, cómo descargarlo) en
[data/raw/README.md](data/raw/README.md).
