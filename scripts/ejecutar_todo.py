"""
Corre todo el análisis en orden (pasos 02 a 08). Desde la carpeta raíz o desde scripts/:
    python scripts/ejecutar_todo.py
Los pasos 00 y 01 (descomprimir y limpiar el RNDC en R) solo hacen falta para la ruta
completa, porque data/final/ ya viene en el repositorio.
Se detiene en el primer paso que falle (incluidas las pruebas).
"""

import os
import subprocess
import sys
import time
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
PASOS = ["02_red_detallada.py", "03_grafo_analisis.py", "04_validacion_y_descripcion.py",
         "05_simulacion_cierres.py", "06_pruebas.py", "07_intermediacion_y_carga.py",
         "08_figuras.py"]

inicio = time.time()
for script in PASOS:
    print(f"\n{'=' * 70}\n{script}\n{'=' * 70}", flush=True)
    r = subprocess.run([sys.executable, script], cwd=CARPETA,
                       env=dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8"))
    if r.returncode != 0:
        sys.exit(f"\nFALLÓ {script}: revise el error de arriba.")
print(f"\nListo en {(time.time() - inicio) / 60:.1f} min. "
      f"Resultados en outputs/resultados/ y figuras en outputs/figuras/.")
