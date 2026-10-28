"""
HERRAMIENTA — Ruta de menor costo y ruta alterna ante cierres (para la demostración).

El usuario elige un origen, un destino y las vías que quiere cerrar. La ventana muestra:
  - la ruta normal (gris oscuro) y la ruta alterna con las vías cerradas (naranja);
  - los km extra, el sobrecosto por tonelada y, con las toneladas del RNDC de esa
    pareja, el sobrecosto al año y el de un cierre de N días;
  - si no queda ruta, lo dice (la vía cerrada era un puente para esa pareja).

Uso: `python app_rutas.py` desde scripts/. Necesita haber corrido el paso 03.
Necesita una pantalla: en Google Colab no abre (use un computador con Python).
"""

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure

import config as c
from vial.archivos import cargar_grafo, cargar_od
from vial.ciudades import lista_ciudades, nombre_corto
from vial.rutas import ruta

GRIS, OSCURO, NARANJA, ROJO = "#d9d8d3", "#2b2b29", "#eb6834", "#e34948"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Red vial de carga — rutas y cierres")
        self.geometry("1250x780")
        self.G = cargar_grafo()
        od = cargar_od()
        self.toneladas = {(f.o, f.d): f.toneladas for f in od.itertuples()}
        self.nodo = {nombre_corto(self.G, n): n for n in sorted(lista_ciudades(self.G),
                                                                 key=lambda n: nombre_corto(self.G, n))}
        self.arista = {f"{d['id_arista']}  {d['nombre']}": (u, v)
                       for u, v, d in sorted(self.G.edges(data=True), key=lambda e: e[2]["nombre"])}

        panel = ttk.Frame(self, padding=10)
        panel.pack(side="left", fill="y")
        ttk.Label(panel, text="Origen").pack(anchor="w")
        self.origen = ttk.Combobox(panel, values=list(self.nodo), state="readonly", width=40)
        self.origen.pack(anchor="w", pady=(0, 6))
        ttk.Label(panel, text="Destino").pack(anchor="w")
        self.destino = ttk.Combobox(panel, values=list(self.nodo), state="readonly", width=40)
        self.destino.pack(anchor="w", pady=(0, 6))
        ttk.Label(panel, text="Vías cerradas (Ctrl + clic para varias)").pack(anchor="w")
        self.cerradas = tk.Listbox(panel, selectmode="extended", height=18, width=46,
                                   exportselection=False)
        for etiqueta in self.arista:
            self.cerradas.insert("end", etiqueta)
        self.cerradas.pack(anchor="w")
        fila = ttk.Frame(panel)
        fila.pack(anchor="w", pady=6)
        ttk.Label(fila, text="Días de cierre:").pack(side="left")
        self.dias = tk.IntVar(value=c.DIAS_CIERRE)
        ttk.Spinbox(fila, from_=1, to=365, textvariable=self.dias, width=5).pack(side="left", padx=4)
        ttk.Button(fila, text="Calcular", command=self.calcular).pack(side="left", padx=8)
        ttk.Button(fila, text="Quitar cierres", command=self.quitar_cierres).pack(side="left")
        self.texto = ttk.Label(panel, text="Elija origen y destino.", justify="left", wraplength=330)
        self.texto.pack(anchor="w", pady=8)

        self.fig = Figure(figsize=(7, 8))
        self.ax = self.fig.add_subplot(111)
        self.lienzo = FigureCanvasTkAgg(self.fig, master=self)
        self.lienzo.get_tk_widget().pack(side="right", fill="both", expand=True)
        self.dibujar([], None, None)

    def dibujar(self, cerradas, normal, alterna):
        ax = self.ax
        ax.clear()
        trazo = lambda aristas: [np.array(self.G.edges[e]["geometry"].coords) / 1000 for e in aristas]
        ax.add_collection(LineCollection(trazo(self.G.edges()), colors=GRIS, linewidths=1))
        for r, color, ancho in ((normal, OSCURO, 2.5), (alterna, NARANJA, 3)):
            if r:
                ax.add_collection(LineCollection(trazo(zip(r["nodos"][:-1], r["nodos"][1:])),
                                                 colors=color, linewidths=ancho))
        if cerradas:
            ax.add_collection(LineCollection(trazo(cerradas), colors=ROJO, linewidths=3,
                                             linestyles=":"))
        for n in lista_ciudades(self.G):
            x, y = self.G.nodes[n]["x"] / 1000, self.G.nodes[n]["y"] / 1000
            ax.plot(x, y, "o", color=OSCURO, ms=4)
            ax.annotate(nombre_corto(self.G, n), (x, y), xytext=(3, 2),
                        textcoords="offset points", fontsize=7)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.autoscale()
        self.lienzo.draw_idle()

    def quitar_cierres(self):
        self.cerradas.selection_clear(0, "end")
        self.calcular()

    def dias_de_cierre(self):
        """Días del cuadro; si el texto no es un número válido, usa DIAS_CIERRE."""
        try:
            return max(1, min(365, int(self.dias.get())))
        except (tk.TclError, ValueError):
            self.dias.set(c.DIAS_CIERRE)
            return c.DIAS_CIERRE

    def calcular(self):
        if self.origen.get() not in self.nodo or self.destino.get() not in self.nodo:
            self.texto.config(text="Elija origen y destino.")
            return
        if self.origen.get() == self.destino.get():
            self.texto.config(text="El origen y el destino son la misma ciudad.")
            return
        o, d = self.nodo[self.origen.get()], self.nodo[self.destino.get()]
        cerradas = [self.arista[self.cerradas.get(i)] for i in self.cerradas.curselection()]
        dias = self.dias_de_cierre()
        normal = ruta(self.G, o, d)
        H = self.G.copy()
        H.remove_edges_from(cerradas)
        alterna = ruta(H, o, d)
        t = self.toneladas.get((o, d), 0)
        lineas = [f"{self.origen.get()} -> {self.destino.get()}",
                  f"Ruta normal: {normal['km']:,.0f} km, {normal['costo']:,.0f} COP por tonelada.",
                  f"Carga de esta pareja (RNDC 2015): {t:,.0f} t al año.",
                  f"Vías cerradas: {len(cerradas)}."]
        if alterna is None:
            lineas.append(f"\nCON ESTOS CIERRES NO HAY RUTA entre las dos ciudades: "
                          f"{t:,.0f} t al año quedan sin ruta "
                          f"({t * dias / 365:,.0f} t en {dias} días).")
        elif alterna["nodos"] == normal["nodos"]:
            lineas.append("\nLos cierres no afectan esta ruta.")
        else:
            extra = alterna["costo"] - normal["costo"]
            lineas += [f"\nRuta alterna: {alterna['km']:,.0f} km (+{alterna['km'] - normal['km']:,.0f} km).",
                       f"Sobrecosto: {extra:,.0f} COP por tonelada.",
                       f"Sobrecosto de esta pareja: {extra * t / 1e6:,.0f} millones COP al año; "
                       f"{extra * t * dias / 365 / 1e6:,.0f} millones en {dias} días."]
        self.texto.config(text="\n".join(lineas))
        self.dibujar(cerradas, normal, alterna)


if __name__ == "__main__":
    App().mainloop()
