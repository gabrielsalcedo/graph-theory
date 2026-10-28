# Auditoría y migración del repositorio

Rama `revision-general`. Fuente de verdad: la carpeta `graphs-appl` (solo lectura: no se
editó, movió ni borró nada en ella). Este documento registra qué se encontró, qué se
cambió, las diferencias de cifras y lo que queda para el equipo.

## 1. Estado inicial

### 1.1 Dos versiones del proyecto

| | Clon de GitHub (`main`) | `graphs-appl` (local) |
|---|---|---|
| Código | paquete `scripts/vial/` (estructura de `CLAUDE.md`) | scripts planos `comun.py` + `02_`…`07_` |
| Cierres (`I`, `D`) | no existían | `05_simulacion_cierres.py` |
| Pruebas | 6 | 9 (con `I`/`D` a mano en el grafo de juguete) |
| Red INVIAS | solo `invias_parte_01.geojson` en la raíz; `config.py` esperaba `invias.geojson` o `invias.zip` (no estaban) | 11 partes en `data/raw/invias/` |
| `data/final/`, `outputs/` | vacíos (marcadores `m`, `e`) | completos |
| ¿Corría? | No | Sí |

Decisión del equipo: construir la versión definitiva en el clon con todo lo de
`graphs-appl`, reorganizado en el paquete `vial/`.

### 1.2 Sobrantes del clon (movidos a `_revisar/`, no borrados)

| Archivo | Contenido | ¿Está en `graphs-appl`? |
|---|---|---|
| `scripts/02_grafo.py`, marcadores `m` y `e` (6) | una línea en blanco | — |
| `scripts/limpieza_rndc.R` | idéntico a `01_limpieza_rndc.R` | sí |
| `invias_parte_01.geojson` (raíz) | igual a la parte 01, con fin de línea CRLF | sí |
| `scripts/data.py` | exploración inicial por celdas (duplicados del RNDC, Pareto, cruce con DIVIPOLA, topología); nombres de columna sin llenar, no corre | **no** |
| `scripts/invias.py` | visor de la red (20 líneas, usa `pyprojroot`) | **no** |
| `scripts/vial/*.py` anteriores y scripts `02_`…`06_`, `app_rutas.py`, `ejecutar_todo.py`, `config.py`, `00_preparar_datos.py` anteriores | versión anterior del código | reemplazados; ver 1.3 |

### 1.3 Lo que tenía el `vial/` anterior y no tiene `graphs-appl`

Queda en `_revisar/scripts/vial_anterior/` por si el equipo lo quiere recuperar:
corrección de coordenadas (lat, lon) invertidas, fracción de superficie "afirmado" por
arista (`SUPERFICIE_AFIRMADO`, con el código de superficie aún sin verificar), reporte de
componentes para varias tolerancias de unión (5–100 m) y ranking de criticidad por vía.

### 1.4 Datos

| Archivo | Tamaño | En GitHub |
|---|---|---|
| `data/raw/invias/invias_parte_01..11.geojson` | 10,5–24,9 MB c/u (250 MB en total) | sí |
| `data/raw/invias.geojson` (descarga original) | 250,2 MB | no (`.gitignore`) |
| `data/raw/base1.zip`, `base2.zip` | 14,9 y 14,6 MB | sí |
| `data/raw/base1.csv`, `base2.csv` | 143,7 y 155,0 MB | no (`.gitignore`) |
| `data/raw/divipola.csv` | 0,75 MB | sí |
| `data/final/matriz_od.csv`, `nodos_demanda.csv`, `costo_por_config.csv` | 4,0 MB; 94 KB; 2 KB | sí |
| `data/final/rndc_limpio.rds` | 29,7 MB | no (`.gitignore`; Python no lo lee) |
| `outputs/grafo/red_detallada.pkl` | 1,4 MB | no (`.gitignore`; se regenera) |

Ningún archivo del repositorio pasa de 25 MB. La descarga de INVIAS de octubre de 2026 es
idéntica a las 11 partes: 652 tramos, EPSG:4326, mismas 24 columnas, mismas geometrías,
20.011 km. No hay cambio de esquema.

## 2. Qué se cambió

- **Estructura:** `comun.py` y los pasos de `graphs-appl` se partieron en módulos de
  `scripts/vial/` (carga, limpieza, grafo, costo, ciudades, archivos, rutas, centralidad,
  validacion, cierres, figuras, reporte). Los scripts numerados solo los llaman:
  00 descomprimir, 01 R, 02 red detallada, 03 grafo G, 04 validación y descripción,
  05 cierres, 06 pruebas, 07 intermediación y carga, 08 figuras.
- **`config.py`:** todas las rutas y constantes (antes había números sueltos: 300 pares
  de validación, 14 días, regla de 1 km / mitad del tramo, simplificación de 50 y 200 m,
  código de Bogotá, tolerancia de anclaje de 1 m, DPI, 200 pares y semilla de las
  pruebas). Mismos valores. Las 11 partes de la red están listadas de forma explícita.
- **Errores corregidos:** `06_pruebas.py` no devolvía error cuando una prueba fallaba,
  así que `ejecutar_todo.py` decía "Listo" con pruebas fallidas. Ahora se detiene.
- **Duplicado eliminado:** el nombre corto de los vértices se calculaba en dos sitios.
- **Reportes:** `reporte_construccion.txt` se divide en `reporte_red_detallada.txt`
  (paso 02) y `reporte_grafo_analisis.txt` (paso 03). El paso 02 ahora reporta también
  los km de la capa de INVIAS (20.011 km), que cita el documento.
- **Herramienta:** avisa si origen y destino coinciden, muestra cuántas vías se cerraron,
  tiene botón "Quitar cierres" y no se rompe si el cuadro de días tiene texto.
- **Entorno:** `environment.yml` y `requirements.txt` con versiones fijas.
- **Documentación:** `README.md`, `data/raw/README.md` y este archivo.
- **LaTeX:** `informe/entrega2/` (ver sección 5).

## 3. Regresión y diferencias de cifras

El código migrado da **exactamente los mismos archivos** (byte a byte) que el código de
`graphs-appl` corrido en el mismo entorno: las 6 tablas del grafo, las 5 de resultados y
las 7 figuras. Pruebas: 9/9. Desde `outputs/` vacío, `python scripts/ejecutar_todo.py`
reproduce los 22 archivos idénticos en 2,4 min.

La ruta completa también se comprobó: `00_preparar_datos.py` + `Rscript
scripts/01_limpieza_rndc.R` (R 4.5.2) reescriben `data/final/` con archivos idénticos
byte a byte a los del repositorio.

### 3.1 Frente a las salidas guardadas en `graphs-appl` y a `CLAUDE.md` §2

Las salidas guardadas en `graphs-appl` se produjeron con versiones de librerías que no
quedaron registradas (el `environment.yml` anterior no fijaba versiones). Con el entorno
fijado (Python 3.11.17, shapely 2.2.0 / GEOS 3.14.1, geopandas 1.2.0, pandas 3.0.6):

| Cifra de referencia (`CLAUDE.md` §2) | Antes | Ahora | ¿Cambia la entrega 2? |
|---|---|---|---|
| Tramos INVIAS / km | 652 / 20.011 | igual | No |
| Red detallada D | 841 nodos, 970 aristas | **842 nodos, 972 aristas** (11.866 km) | No (no la cita) |
| Grafo G | 53 vértices, 77 aristas | igual | No |
| Grado medio | 2,9 | 2,91 | No |
| Diámetro | 14 aristas | igual | No |
| κ(G) = λ(G) | 1 | igual | No |
| Puentes | Buenaventura–Dagua, Villavicencio–Puerto Gaitán, Rionegro–Sonsón | igual | No |
| Vértices de corte | 3 | igual (Dagua, Rionegro, Villavicencio) | No |
| Mayor intermediación | Buga–Zarzal, 32 % de los pares | igual | No |
| km grafo / km RNDC (300 pares) | 1,04 (mediana 1,03) | 1,041 (mediana 1,028) | No |
| Distancias G vs D | +4 % (máx. 21 %) | igual | No |
| Pruebas | 6/6 | **9/9** (hay 3 pruebas más) | No |
| Arista Cali–Palmira | 42,47 km | **40,63 km** (recorre también el tramo 371) | No |

Consecuencias en el detalle:

- Solo una arista de G cambia de longitud (Cali–Palmira, −1,84 km). Como los `id_arista`
  se numeran por longitud, `e70` y `e71` intercambian nombre.
- Las listas de `miembros` de cada área metropolitana tienen los mismos municipios en
  otro orden. `tramos.csv` gana el tramo 371 (251 en vez de 250).

### 3.2 Cierres, intermediación y carga

| Cifra | Antes | Ahora |
|---|---|---|
| Intermediación y carga x_e (77 aristas) | — | idénticas en todas |
| Spearman C_B vs x_e | 0,76 | 0,76 |
| Puentes: carga sin ruta | 9,45 / 0,98 / 0,97 Mt | igual |
| Grupos (crítico, importante, vulnerable, secundario, sin carga) | 18, 14, 17, 18, 10 | igual (ninguna arista cambia de grupo) |
| Mayor sobrecosto: Buga–Zarzal | 906,8 mil M COP/año | **908,6** mil M (14 días: 34,8 en ambos) |
| 2.º y 3.º: El Guamo–El Carmen, Bosconia–Aguachica | 687,3 y 473,0 | igual |
| Aristas cuyo sobrecosto cambia | — | 11, todas en el Valle (por Cali–Palmira), máx. ±3,0 mil M |
| Tramos de INVIAS simulados | 242 (100 cierres distintos) | **243** (100 cierres distintos) |

Ninguna cifra de cierres aparece en la entrega 2. Para el documento final hay que usar
las nuevas (en especial 908,6 en vez de ~907 mil millones para Buga–Zarzal).

### 3.3 Tiempos

Paso 02 ≈ 40 s, 03 ≈ 2 min, 04–08 ≈ 45 s; `ejecutar_todo.py` ≈ 2,4 min. La simulación de
cierres tarda 3 s, así que no se optimizó nada: no había un costo medible que reducir.

### 3.4 Entorno de conda sin activar (Windows)

Si se llama a `python.exe` del entorno sin `conda activate`, Windows no encuentra las DLL
de MKL y numpy se cierra sin mensaje (código `0xC06D007F`) en la primera multiplicación
de matrices (la correlación de Spearman del paso 07). Pasa igual con el código original.
Con el entorno activado funciona; el README lo advierte.

## 4. Lo que hay que actualizar fuera del código

| Dónde | Cambio |
|---|---|
| `CLAUDE.md` §2 (está solo en `graphs-appl`) | 841 nodos, 970 aristas → 842, 972; "tests 6/6" → 9/9 |
| `RECUENTO.md` (está solo en `graphs-appl`) | 841/970 → 842/972; 242 → 243 tramos simulados; Buga–Zarzal 907 → 909 mil millones; pruebas en `07_pruebas.py` → `06_pruebas.py`; nombres de los scripts |
| Entrega 2 | ver 5.2 (85,7 millones de t) |

## 5. LaTeX

### 5.1 Arreglos mecánicos aplicados (`informe/entrega2/`)

- La figura apuntaba a `mapa_ciudades.png`, que no existe. Ahora usa
  `\graphicspath{{../../outputs/figuras/}}` y `grafo_analisis_mapa.png` (la que produce
  `08_figuras.py`, con los puentes en naranja, como dice el pie de figura).
- "Isaac Suarez" → "Isaac Suárez" (el correo queda sin tilde).
- Apellido: "Catral" en el documento y en el README (antes el README decía "Catal").
- `dane_divipola`: se agrega `year = {2023}` (antes no tenía año y BibTeX avisaba).
- Comprobado: las 10 citas tienen entrada en `references.bib` y todas las entradas se
  citan; todas las `\ref` tienen su `\label`.

La entrega 1 no está disponible; no se incluyó `informe/entrega1/`.

**No se pudo compilar aquí:** la instalación de TinyTeX de este computador no tiene
`IEEEtran.cls` ni los paquetes `cite`, `algorithm`, `algpseudocode`, etc. No se instaló
nada. Para compilar: `tlmgr install ieeetran cite algorithms algorithmicx float xurl
booktabs` o subir `informe/entrega2/` y `outputs/figuras/grafo_analisis_mapa.png` a
Overleaf (allí la figura debe quedar en la ruta `../../outputs/figuras/` o hay que
ajustar `\graphicspath`).

### 5.2 Propuesta de cambio de contenido (no aplicada): toneladas de 2015

El documento (Sección II) dice "*cerca de 6 millones de viajes y 85,7 millones de
toneladas despachadas entre municipios*". La salida de `01_limpieza_rndc.R` da:

| Cifra | Toneladas | Qué incluye |
|---|---|---|
| Solo kilos | 85.669.244 | carga reportada en kilogramos; deja por fuera los líquidos reportados en galones |
| Kilos + galones | 93.196.338 | además, los líquidos convertidos a 3,2 kg/galón |
| Matriz O-D (`matriz_od.csv`) | **92.990.667** | lo anterior sin autolazos (175.178 t, mismo municipio) y sin códigos fuera de DIVIPOLA |

El 85,7 es la carga solo en kilos: omite 7,5 millones de t de líquidos. Además, "entre
municipios" describe la matriz O-D, que es la que usa el modelo (y sobre la que se
calcula el 47 % de la Sección V). Viajes: 5.999.433 en total, 5.985.633 en la matriz.

Edición propuesta:

> Solo en el año 2015, el RNDC registra cerca de $6$ millones de viajes y $93{,}0$
> millones de toneladas despachadas entre municipios \cite{rndc}.

Alternativa, si se prefiere mantener 85,7: "*85,7 millones de toneladas de carga
reportada en kilogramos (93,2 millones al incluir los líquidos)*".

### 5.3 Otros puntos de contenido para revisar (no aplicados)

1. **Intermediación y carga con empates (Sección IV-D).** El texto dice que $x_e$ es
   *exactamente* la intermediación ponderada por la demanda y que, con varias rutas igual
   de baratas, $C_B$ cuenta cada una en proporción. Pero la asignación todo o nada manda
   toda la carga por una sola de esas rutas. La igualdad es exacta solo si no hay
   empates. Propuesta: "…la suma resultante coincide con la carga $x_e$ de
   \eqref{eq:flujo} cuando cada pareja tiene una sola ruta más barata".
2. **"La diferencia promedio es del 4 %" (Sección V-C).** El 4 % es la razón km grafo /
   km RNDC ponderada por toneladas (1,041); la mediana es 1,028 y el rango p10–p90 va de
   0,89 a 1,36. Propuesta: "…los km del grafo son, en promedio ponderado por toneladas,
   un 4 % mayores que los reportados".
3. **Idioma.** El documento no carga `babel`; la partición de palabras y algunos textos
   automáticos quedan en inglés. Opcional: `\usepackage[spanish]{babel}` (revisar que no
   choque con IEEEtran ni con los `\renewcommand` de `\refname` y `\tablename`).

## 6. Decisiones pendientes para el equipo

1. **`_revisar/`:** decidir qué hacer con `data.py`, `invias.py` y las funciones del
   `vial/` anterior (1.3). La carpeta no se sube a GitHub.
2. **Datos marcados PENDIENTE** en `data/raw/README.md`: nombre y versión del recurso de
   HDX, forma exacta de la exportación del RNDC, nombre del archivo de DIVIPOLA.
3. **Google Colab:** las instrucciones del README no se han probado. Con pip, shapely
   trae su propio GEOS y podría no dar 842/972.
4. **Toneladas de 2015** en la entrega 2 (5.2) y los puntos de 5.3.
5. **`CLAUDE.md` y `RECUENTO.md`:** solo existen en `graphs-appl`. Decidir si se suben al
   repositorio (actualizados según la sección 4).
6. **Nombre del proyecto de RStudio:** `graphs-appl-ports.Rproj`. Funciona (`here()` lo usa
   para ubicar la raíz), pero el nombre no corresponde al repositorio.
7. **Formato de números en la herramienta:** usa separador de miles en inglés
   (2,292,920). Para la presentación se puede cambiar a 2.292.920.
