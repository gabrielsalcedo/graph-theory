# Auditoría y migración del repositorio

Rama `revision-general`. Fuente de verdad: la carpeta `graphs-appl` (solo lectura). Este
documento se completa por lotes; aquí se registran las diferencias y las decisiones.

## 1. Regresión de la migración a `scripts/vial/`

El código migrado da **exactamente los mismos archivos** (byte a byte) que el código
original de `graphs-appl` corrido en el mismo entorno: `vertices.csv`, `aristas.csv`,
`od_ciudades.csv`, `tramos.csv`, `tramos_por_arista.csv`, `red_detallada.csv`,
`validacion.txt` y `validacion_pares_rndc.csv`. Pruebas: 9/9.

## 2. Diferencias con las salidas guardadas en `graphs-appl`

Las salidas guardadas en `graphs-appl` se produjeron con versiones de librerías que no
quedaron registradas (el `environment.yml` anterior no fijaba versiones). Con el entorno
fijado ahora (`environment.yml`: Python 3.11.17, shapely 2.2.0 / GEOS 3.14.1,
geopandas 1.2.0, pandas 3.0.6) el código **sin cambios** da:

| Cifra | Guardada en `graphs-appl` | Entorno fijado | ¿Cambia el documento? |
|---|---|---|---|
| Tramos INVIAS / km | 652 / 20.011 | 652 / 20.011 | No |
| Red detallada D | 841 nodos, 970 aristas, 11.862 km | **842 nodos, 972 aristas, 11.866 km** | No (el documento no la cita) |
| Grafo G | 53 vértices (25 + 28), 77 aristas | igual | No |
| Grado medio, diámetro | 2,91; 14 | igual | No |
| κ(G), λ(G) | 1, 1 | igual | No |
| Puentes / vértices de corte | 3 / 3 (los mismos) | igual | No |
| G frente a D | media 1,040, máx. 1,214 | igual | No |
| Validación RNDC (300 pares) | 1,041 ponderada, mediana 1,028 | igual | No |
| Carga O-D entre ciudades | 43.718.236 t, 47,0 %, 571 pares | idéntica | No |
| Arista Cali–Palmira | 42,47 km | **40,63 km** (ahora recorre también el tramo 371) | No |

Consecuencias:

- Solo una arista de G cambia de longitud (Cali–Palmira, −1,84 km; total de G 8.720,3 →
  8.718,4 km). Como los `id_arista` se numeran por longitud, `e70` y `e71` intercambian
  nombre (Buga–Palmira ↔ Cali–Palmira).
- Las listas de `miembros` de cada área metropolitana tienen los mismos municipios en
  otro orden.
- `tramos.csv` gana el tramo 371 (251 en vez de 250).
- La simulación de cierres puede variar levemente en lo que pasa por Cali–Palmira (se
  revisa en el lote 4).

### 2.1 Cierres, intermediación y carga (lote 4)

El código migrado de los pasos 05, 07 y 08 da archivos idénticos byte a byte al original
(`cierres_aristas.csv`, `cierres_tramos.csv`, `intermediacion_y_carga.csv` y las 7
figuras). Frente a lo guardado en `graphs-appl`:

| Cifra | Guardada | Entorno fijado |
|---|---|---|
| Intermediación y carga x_e (77 aristas) | — | idénticas en todas |
| Spearman C_B vs x_e | 0,76 | 0,76 |
| Puentes: carga sin ruta | 9,45 / 0,98 / 0,97 Mt | igual |
| Grupos (crítico, importante, vulnerable, secundario, sin carga) | 18, 14, 17, 18, 10 | igual (ninguna arista cambia de grupo) |
| Mayor sobrecosto: Buga–Zarzal | 906,8 mil M COP/año | **908,6** mil M (14 días: 34,8 en ambos) |
| 2.º y 3.º: El Guamo–El Carmen, Bosconia–Aguachica | 687,3 y 473,0 | igual |
| Aristas cuyo sobrecosto cambia | — | 11, todas en el Valle (por Cali–Palmira), máx. ±3,0 mil M |
| Tramos de INVIAS simulados | 242 (100 cierres distintos) | **243** (100 cierres distintos; entra el tramo 371) |

Tiempos (entorno fijado, Windows): paso 02 ≈ 37 s, 03 ≈ 126 s, 04–08 ≈ 45 s; todo
`ejecutar_todo.py` ≈ 2,5 min. La simulación de cierres tarda 3 s, así que no se optimizó.

### 2.2 Entorno de conda sin activar

Si se llama a `python.exe` del entorno sin `conda activate`, Windows no encuentra las
DLL de MKL y numpy se cierra sin mensaje (código `0xC06D007F`) en la primera
multiplicación de matrices (la correlación de Spearman del paso 07). Con el entorno
activado funciona. El README lo advierte.

**Decisión del equipo:** se aceptan los resultados del entorno fijado y se regeneran las
salidas. Hay que actualizar 841/970 por 842/972 en `CLAUDE.md` (§2) y `RECUENTO.md`; el
documento de la entrega 2 no cita esas cifras.
