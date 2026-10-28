"""
Reporte de construcción: lo que se imprime en pantalla también queda en un .txt.

  anotar()           imprime una línea y la guarda
  guardar_reporte()  escribe las líneas guardadas en un archivo
"""

lineas = []


def anotar(texto):
    """Imprime 'texto' y lo guarda para el reporte."""
    lineas.append(texto)
    print(texto)


def guardar_reporte(ruta):
    """Escribe en 'ruta' todas las líneas anotadas hasta ahora."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas), encoding="utf-8")
