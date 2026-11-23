# Guion de la presentación (máximo 7 minutos)

Diapositivas: `informe/presentacion/presentacion.pdf` (12 diapositivas).

Cada diapositiva trae:

- **En pantalla:** lo que el público está viendo.
- **Qué decir:** el texto para leer o aprender (entre comillas). Las *cursivas* son acciones, no se dicen.
- **Qué señalar:** a dónde apuntar mientras se habla.
- **Transición:** la última frase, que entrega a la siguiente diapositiva o persona.

**Reparto:** Gabriel abre y presenta los costos de cerrar (1–3 y 8–9); David, el modelo
(4–5); Isaac, la implementación, la demo y el cierre (6–7 y 10–12). Cámbienlo como prefieran.
Los tiempos son acumulados y dejan unos 15 segundos de margen.

**Antes de empezar:** abrir la herramienta en otra ventana (`conda activate vial`, `cd scripts`,
`python app_rutas.py`) con Buenaventura como origen y Bogotá como destino ya elegidos.

| # | Diapositiva | Quién | Tiempo |
|---|---|---|---|
| 1 | Título | Gabriel | 0:00–0:15 |
| 2 | El problema | Gabriel | 0:15–0:50 |
| 3 | Hipótesis | Gabriel | 0:50–1:20 |
| 4 | Datos y modelo | David | 1:20–2:05 |
| 5 | El grafo de análisis | David | 2:05–2:40 |
| 6 | Implementación | Isaac | 2:40–3:25 |
| 7 | Resultado 1: posición vs. uso | Isaac | 3:25–4:05 |
| 8 | Resultado 2: el costo de cerrar | Gabriel | 4:05–4:40 |
| 9 | Resultado 3: carga y desvío | Gabriel | 4:40–5:15 |
| 10 | Demostración | Isaac | 5:15–6:15 |
| 11 | Conclusiones | Isaac | 6:15–6:50 |
| 12 | Gracias | Isaac | 6:50–7:00 |

---

## 1. Título — Gabriel (0:00–0:15)

**En pantalla:** título del proyecto, autores y universidad.

**Qué decir:**

> "Buenas tardes. Somos David Catral, Isaac Suárez y Gabriel Salcedo. Vamos a mostrar cómo
> usamos teoría de grafos para medir qué tan vulnerable es la red vial de carga de Colombia."

**Qué señalar:** nada; mirar al público.

**Transición:** pasar a la diapositiva 2 sin pausa.

---

## 2. El problema — Gabriel (0:15–0:50)

**En pantalla:** tres puntos sobre los cierres y el recuadro con la pregunta.

**Qué decir:**

> "Casi toda la carga del país viaja por carretera, y lo hace por unos pocos corredores.
> Esos corredores se cierran a menudo por derrumbes, bloqueos u obras. Cuando eso pasa, la
> carga se desvía por una ruta más larga y más cara, o se queda sin ruta.
>
> Nuestra pregunta es: ¿qué tramos causan el mayor daño económico cuando se cierran? Lo
> medimos en pesos de más y en toneladas que se quedan sin ruta."

**Qué señalar:** el recuadro de la pregunta, al decir "nuestra pregunta es".

**Transición:** "Para responderla, miramos cada tramo desde tres ángulos."

---

## 3. Hipótesis — Gabriel (0:50–1:20)

**En pantalla:** tres columnas, Posición, Uso y Consecuencia, y la frase en naranja abajo.

**Qué decir:**

> "Primero, su posición: cuántas parejas de ciudades pasan por él. Segundo, su uso: cuántas
> toneladas pasan de verdad. Y tercero, la consecuencia de perderlo: cuánto cuesta cerrarlo.
>
> Nuestra hipótesis es que estos tres ángulos no coinciden. Si coincidieran, bastaría con
> mirar el mapa. En esas diferencias están los tramos que se subestiman."

**Qué señalar:** cada columna en orden, de izquierda a derecha; al final, la frase en naranja.

**Transición:** "David les cuenta cómo construimos el modelo."

---

## 4. Datos y modelo — David (1:20–2:05)

**En pantalla:** a la izquierda, las tres fuentes y la fórmula del peso; a la derecha, los pasos del mapa al grafo.

**Qué decir:**

> "Usamos tres fuentes públicas: el mapa de carreteras de INVIAS, con 652 tramos; el Registro
> Nacional de Despachos de Carga de 2015, con las toneladas entre municipios; y la DIVIPOLA
> del DANE, para ubicar los municipios.
>
> El peso de cada arista no es su longitud sino su costo: lo que cuesta mover una tonelada
> por ella, 248,6 pesos por kilómetro, el flete promedio de 2015.
>
> El mapa de INVIAS no era un grafo: estaba partido en 464 pedazos que no se tocaban. Lo
> limpiamos y lo resumimos en el grafo de análisis: 25 ciudades, 28 cruces y 77 aristas."

**Qué señalar:** la fórmula del peso al decir "248,6"; la línea en naranja (25 ciudades + 28 cruces) al final.

**Transición:** "Así se ve ese grafo sobre el mapa."

---

## 5. El grafo de análisis — David (2:05–2:40)

**En pantalla:** el mapa del grafo (azul, con los puentes en naranja) y cuatro datos a la derecha.

**Qué decir:**

> "Lo primero que nos dice es que la red es frágil: su conectividad es 1, o sea que una sola
> falla puede partirla en dos. Tiene tres puentes, que son las líneas naranjas. El más
> importante es Buenaventura–Dagua, la única salida del principal puerto del Pacífico.
>
> Y se parece a la realidad: sus distancias difieren apenas 4 % de las que reportan los
> camiones."

**Qué señalar:** la línea naranja corta en el suroccidente (Buenaventura–Dagua) al nombrarla.

**Transición:** "Isaac explica cómo calculamos todo sobre este grafo."

---

## 6. Implementación — Isaac (2:40–3:25)

**En pantalla:** la lista de algoritmos y, a la derecha, las dos fórmulas del daño, I(e) y D(e).

**Qué decir:**

> "Para encontrar la ruta más barata programamos nuestro propio algoritmo de Dijkstra, y lo
> comprobamos contra una librería profesional. Con esas rutas
> repartimos la carga: toda la carga de cada pareja va por su ruta más barata. Usamos Brandes
> para medir la posición de cada arista y Tarjan para encontrar los puentes.
>
> Para medir el daño, quitamos una arista, recalculamos todas las rutas y sumamos dos cosas:
> I, los pesos de más que paga la carga que se desvía, y D, las toneladas que se quedan sin
> ruta. Cerramos las 77 aristas y 243 tramos de INVIAS en tres segundos, y todo está
> verificado con 9 pruebas calculadas a mano."

**Qué señalar:** la fórmula de I al decir "pesos de más" y la de D al decir "sin ruta".

**Transición:** "Con eso, estos son los resultados."

---

## 7. Resultado 1: la posición no es el uso — Isaac (3:25–4:05)

**En pantalla:** gráfico de puntos. Cada punto es una carretera; el eje horizontal es su posición en el mapa y el vertical, la carga que lleva. Los puntos naranjas son puentes.

**Qué decir:**

> "Cada punto es una de las 77 carreteras. Hacia la derecha, más parejas de ciudades pasan
> por ella; hacia arriba, más carga lleva de verdad. Si posición y uso fueran lo mismo, todos
> los puntos estarían sobre una diagonal. Se parecen —la correlación es 0,76—, pero no
> ordenan igual.
>
> Miren el punto naranja de arriba a la izquierda: es Buenaventura–Dagua. Por posición es
> apenas la número 28, pero es la tercera por carga, con el 21,6 % de toda la carga. El mapa
> la subestima. Al revés,
> Barrancabermeja–Puerto Berrío, abajo a la derecha, es la sexta por posición pero la 42 por
> carga."

**Qué señalar:** primero los ejes (abajo y a la izquierda); luego el punto naranja de arriba a la izquierda; luego el punto de Barrancabermeja, abajo a la derecha.

**Transición:** "Gabriel les muestra cuánto cuesta cerrar."

---

## 8. Resultado 2: el costo de cerrar — Gabriel (4:05–4:40)

**En pantalla:** a la izquierda, los tres puentes con la carga que dejan sin ruta; a la derecha, la tabla de las cinco aristas más costosas.

**Qué decir:**

> "Hay dos tipos de daño. Si se cierra Buenaventura–Dagua, 9,45 millones de toneladas al año
> se quedan sin ninguna ruta.
>
> Entre las vías que sí tienen desvío, la más costosa es Buga–Zarzal: 908.600 millones de
> pesos al año, o 34.800 millones si el cierre dura solo dos semanas. ¿Por qué tanto? Porque
> la carga de Buenaventura a Bogotá pasa de 470 a 821 kilómetros: tiene que bajar por Cali y
> Neiva."

**Qué señalar:** el 9,45 en naranja; luego el 908,6 de la primera fila de la tabla; al final, la línea de abajo (470 → 821 km).

**Transición:** "Y ahora juntamos los tres ángulos."

---

## 9. Resultado 3: carga y desvío — Gabriel (4:40–5:15)

**En pantalla:** gráfico de cuadrantes. Cada punto es una carretera; el eje horizontal es cuánta carga mueve y el vertical, qué tan caro es su desvío por tonelada. Las líneas punteadas son las medianas y dividen cuatro grupos.

**Qué decir:**

> "Este gráfico separa las dos causas del daño: hacia la derecha, más carga; hacia arriba,
> un desvío más caro por tonelada. Las líneas punteadas marcan la carretera típica y dividen
> cuatro grupos.
>
> Arriba a la derecha están las críticas, en naranja: mucha carga y mal desvío. Son 18. Por
> ejemplo, Buga–Zarzal mueve 9,5 millones de toneladas y cada una paga 95.000 pesos más si se
> cierra. Bosconia–Aguachica mueve menos carga, pero tiene el peor desvío de todas las
> críticas. Abajo a la derecha, en azul, están las que mueven mucha carga pero tienen un buen
> desvío: cerrarlas cuesta poco por tonelada. Y arriba del todo, los tres puentes, que no
> tienen desvío."

**Qué señalar:** los ejes; el cuadrante de arriba a la derecha y los puntos de Buga–Zarzal y Bosconia–Aguachica; los puntos azules de abajo a la derecha; la fila de puntos de arriba del todo (los puentes).

**Transición:** "Isaac les muestra la herramienta en vivo."

---

## 10. Demostración — Isaac (5:15–6:15)

**En pantalla:** primero la diapositiva con los dos casos; luego, la ventana de la herramienta.

*(Cambiar a la ventana de la herramienta.)*

**Qué decir:**

> "Esta herramienta permite elegir un origen, un destino y las vías cerradas. Elegimos
> Buenaventura y Bogotá, y cerramos Buga–Zarzal."
>
> *(Seleccionar Buga–Zarzal en la lista y pulsar Calcular.)*
>
> "La ruta normal es la gris; la alterna, en naranja, baja por Cali y Neiva: 350 kilómetros
> más y 87.000 pesos más por tonelada. Para esta sola pareja son casi 200.000 millones de
> pesos al año. Ahora cerramos Buenaventura–Dagua."
>
> *(Pulsar "Quitar cierres", seleccionar Buenaventura–Dagua y pulsar Calcular.)*
>
> "La herramienta nos dice que no hay ruta: 2,3 millones de toneladas al año se quedan sin
> salida."

**Qué señalar:** la línea naranja en el mapa de la herramienta; el texto de resultados a la izquierda.

**Si la herramienta falla:** quedarse en la diapositiva 10 y leer los dos casos que tiene.

**Transición:** *(volver a las diapositivas)* "Para cerrar."

---

## 11. Conclusiones — Isaac (6:15–6:50)

**En pantalla:** cuatro conclusiones y, en gris, las limitaciones.

**Qué decir:**

> "Los cierres más costosos con desvío son Buga–Zarzal, El Guamo–El Carmen y
> Bosconia–Aguachica; sin ruta, Buenaventura–Dagua. La hipótesis se cumple: posición, uso y
> consecuencia se parecen, pero no coinciden; solo dos carreteras están entre las diez
> primeras de las tres medidas. Mirar solo el mapa no basta.
>
> Lo que hace crítico a un tramo es tener mucha carga y un mal desvío, y eso nos da una lista
> concreta de 18 carreteras para priorizar. Nuestras cifras son un mínimo, porque no
> incluimos congestión ni la red secundaria."

**Qué señalar:** cada viñeta en orden; al final, la línea gris de limitaciones.

**Transición:** pasar a la última diapositiva.

---

## 12. Gracias — Isaac (6:50–7:00)

**En pantalla:** "Gracias", "¿Preguntas?" y el enlace al repositorio.

**Qué decir:**

> "Gracias. El código, los datos y la herramienta están en el repositorio. ¿Preguntas?"

**Qué señalar:** nada; mirar al público.

---

## Preguntas probables y respuestas cortas

- **¿Por qué un solo flete para toda la red?** Porque el RNDC no da el costo por vía. Con
  tarifa única la ruta más barata es la más corta; una tarifa por terreno o superficie es
  el siguiente paso.
- **¿Por qué el sobrecosto es un mínimo?** Porque suponemos que la ruta alterna no se
  congestiona y que la carga no cambia ante el cierre.
- **¿Por qué 25 ciudades?** Son las de más carga después de agrupar las áreas
  metropolitanas; con 53 vértices se pueden aplicar todos los conceptos del curso y cerrar
  todas las aristas.
- **¿Cómo saben que el grafo se parece a la realidad?** En las 300 parejas con más carga,
  los km del grafo son 1,04 veces los que reporta el RNDC (mediana 1,03).
- **¿Por qué Spearman y no Pearson?** Porque nos interesa el orden de prioridad de las
  carreteras, no sus valores exactos; Spearman compara los rankings y no se deja dominar por
  unas pocas carreteras con valores muy grandes.
- **¿Por qué Buenaventura–Dagua tiene exactamente 8 % de intermediación?** Buenaventura es un
  extremo de la red: su vía la usan solo las 24 parejas que incluyen a Buenaventura, y
  24/300 = 8 %.
- **¿Por qué el acceso a Medellín deja carga sin ruta si no es un puente?** Porque el tramo
  de INVIAS recorre a la vez las tres aristas que llegan a la ciudad; INVIAS no tiene
  calles urbanas, así que en el modelo no hay otra salida.
