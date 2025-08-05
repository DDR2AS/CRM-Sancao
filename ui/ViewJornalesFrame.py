import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from datetime import datetime

import pandas as pd

class JornalesFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master)

        self.process = process

        try:
            self.datos = self.process.getJornales()
        except Exception as e:
            print("Error al obtener datos desde process.getJornales(): ", e)
            self.datos = pd.DataFrame()

        # Total
        self.total_label = ctk.CTkLabel(self, text="Total Jornal: S/ 0.00", font=("Arial", 24, "bold"))
        self.total_label.pack(pady=10)

        # Tabla
        self.columns = ("Fecha Trabajo", "Actividad", "Monto Total", "Trabajador")
        style = ttk.Style()
        style.configure("Treeview",
                        font=("Segoe UI", 12),
                        rowheight=32,
                        background="#F9F9F9",
                        fieldbackground="#F9F9F9",
                        foreground="#333333",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 14, "bold"),
                        background="#DDEBF7",
                        foreground="#1F4E79",
                        relief="flat")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=10)
        
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=130)
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.cargar_datos(self.datos)

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = 0.0
        for _, row in datos.iterrows():
            fecha = row['Fecha Trabajo']
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_str = fecha.strftime("%Y-%m-%d")
            try:
                monto = float(row.get("Monto Total", 0))
                self.tree.insert("", tk.END, values=(
                    fecha_str,
                    row.get("Actividad", ""),
                    monto,
                    row.get("Trabajador", "")
                ))
                total += monto
            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.total_label.configure(text=f"Total Jornal: S/ {total:,.2f}")