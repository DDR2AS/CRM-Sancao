import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from datetime import datetime

import pandas as pd

class GastosFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master)
        self.process = process
        
        try:
            self.datos = self.process.getGastos()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.datos = pd.DataFrame()

        # Selector de mes
        self.meses = self.obtener_meses_disponibles()
        self.mes_seleccionado = ctk.StringVar(value="Todos")

        filtro_frame = ctk.CTkFrame(self)
        filtro_frame.pack(pady=(15, 0))

        ctk.CTkLabel(filtro_frame, text="Filtrar por mes:").pack(side="left", padx=(0, 10))

        self.selector_mes = ctk.CTkOptionMenu(
            filtro_frame,
            values=["Todos"] + self.meses,
            variable=self.mes_seleccionado,
            command=self.filtrar_por_mes
        )
        self.selector_mes.pack(side="left")

        # Total
        self.total_label = ctk.CTkLabel(self, text="Gasto Total: S/ 0.00", font=("Arial", 24, "bold"))
        self.total_label.pack(pady=10)

        # Tabla
        self.columns = ("Fecha", "Tipo", "Producto", "Cantidad", "Monto Total", "Descripción")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=10)

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=130)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.cargar_datos(self.datos)

    def obtener_meses_disponibles(self):
        meses = set()
        for _, row in self.datos.iterrows():
            try:
                fecha = datetime.strptime(row["Fecha"], "%Y-%m-%d")
                meses.add(fecha.strftime("%Y-%m"))
            except Exception as e:
                print(f"Fecha inválida: {row['Fecha']} → {e}")
        return sorted(list(meses), reverse=True)

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = 0.0
        for _, row in datos.iterrows():
            try:
                cantidad = row.get("Cantidad", 0)
                monto = float(row.get("Monto Total", 0))
                self.tree.insert("", tk.END, values=(
                    row.get("Fecha", ""),
                    row.get("Tipo", ""),
                    row.get("Producto", ""),
                    cantidad,
                    monto,
                    row.get("Descripcion", "")
                ))
                total += monto
            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.total_label.configure(text=f"Gasto Total: S/ {total:,.2f}")

    def filtrar_por_mes(self, mes):
        if mes == "Todos":
            filtrado = self.datos
        else:
            filtrado = self.datos[
                self.datos["Fecha"].str.startswith(mes)
            ]
        self.cargar_datos(filtrado)

