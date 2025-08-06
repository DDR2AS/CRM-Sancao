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
            self.detalle_datos = self.process.getTransactions()
            self.datos = pd.DataFrame()#self.process.getSummaryByWeek()
        except Exception as e:
            print("Error al obtener datos desde process.getSummaryByWeek():", e)
            self.datos = pd.DataFrame()
            self.detalle_datos = pd.DataFrame()

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

        # Estilos de la tabla 
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=("Segoe UI", 12),
                        rowheight=32,
                        background="#F9F9F9",
                        fieldbackground="#F9F9F9",
                        foreground="#333333",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 14, "bold"),
                        background="#3EA5FF",
                        foreground="#000000",
                        relief="flat")
        
        # ===================== TABLA DETALLE ===================== #
        # Frame contenedor para tabla y scrollbar
        tabla_frame = tk.Frame(self)
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))
        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        # Tabla Detalle
        self.tabla_detalle_columns  = ("Item", "Fecha", "Tipo", "Nombre", "Actividad", "Monto (S/.)", "Enviado (S/.)")
        self.width1 = [64,109,125,335,345,134,134]
        self.tabla_detalle = ttk.Treeview(tabla_frame,
                                          columns=self.tabla_detalle_columns,
                                          show="headings",
                                          height=8,
                                          yscrollcommand=scrollbar.set)
        
        for i, col in enumerate(self.tabla_detalle_columns):
            self.tabla_detalle.heading(col, text=col)
            self.tabla_detalle.column(col, anchor=tk.CENTER, width=self.width1[i])

        self.tabla_detalle.pack(side="left", fill="both", expand=True)
        
        # Botón exportar datos
        self.boton_exportar = ctk.CTkButton(self, text="Exportar a Excel", command=self.exportar_a_excel)
        self.boton_exportar.pack(pady=(5, 15))
        """
        # Tabla
        self.columns = ("Fecha Inicio", "Fecha Fin", "Gasto", "Jornal", "Envíos Dinero")
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=8)
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=130)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        

        #self.cargar_datos(self.datos)
        """
        self.boton_mostrar_ancho = ctk.CTkButton(self, text="Mostrar ancho columnas", command=self.mostrar_ancho_columnas)
        self.boton_mostrar_ancho.pack(pady=(0, 15))
        self.cargar_detalle_datos(self.detalle_datos)

    # ========= FUNCIONES ========= #
    def mostrar_ancho_columnas(self):
        print("Anchura actual de columnas:")
        for col in self.tabla_detalle_columns:
            ancho = self.tabla_detalle.column(col)["width"]
            print(f" - {col}: {ancho} px")

    def cargar_detalle_datos(self, datos):
        for i in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(i)

        # Ordenando las filas de ascendente
        datos = datos.sort_values(by='Fecha', ascending=True)

        for idx, row in enumerate(datos.iterrows(),start=1):
            _, row = row
            fecha = row['Fecha']
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_str = fecha.strftime("%Y-%m-%d")

            # Filtrando valores nan
            tipo = row['Tipo'] if pd.notna(row.get('Tipo')) else ""
            nombre = row['Nombre'] if pd.notna(row.get('Nombre')) else ""
            actividad = row['Actividad'] if pd.notna(row.get('Actividad')) else ""
            monto = f"{row['Monto']:.2f}" if pd.notna(row.get('Monto')) else ""
            enviado = f"{row['Enviado']:.2f}" if pd.notna(row.get('Enviado')) else ""

            self.tabla_detalle.insert("", "end", values=(
                idx,
                fecha_str,
                tipo,
                nombre,
                actividad,
                monto,
                enviado
            ))

    def aplicar_filtro_fechas(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas inválidas:", e)
            return

        df = self.detalle_datos.copy()
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Actividad"] = df["Actividad"].fillna('')  # Rellenar NaN con ''

        filtrado = df[
            (df["Fecha"] >= fecha_ini) &
            (df["Fecha"] <= fecha_fin)
        ]

        self.cargar_detalle_datos(filtrado)

    def exportar_a_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if file_path:
            try:
                self.detalle_datos.to_excel(file_path, index=False)
                print(f"Exportado exitosamente a {file_path}")
            except Exception as e:
                print(f"Error al exportar: {e}")

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_gasto = 0
        total_jornal = 0
        total_sendMoney = 0

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
                f"{row['Jornal']:.2f}",
                f"{row['sendMoney']:.2f}"
            ))
            total_gasto += row["Gastos"]
            total_jornal += row["Jornal"]
            total_sendMoney += row["sendMoney"]