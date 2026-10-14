import geopandas as gpd
from pyprojroot.here import here
import pandas as pd
import matplotlib.pyplot as plt  # Necesario para mostrar el mapa al final

# Corrección de la ruta para que apunte al mismo lugar que en tu código de R
ruta_datos = here("data/raw/invias.geojson") 

# CORRECCIÓN: Pasamos la variable sin comillas
red = gpd.read_file(ruta_datos)   # o .geojson si cambias el formato

print(red.shape)          # ¿cuántos tramos?
print(red.columns)        # ¿qué atributos trae?
print(red.crs)            # ¿en qué sistema de coordenadas está?
print(red.head())

# Para visualizar el mapa en Python necesitas activar el backend de gráficos
red.plot()                
plt.show()                # Muestra la ventana con el mapa de la red de Colombia
