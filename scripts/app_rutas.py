"""
Ventana para consultar la RUTA DE MENOR COSTO (Dijkstra) entre dos municipios.

Ejecutar en Spyder con F5. Se abre una ventana aparte; el script termina al cerrarla.
- Escriba parte del nombre en "Origen" o "Destino": la lista se filtra mientras escribe
  (no distingue tildes ni mayúsculas). Elija una opción de la lista desplegable.
- "Calcular ruta" ejecuta Dijkstra (vial/rutas.py) con el costo de vial/costo.py.
- El mapa resalta la ruta; con la barra inferior se puede acercar y desplazar.

Usa el grafo de análisis del paso 2 (02_construir_grafo.py). OPCIONAL: es la herramienta
interactiva del proyecto; no produce ningún resultado del repositorio.
"""

import tkinter as tk
import unicodedata
from tkinter import messagebox, ttk

import networkx as nx
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure

from vial.archivos import cargar_grafo
from vial import grafo as modulo_grafo
from vial import rutas

GRIS_RED = "#c9c8c2"
NARANJA = "#eb6834"
AZUL = "#2a78d6"
TINTA = "#2b2b29"
TINTA_SUAVE = "#6b6a65"


def normalizar(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn").lower()


class SelectorFiltrable(ttk.Combobox):
    """Combobox que filtra sus opciones con lo que el usuario escribe."""

    def __init__(self, padre, opciones, **kw):
        super().__init__(padre, values=opciones, **kw)
        self._todas = opciones
        self.bind("<KeyRelease>", self._filtrar)

    def _filtrar(self, evento):
        if evento.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        texto = normalizar(self.get())
        self["values"] = [o for o in self._todas if texto in normalizar(o)] or self._todas


class AppRutas(tk.Tk):
    def __init__(self, G):
        super().__init__()
        self.G = G
        self.title("Ruta de menor costo — red vial de carga")
        self.geometry("1280x800")
        self.minsize(980, 640)

        # componente conexa de cada nodo (para explicar cuando no hay ruta)
        self.componente = {}
        for i, comp in enumerate(sorted(nx.connected_components(G), key=len, reverse=True)):
            for n in comp:
                self.componente[n] = i

        tabla = modulo_grafo.municipios_en_grafo(G)
        self.etiqueta_a_nodo = {
            f"{f.nombre} — {f.departamento} ({f.cod_mpio})": f.nodo for f in tabla.itertuples()}
        self.opciones = list(self.etiqueta_a_nodo)

        self._construir_panel()
        self._construir_mapa()
        self._dibujar_red()

    # ------------------------------------------------------------------ interfaz
    def _construir_panel(self):
        panel = ttk.Frame(self, padding=12)
        panel.pack(side="left", fill="y")

        ttk.Label(panel, text="Ruta de menor costo", font=("TkDefaultFont", 13, "bold")).pack(anchor="w")
        ttk.Label(panel, text=f"{len(self.opciones)} municipios conectados a la red",
                  foreground=TINTA_SUAVE).pack(anchor="w", pady=(0, 10))

        ttk.Label(panel, text="Origen").pack(anchor="w")
        self.origen = SelectorFiltrable(panel, self.opciones, width=46)
        self.origen.pack(anchor="w", pady=(0, 8))
        ttk.Label(panel, text="Destino").pack(anchor="w")
        self.destino = SelectorFiltrable(panel, self.opciones, width=46)
        self.destino.pack(anchor="w", pady=(0, 8))

        botones = ttk.Frame(panel)
        botones.pack(anchor="w", pady=(2, 12))
        ttk.Button(botones, text="Calcular ruta", command=self.calcular).pack(side="left")
        ttk.Button(botones, text="⇄ Intercambiar", command=self.intercambiar).pack(side="left", padx=6)
        ttk.Button(botones, text="Ver toda la red", command=self.ver_todo).pack(side="left")
        self.bind("<Return>", lambda e: self.calcular())

        self.resumen = ttk.Label(panel, text="Elija origen y destino.", justify="left",
                                 wraplength=380, font=("TkDefaultFont", 10))
        self.resumen.pack(anchor="w", pady=(0, 8))

        columnas = ("n", "via", "tramo", "km", "costo")
        marco_tabla = ttk.Frame(panel)
        marco_tabla.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings", height=18)
        anchos = {"n": 32, "via": 70, "tramo": 190, "km": 60, "costo": 60}
        titulos = {"n": "#", "via": "Vía", "tramo": "Tramo", "km": "km", "costo": "Costo"}
        for c in columnas:
            self.tabla.heading(c, text=titulos[c])
            self.tabla.column(c, width=anchos[c], anchor="e" if c in ("n", "km", "costo") else "w")
        barra = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def _construir_mapa(self):
        marco = ttk.Frame(self)
        marco.pack(side="right", fill="both", expand=True)
        self.fig = Figure(figsize=(7, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=marco)
        NavigationToolbar2Tk(self.canvas, marco).pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------ mapa
    def _xy(self, nodo):
        d = self.G.nodes[nodo]
        return d["x"] / 1000, d["y"] / 1000

    def _dibujar_red(self):
        ax = self.ax
        ax.clear()
        segs = [np.array(d["geometry"].coords) / 1000 for *_, d in self.G.edges(data=True)]
        ax.add_collection(LineCollection(segs, colors=GRIS_RED, linewidths=0.7, zorder=1))
        mun = [self._xy(n) for n in self.etiqueta_a_nodo.values()]
        ax.scatter(*zip(*mun), s=5, color=TINTA_SUAVE, zorder=2)
        ax.set_aspect("equal")
        ax.axis("off")
        self.capa_ruta = []
        self.ver_todo()

    def ver_todo(self):
        principal = max(nx.connected_components(self.G), key=len)
        xs, ys = zip(*(self._xy(n) for n in principal))
        mx, my = 0.04 * (max(xs) - min(xs)), 0.04 * (max(ys) - min(ys))
        self.ax.set_xlim(min(xs) - mx, max(xs) + mx)
        self.ax.set_ylim(min(ys) - my, max(ys) + my)
        self.canvas.draw_idle()

    def _dibujar_ruta(self, r):
        for artista in self.capa_ruta:
            artista.remove()
        nodos = r["nodos"]
        segs = []
        for a, b in zip(nodos[:-1], nodos[1:]):
            segs.append(np.array(self.G.edges[a, b]["geometry"].coords) / 1000)
        lc = LineCollection(segs, colors=NARANJA, linewidths=3, zorder=3)
        self.ax.add_collection(lc)
        (xo, yo), (xd, yd) = self._xy(nodos[0]), self._xy(nodos[-1])
        p1 = self.ax.scatter([xo], [yo], s=90, color=AZUL, edgecolor="white", linewidth=1.5, zorder=4)
        p2 = self.ax.scatter([xd], [yd], s=90, color=TINTA, edgecolor="white", linewidth=1.5,
                             marker="s", zorder=4)
        t1 = self.ax.annotate(" " + self.G.nodes[nodos[0]]["nombre"], (xo, yo), fontsize=9,
                              color=TINTA, zorder=5, fontweight="bold")
        t2 = self.ax.annotate(" " + self.G.nodes[nodos[-1]]["nombre"], (xd, yd), fontsize=9,
                              color=TINTA, zorder=5, fontweight="bold")
        self.capa_ruta = [lc, p1, p2, t1, t2]

        todos = np.vstack(segs)
        x0, y0 = todos.min(axis=0)
        x1, y1 = todos.max(axis=0)
        margen = max(x1 - x0, y1 - y0) * 0.15 + 20
        self.ax.set_xlim(x0 - margen, x1 + margen)
        self.ax.set_ylim(y0 - margen, y1 + margen)
        self.canvas.draw_idle()

    # ------------------------------------------------------------------ acciones
    def _nodo(self, combo, rotulo):
        texto = combo.get()
        if texto not in self.etiqueta_a_nodo:
            messagebox.showwarning("Falta elegir",
                                   f"Elija el {rotulo} de la lista desplegable "
                                   f"(escriba parte del nombre y despliegue la lista).")
            return None
        return self.etiqueta_a_nodo[texto]

    def intercambiar(self):
        a, b = self.origen.get(), self.destino.get()
        self.origen.set(b)
        self.destino.set(a)

    def calcular(self):
        o = self._nodo(self.origen, "origen")
        d = self._nodo(self.destino, "destino") if o else None
        if not (o and d):
            return
        if o == d:
            messagebox.showinfo("Mismo municipio", "El origen y el destino son el mismo municipio.")
            return
        r = rutas.ruta_minima(self.G, o, d)
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        if r is None:
            self.resumen.config(text="No hay ruta entre estos municipios.")
            messagebox.showinfo(
                "Sin ruta",
                "No existe ninguna ruta en la red entre estos dos municipios: quedaron en "
                f"componentes conexas distintas (componentes {self.componente[o]} y "
                f"{self.componente[d]}).\n\nCon datos simulados suele deberse a la tolerancia "
                "de unión de extremos (TOLERANCIA_UNION_M en config.py): huecos mayores que "
                "esa tolerancia cortan la vía. Revise la tabla de sensibilidad en "
                "reporte_construccion.txt.")
            return
        via = [t for t in r["tramos"] if t["tipo"] == "via"]
        con = [t for t in r["tramos"] if t["tipo"] == "conector"]
        self.resumen.config(text=(
            f"Costo mínimo: {r['costo']:,.1f} {r['unidad']}\n"
            f"Distancia: {r['km']:,.1f} km  ({sum(t['km'] for t in con):.1f} km en conectores "
            f"municipio–vía)\n"
            f"Aristas recorridas: {len(r['tramos'])}  ·  nodos: {len(r['nodos'])}\n"
            f"Concesiones atravesadas: "
            f"{', '.join(sorted({c for t in via for c in t['concesion'].split(', ') if c != '-'})) or 'ninguna'}"))
        # aristas consecutivas de la misma vía se muestran en una sola fila
        filas = []
        for t in r["tramos"]:
            if filas and filas[-1]["via"] == t["via"] and filas[-1]["nombre"] == t["nombre"]:
                filas[-1]["km"] += t["km"]
                filas[-1]["costo"] += t["costo"]
            else:
                filas.append(dict(t))
        for i, t in enumerate(filas, start=1):
            self.tabla.insert("", "end", values=(i, t["via"], t["nombre"],
                                                 f"{t['km']:.1f}", f"{t['costo']:.1f}"))
        self._dibujar_ruta(r)


def main():
    G = cargar_grafo()
    app = AppRutas(G)
    app.mainloop()


if __name__ == "__main__":
    main()
