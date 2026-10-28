# Guion de la presentación (máximo 7 minutos)

Diapositivas: `informe/presentacion/presentacion.tex` (12 diapositivas).
Reparto sugerido: **Gabriel** abre y presenta los resultados de cierres, **David** el
modelo, **Isaac** la implementación, la demostración y el cierre. Cámbienlo como prefieran;
los tiempos son acumulados y dejan 15 segundos de margen.

Antes de empezar: tener abierta la herramienta (`conda activate vial`, luego
`cd scripts` y `python app_rutas.py`) en otra ventana, con Buenaventura como origen y
Bogotá como destino ya elegidos.

---

### 1. Título — Gabriel (0:00–0:15)

> Buenas tardes. Somos David Catral, Isaac Suárez y Gabriel Salcedo, y vamos a mostrar
> cómo usamos teoría de grafos para medir qué tan vulnerable es la red vial primaria de
> carga de Colombia.

### 2. El problema — Gabriel (0:15–0:50)

> Casi toda la carga del país viaja por carretera, y lo hace por unos pocos corredores.
> Esos corredores se cierran a menudo por derrumbes, bloqueos u obras. Cuando eso pasa,
> la carga se desvía por una ruta más larga y más cara, o se queda sin ruta. Nuestra
> pregunta es: ¿qué tramos causan el mayor daño económico cuando se cierran? Lo medimos
> de dos formas: el sobrecosto en pesos de la carga que se desvía y las toneladas que se
> quedan sin ninguna ruta.

### 3. Hipótesis — Gabriel (0:50–1:20)

> Miramos cada tramo desde tres ángulos. Su posición: cuántas parejas de ciudades pasan
> por él. Su uso: cuántas toneladas pasan de verdad. Y la consecuencia de perderlo: cuánto
> cuesta cerrarlo. Nuestra hipótesis es que estos tres ángulos no coinciden; si
> coincidieran, bastaría con mirar el mapa. Y en esas diferencias están los tramos que se
> subestiman.

### 4. Datos y modelo — David (1:20–2:05)

> Usamos tres fuentes públicas: la red vial de INVIAS, con 652 tramos; el Registro
> Nacional de Despachos de Carga de 2015, que nos da cuántas toneladas van de cada
> municipio a cada otro; y la DIVIPOLA, para ubicar los municipios. El peso de cada arista
> no es su longitud, sino el costo de mover una tonelada por ella: 248,6 pesos por
> tonelada-kilómetro, el flete promedio del RNDC. El mapa de INVIAS no es un grafo: tuvimos
> que limpiarlo, porque estaba partido en 464 pedazos. De ahí sale una red detallada de 842
> nodos, que resumimos en el grafo de análisis: 25 ciudades, 28 cruces y 77 aristas.

### 5. El grafo de análisis — David (2:05–2:40)

> Este es el grafo sobre el mapa. Lo primero que nos dice es que la red es frágil: su
> conectividad de vértices y de aristas es 1, o sea que una sola falla la parte. Tiene tres
> puentes, en naranja; el más importante es Buenaventura–Dagua, la única salida del
> principal puerto del Pacífico. Y para saber si el grafo representa bien la realidad,
> comparamos sus distancias con los kilómetros que reporta el RNDC: la diferencia es de
> 4 %.

### 6. Implementación — Isaac (2:40–3:25)

> Para las rutas más baratas programamos nuestro propio Dijkstra, y lo comprobamos contra
> NetworkX en 200 parejas. Con esas rutas repartimos la carga: toda la carga de cada pareja
> va por su ruta más barata, y eso es una intermediación ponderada por toneladas. Usamos
> Brandes para la intermediación y Tarjan para los puentes. Y para medir el daño, el
> algoritmo de cierres quita una arista, recalcula todas las rutas y suma el sobrecosto y
> la carga que se queda sin ruta. Como el grafo es pequeño, cerramos las 77 aristas y 243
> tramos de INVIAS en tres segundos. Todo se verificó con 9 pruebas calculadas a mano.

### 7. Resultado 1 — Isaac (3:25–4:00)

> Primer resultado: la posición no es el uso. Están correlacionadas, 0,76, pero no ordenan
> igual. Buenaventura–Dagua es apenas la número 28 por posición, porque solo conecta una
> ciudad, pero es la tercera por carga: por ella pasa el 21,6 % de toda la carga entre las
> 25 ciudades. Al revés, Barrancabermeja–Puerto Berrío es la sexta por posición y la 42 por
> carga.

### 8. Resultado 2 — Gabriel (4:00–4:40)

> Segundo resultado: lo que cuesta cerrar. Si se cierra Buenaventura–Dagua, 9,45 millones
> de toneladas al año se quedan sin ruta. Entre las vías que sí tienen desvío, la más
> costosa es Buga–Zarzal: 908,6 mil millones de pesos al año, o 34,8 mil millones si el
> cierre dura dos semanas. La carga de Buenaventura a Bogotá pasa de 470 a 821 kilómetros,
> porque tiene que bajar por Cali y Neiva.

### 9. Resultado 3 — Gabriel (4:40–5:15)

> Y el tercer resultado responde la hipótesis. De las diez primeras aristas en cada medida,
> solo dos están en las tres listas. Puerto Triunfo–Honda es la segunda por posición, pero
> la 20 por sobrecosto, porque tiene un buen desvío. Bosconia–Aguachica es la 27 por
> posición y la tercera por sobrecosto. Con carga y calidad del desvío clasificamos las
> aristas: 18 son críticas, es decir, mueven mucha carga y no tienen una buena alternativa.

### 10. Demostración — Isaac (5:15–6:15)

Cambiar a la ventana de la herramienta.

> Esta es la herramienta. Elegimos Buenaventura y Bogotá, y cerramos Buga–Zarzal.
> *(Seleccionar la vía en la lista y pulsar Calcular.)* En naranja aparece la ruta alterna:
> 350 kilómetros más y 87 mil pesos más por tonelada; para esta sola pareja son casi 200
> mil millones de pesos al año. Ahora cerramos Buenaventura–Dagua.
> *(Pulsar "Quitar cierres", seleccionar Buenaventura–Dagua y Calcular.)* La herramienta
> nos dice que no hay ruta: 2,3 millones de toneladas al año se quedan sin salida.

Si la herramienta falla, quedarse en la diapositiva 10, que tiene los dos casos.

### 11. Conclusiones — Isaac (6:15–6:50)

> Para cerrar. Los cierres más costosos con desvío son Buga–Zarzal, El Guamo–El Carmen y
> Bosconia–Aguachica; sin ruta, Buenaventura–Dagua. La hipótesis se cumple: posición, uso y
> consecuencia se parecen, pero no coinciden, así que el mapa solo no basta. Lo que hace
> crítico a un tramo es tener mucha carga y una mala alternativa, y eso nos da una lista
> concreta de 18 aristas para priorizar. Nuestro sobrecosto es un mínimo, porque no
> modelamos congestión ni la red secundaria.

### 12. Gracias — Isaac (6:50–7:00)

> Gracias. El código, los datos y la herramienta están en el repositorio. ¿Preguntas?

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
- **¿Por qué el acceso a Medellín deja carga sin ruta si no es un puente?** Porque el tramo
  de INVIAS recorre a la vez las tres aristas que llegan a la ciudad; INVIAS no tiene
  calles urbanas, así que en el modelo no hay otra salida.
