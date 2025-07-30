import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from tkcalendar import DateEntry


import pandas as pd

class ResumenFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master)
        self.process = process

        try:
            self.datos = self.process.getSummaryByWeek()
        except Exception as e:
            print("Error al obtener datos desde process.getSummaryByWeek():", e)
            self.datos = pd.DataFrame()

        # Filtro Fecha inicio y Fecha fin
        filtro_frame = ctk.CTkFrame(self)
        filtro_frame.pack(pady=10)

        ctk.CTkLabel(filtro_frame, text="Fecha Inicio:").pack(side="left", padx=(10, 5))
        self.date_inicio = DateEntry(filtro_frame, date_pattern="yyyy-mm-dd")
        self.date_inicio.pack(side="left", padx=5)

        ctk.CTkLabel(filtro_frame, text="Fecha Fin:").pack(side="left", padx=(10, 5))
        self.date_fin = DateEntry(filtro_frame, date_pattern="yyyy-mm-dd")
        self.date_fin.pack(side="left", padx=5)

        ctk.CTkButton(filtro_frame, text="Filtrar", command=self.aplicar_filtro_fechas).pack(side="left", padx=10)

        # Tabla
        self.columns = ("Fecha Inicio", "Fecha Fin", "Gasto", "Jornal")
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

        # Botón exportar datos
        self.boton_exportar = ctk.CTkButton(self, text="Exportar a Excel", command=self.exportar_a_excel)
        self.boton_exportar.pack(pady=(5, 15))
        
        self.cargar_datos(self.datos)


    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_gasto = 0
        total_jornal = 0

        for _, row in datos.iterrows():
            fecha_ini = row["Fecha Inicio"]
            fecha_fin = row["Fecha Fin"]

            if isinstance(fecha_ini, str):
                fecha_ini = datetime.strptime(fecha_ini, "%Y-%m-%d")
            if isinstance(fecha_fin, str):
                fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

            self.tree.insert("", tk.END, values=(
                fecha_ini.strftime("%Y-%m-%d"),
                fecha_fin.strftime("%Y-%m-%d"),
                f"{row['Gastos']:.2f}",
                f"{row['Jornal']:.2f}"
            ))
            total_gasto += row["Gastos"]
            total_jornal += row["Jornal"]

    def aplicar_filtro_fechas(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas inválidas:", e)
            return

        df = self.datos.copy()
        df["Fecha Inicio"] = pd.to_datetime(df["Fecha Inicio"], errors="coerce")
        df["Fecha Fin"] = pd.to_datetime(df["Fecha Fin"], errors="coerce")

        filtrado = df[
            (df["Fecha Inicio"] >= fecha_ini) &
            (df["Fecha Fin"] <= fecha_fin)
        ]
        self.cargar_datos(filtrado)

    def exportar_a_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            try:
                self.datos.to_excel(file_path, index=False)
                print(f"Exportado exitosamente a {file_path}")
            except Exception as e:
                print(f"Error al exportar: {e}")