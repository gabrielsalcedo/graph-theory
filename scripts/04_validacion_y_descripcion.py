"""
PASO 04 — Descripción estructural del grafo de análisis y validación contra el RNDC.

1. Propiedades: orden, tamaño, grados, conexidad, planaridad, diámetro, κ(G), λ(G),
   puentes y vértices de corte (Tarjan, vía networkx).
2. Validación: en los 300 pares O-D con más toneladas, se comparan los km de la ruta
   más corta del grafo con los km por viaje que reporta el RNDC.

Salidas: outputs/resultados/validacion.txt y validacion_pares_rndc.csv
"""

import config as c
from vial.archivos import cargar_grafo
from vial.validacion import frente_a_rndc, propiedades


def main():
    c.RESULTADOS.mkdir(parents=True, exist_ok=True)
    G = cargar_grafo()
    texto = "\n".join(propiedades(G) + frente_a_rndc(G))
    (c.RESULTADOS / "validacion.txt").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
