"""
EJECUTA TODO EL ANÁLISIS EN ORDEN y reproduce todos los resultados y figuras.

Uso (desde la carpeta scripts/, con el entorno "vial" activo):
    python ejecutar_todo.py

Corre los pasos 2 a 6 (~1-2 min). Los pasos 0 y 1 (descomprimir datos y limpiar el RNDC
en R) no hacen falta porque data/final/ ya viene en el repositorio; ver README.md.

  02_construir_grafo.py           -> outputs/resultados/grafo.pkl, grafo_detallado.pkl, ...
  03_criticidad_intermediacion.py -> outputs/resultados/criticas_*.csv, mapa y barras
  04_validar_grafo.py             -> outputs/resultados/validacion.txt
  05_dibujar_grafos.py            -> outputs/figuras/*.png
  06_pruebas.py                   -> 6 pruebas automáticas (deben salir 6/6)
"""

import os
import subprocess
import sys
import time
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
PASOS = [
    "02_construir_grafo.py",
    "03_criticidad_intermediacion.py",
    "04_validar_grafo.py",
    "05_dibujar_grafos.py",
    "06_pruebas.py",
]


def main():
    inicio = time.time()
    entorno = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    for script in PASOS:
        print(f"\n{'=' * 70}\n{script}\n{'=' * 70}", flush=True)
        r = subprocess.run([sys.executable, script], cwd=CARPETA, env=entorno)
        if r.returncode != 0:
            sys.exit(f"\nFALLÓ {script}. Revise el mensaje de error de arriba.")
    print(f"\nListo en {(time.time() - inicio) / 60:.1f} min. "
          f"Resultados en outputs/resultados/ y figuras en outputs/figuras/.")


if __name__ == "__main__":
    main()
