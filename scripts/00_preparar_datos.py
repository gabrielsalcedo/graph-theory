"""
PASO 0 — Prepara los datos crudos del RNDC (solo para la ruta completa).

El RNDC 2015 viene en el repositorio comprimido (base1.zip, base2.zip), porque los .csv
pesan más de 100 MB y GitHub no los acepta. Este script los descomprime en data/raw/
para que 01_limpieza_rndc.R los pueda leer.

Uso (desde la carpeta raíz):  python scripts/00_preparar_datos.py
No hace falta para la ruta rápida: data/final/ ya viene en el repositorio y la red vial
viene partida en data/raw/invias/ (el paso 02 la une sola).
"""

import zipfile

import config as c

for zip_ in c.ZIPS_RNDC:
    if not zip_.exists():
        print(f"FALTA   {zip_.name}  (ver data/raw/README.md)")
        continue
    with zipfile.ZipFile(zip_) as z:
        for miembro in z.namelist():
            if (c.CARPETA_RAW / miembro).exists():
                print(f"YA ESTÁ {miembro}")
            else:
                print(f"EXTRAE  {miembro} ...")
                z.extract(miembro, c.CARPETA_RAW)
print("Listo.")
