"""
Peso de las aristas: w = km x tarifa, el costo de mover una tonelada por la vía.

  costo_arista()   costo en COP de 2015 por tonelada
"""

import config as c


def costo_arista(longitud_m):
    """Recibe la longitud de la vía en metros; devuelve el costo (COP) de mover una
    tonelada por ella con la tarifa única TARIFA_COP_TKM."""
    return longitud_m / 1000 * c.TARIFA_COP_TKM
