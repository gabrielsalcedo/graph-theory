"""
Divide data/raw/invias.geojson (250 MB) en partes de menos de 25 MB para poder subirlas
a GitHub (que no acepta archivos de más de 100 MB). Solo hay que correrlo si se vuelve a
descargar la red vial. El paso 02 vuelve a unir las partes al leerlas.

Uso, desde la carpeta raíz:   python scripts/dividir_invias.py
Salida: data/raw/invias/invias_parte_01.geojson, invias_parte_02.geojson, ...
Si salen más o menos de 11 partes, actualice N_PARTES_RED en config.py.

Cómo funciona: en el archivo de INVIAS cada tramo (Feature) ocupa una línea. Se copian las
líneas tal cual, en orden, y cada parte lleva el mismo encabezado. Así ningún dato cambia.
"""

import config as c

lineas = c.RED_VIAL_COMPLETA.read_text(encoding="utf-8").splitlines()
inicio = next(i for i, l in enumerate(lineas) if l.startswith('"features"')) + 1
encabezado = lineas[:inicio]                  # type, name, crs y '"features": ['
tramos = [l.rstrip(",") for l in lineas[inicio:] if l.startswith('{ "type": "Feature"')]

c.CARPETA_PARTES_RED.mkdir(exist_ok=True)
for viejo in c.CARPETA_PARTES_RED.glob("invias_parte_*.geojson"):
    viejo.unlink()

partes, actual, tamano = [], [], 0
for t in tramos:
    peso = len(t.encode("utf-8")) + 2
    if actual and tamano + peso > c.TAMANO_MAX_PARTE:   # esta parte ya está llena
        partes.append(actual)
        actual, tamano = [], 0
    actual.append(t)
    tamano += peso
partes.append(actual)

for i, p in enumerate(partes, start=1):
    texto = "\n".join(encabezado) + "\n" + ",\n".join(p) + "\n]\n}\n"
    (c.CARPETA_PARTES_RED / f"invias_parte_{i:02d}.geojson").write_text(texto, encoding="utf-8")
    print(f"invias_parte_{i:02d}.geojson: {len(p)} tramos, {len(texto.encode()) / 1e6:.1f} MB")
print(f"Total: {len(tramos)} tramos en {len(partes)} partes.")
if len(partes) != c.N_PARTES_RED:
    print(f"OJO: config.py espera {c.N_PARTES_RED} partes; cambie N_PARTES_RED a {len(partes)}.")
