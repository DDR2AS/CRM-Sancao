import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from tkcalendar import DateEntry
from tkinter import messagebox
import os
import sys

import pandas as pd

class ResumenFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master, fg_color="white")
        self.process = process

        try:
            self.detalle_datos = self.process.getTransactions()
            self.datos = pd.DataFrame()
        except Exception as e:
            print("Error al obtener datos desde process.getSummaryByWeek():", e)
            self.datos = pd.DataFrame()
            self.detalle_datos = pd.DataFrame()

        # Filtro Fecha inicio y Fecha fin
        filtro_frame = ctk.CTkFrame(self)
        filtro_frame.pack(pady=5, anchor="center")

        # Obtener primer día del mes actual
        hoy = datetime.today()
        first_day = hoy.replace(day=1)

        ctk.CTkLabel(filtro_frame, text="Fecha Inicio:").pack(side="left", padx=(10, 5))
        self.date_inicio = DateEntry(filtro_frame, date_pattern="yyyy-mm-dd")
        self.date_inicio.set_date(first_day)  # Asignamos el primer día del mes
        self.date_inicio.pack(side="left", padx=5, pady=10)


        ctk.CTkLabel(filtro_frame, text="Fecha Fin:").pack(side="left", padx=(10, 5))
        self.date_fin = DateEntry(filtro_frame, date_pattern="yyyy-mm-dd")
        self.date_fin.pack(side="left", padx=5, pady=10)

        ctk.CTkButton(filtro_frame, text="Filtrar", command=self.aplicar_filtro_fechas).pack(side="left", padx=10, pady=10)
        # ===================== TOTALES ===================== #
        frame_totales = ctk.CTkFrame(self, fg_color="white")
        frame_totales.pack(anchor="w", padx=20, pady=5)

        # Sub-frame para gasto
        frame_gasto = ctk.CTkFrame(frame_totales, fg_color="#ff4d4f", corner_radius=10)
        frame_gasto.pack(side="left", padx=(0, 15), ipadx=15, ipady=10)

        self.label_gasto = ctk.CTkLabel(frame_gasto, text="Gasto Total: S/ 0.0", font=("Segoe UI", 15, "bold"), text_color="white")
        self.label_gasto.pack()

        # Sub-frame para jornales
        frame_jornales = ctk.CTkFrame(frame_totales, fg_color="#1c39dd", corner_radius=10)
        frame_jornales.pack(side='left', padx=(0, 15), ipadx=15, ipady=10)

        self.label_jornales = ctk.CTkLabel(frame_jornales, text="Total Jornal: S/ 0.0", font=("Segoe UI", 14, "bold"), text_color="white")
        self.label_jornales.pack()

        # Sub-frame para abono
        frame_abono = ctk.CTkFrame(frame_totales, fg_color="#f1a643", corner_radius=10)
        frame_abono.pack(side='left', padx=(0, 15), ipadx=15, ipady=10)

        self.label_abono = ctk.CTkLabel(frame_abono, text="Gasto Abono: S/ 0.0", font=("Segoe UI", 14, "bold"), text_color="#333")
        self.label_abono.pack()

        # Sub-frame para enviado
        frame_enviado = ctk.CTkFrame(frame_totales, fg_color="#1cddb3", corner_radius=10)
        frame_enviado.pack(side="left", ipadx=15, ipady=10)

        self.label_enviado = ctk.CTkLabel(frame_enviado, text="Total Enviado: S/ 0.0", font=("Segoe UI", 14, "bold"), text_color="#333")
        self.label_enviado.pack()

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
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        # Scrollbar horizontal
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Tabla Detalle
        self.tabla_detalle_columns  = ("Item", "Fecha", "Tipo", "Nombre", "Actividad", "Descripción", "Abono (S/.)" ,"Gasto (S/.)", "Jornal (S/.)" ,"Enviado (S/.)")
        self.width1 = [64,108,125,215,240,169,146,142,150, 150]
        self.tabla_detalle = ttk.Treeview(tabla_frame,
                                          columns=self.tabla_detalle_columns,
                                          show="headings",
                                          height=8,
                                          yscrollcommand=scrollbar_y.set,
                                          xscrollcommand=scrollbar_x.set)
        
        for i, col in enumerate(self.tabla_detalle_columns):
            self.tabla_detalle.heading(col, text=col)
            self.tabla_detalle.column(col, anchor=tk.CENTER, width=self.width1[i])

        self.tabla_detalle.pack(side="left", fill="both", expand=True)
        # Asociar scrollbars
        scrollbar_y.config(command=self.tabla_detalle.yview)
        scrollbar_x.config(command=self.tabla_detalle.xview)
        
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
        #self.boton_mostrar_ancho = ctk.CTkButton(self, text="Mostrar ancho columnas", command=self.mostrar_ancho_columnas)
        #self.boton_mostrar_ancho.pack(pady=(0, 15))
        self.cargar_detalle_datos(self.detalle_datos)
        self.aplicar_filtro_fechas()

    # ========= FUNCIONES ========= #
    def recargar_tabla(self):
        try:
            self.detalle_datos = self.process.getTransactions()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.tabla_detalle_columns  = ("Item", "Fecha", "Tipo", "Nombre", "Actividad", "Descripción", "Abono (S/.)" ,"Gasto (S/.)", "Jornal (S/.)" ,"Enviado (S/.)")
            self.detalle_datos = pd.DataFrame(columns=self.tabla_detalle_columns)
            self.cargar_detalle_datos(self.detalle_datos)

    def mostrar_ancho_columnas(self):
        print("Anchura actual de columnas:")
        for col in self.tabla_detalle_columns:
            ancho = self.tabla_detalle.column(col)["width"]
            print(f" - {col}: {ancho} px")

    def cargar_detalle_datos(self, datos):
        # Limpiar tabla antes de cargar
        for i in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(i)

        # Ordenando las filas ascendente por fecha
        if "Fecha" in datos.columns:
            datos = datos.sort_values(by="Fecha", ascending=True)

        total_gastos = 0.0
        total_jornal = 0.0
        total_enviado = 0.0
        total_abono = 0.0

        for idx, row in enumerate(datos.itertuples(index=False), start=1):
            fecha = row.Fecha
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_str = fecha.strftime("%Y-%m-%d")

            # Limpiando valores NaN
            tipo = row.Tipo if pd.notna(getattr(row, "Tipo", "")) else ""
            nombre = row.Nombre if pd.notna(getattr(row, "Nombre", "")) else ""
            actividad = row.Actividad if pd.notna(getattr(row, "Actividad", "")) else ""
            descripcion = row.Descripcion if pd.notna(getattr(row, "Descripcion", "")) else ""
            gastoAbono = row.GastoAbono if pd.notna(getattr(row, "GastoAbono", "")) else 0.0
            monto = row.Monto if pd.notna(getattr(row, "Monto", "")) else 0.0
            jornal = row.Jornal if pd.notna(getattr(row, "Jornal", "")) else 0.0
            enviado = row.Enviado if pd.notna(getattr(row, "Enviado", "")) else 0.0

            # Insertar en tabla
            self.tabla_detalle.insert("", "end", values=(
                idx,
                fecha_str,
                tipo,
                nombre,
                actividad,
                descripcion,
                f"{gastoAbono:.2f}" if gastoAbono else "",
                f"{monto:.2f}" if monto else "",
                f"{jornal:.2f}" if jornal else "",
                f"{enviado:.2f}" if enviado else ""
            ))

            # Acumular totales
            total_gastos += float(monto)
            total_jornal += float(jornal)
            total_enviado += float(enviado)
            total_abono += float(gastoAbono)

        # Actualizar labels de totales
        self.label_gasto.configure(text=f"Gasto Total: S/{total_gastos:,.1f}")
        self.label_jornales.configure(text=f"Total Jornal: S/{total_jornal:,.1f}")
        self.label_enviado.configure(text=f"Total Enviado: S/{total_enviado:,.1f}")
        self.label_abono.configure(text=f"Gasto Abono: S/{total_abono:,.1f}")

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

        self.datos_filtrados = df[
            (df["Fecha"] >= fecha_ini) &
            (df["Fecha"] <= fecha_fin)
        ]

        self.cargar_detalle_datos(self.datos_filtrados)
    
    def exportar_a_excel(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="Guardar archivo como..."
        )
        
        if file_path:
            try:
                # Asegurarse de que sea una ruta absoluta
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                
                # Guardar el Excel
                self.datos_filtrados.to_excel(file_path, index=False)
                messagebox.showinfo("Éxito", f"Exportado exitosamente a:\n{file_path}")
                print(f"Exportado exitosamente a {file_path}")
            except PermissionError:
                messagebox.showerror("Error", "No se pudo guardar el archivo. Verifica permisos o cierra el archivo si está abierto.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar:\n{e}")
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