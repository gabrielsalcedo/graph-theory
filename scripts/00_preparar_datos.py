"""
PASO 0 — Prepara los datos crudos después de clonar el repositorio.

GitHub no acepta archivos de más de 100 MB, así que en el repositorio los datos pesados
vienen comprimidos. Este script los descomprime en data/raw/:
  base1.zip   -> base1.csv     (RNDC 2015, parte 1; lo usa 01_limpieza_rndc.R)
  base2.zip   -> base2.csv     (RNDC 2015, parte 2)
  invias.zip  -> invias.geojson (red vial; opcional: Python también lee el .zip directo)

Uso (desde la carpeta raíz del proyecto):  python scripts/00_preparar_datos.py
Solo hace falta para volver a correr la limpieza en R. Para construir el grafo basta con
data/final/ (ya incluido) y data/raw/invias.zip.
"""

import zipfile
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

for nombre in ("base1", "base2", "invias"):
    zip_ = RAW / f"{nombre}.zip"
    if not zip_.exists():
        print(f"FALTA   {zip_.name}  (ver README: Datos)")
        continue
    with zipfile.ZipFile(zip_) as z:
        for miembro in z.namelist():
            destino = RAW / miembro
            if destino.exists():
                print(f"YA ESTÁ {miembro}")
            else:
                print(f"EXTRAE  {miembro} ...")
                z.extract(miembro, RAW)
print("Listo.")
