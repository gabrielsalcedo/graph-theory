"""Lectura de los grafos ya construidos (los guarda 02_construir_grafo.py)."""

import pickle

import config


def _leer(ruta):
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Corra primero 02_construir_grafo.py.")
    with open(ruta, "rb") as f:
        return pickle.load(f)


def cargar_grafo():
    """Grafo de análisis: ciudades + cruces clave."""
    return _leer(config.ARCHIVO_GRAFO)


def cargar_detallado():
    """Red detallada: la red INVIAS limpia con las 50 ciudades conectadas."""
    return _leer(config.ARCHIVO_DETALLADO)
