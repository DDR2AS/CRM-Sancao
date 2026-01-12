import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from tkcalendar import DateEntry
from tkinter import messagebox
import pandas as pd
import os
import sys
import subprocess

from services.process import Pipelines


class ToolTip:
    """Tooltip widget for Treeview cells."""
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.text = ""

    def show(self, text, x, y):
        if not text or self.tip_window:
            return
        self.text = text
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw, text=text, justify="left",
            background="#FFFFD0", foreground="#333",
            relief="solid", borderwidth=1,
            font=("Segoe UI", 10),
            wraplength=400,
            padx=8, pady=5
        )
        label.pack()

    def hide(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class ResumenFrame(ctk.CTkFrame):
    def __init__(self, master, process : Pipelines):
        super().__init__(master, fg_color="white")
        self.process = process

        try:
            self.detalle_datos = self.process.getTransactions()
            self.datos = pd.DataFrame()
        except Exception as e:
            print("Error al obtener datos desde process.getSummaryByWeek():", e)
            self.datos = pd.DataFrame()
            self.detalle_datos = pd.DataFrame()

        # ===================== HEADER ===================== #
        header_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x")

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Reporte Semanal",
            font=("Segoe UI", 24, "bold"),
            text_color="#1a1a2e"
        ).pack(side="left")

        # Filtro (derecha)
        filtro_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        filtro_frame.pack(side="right")

        hoy = datetime.today()
        first_day = hoy.replace(day=1)

        ctk.CTkLabel(filtro_frame, text="Desde:", font=("Segoe UI", 12), text_color="#555").pack(side="left", padx=(0, 5))
        self.date_inicio = DateEntry(filtro_frame, date_pattern="yyyy-mm-dd", font=("Segoe UI", 10))
        self.date_inicio.set_date(first_day)
        self.date_inicio.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(filtro_frame, text="Hasta:", font=("Segoe UI", 12), text_color="#555").pack(side="left", padx=(0, 5))
        self.date_fin = DateEntry(filtro_frame, date_pattern="yyyy-mm-dd", font=("Segoe UI", 10))
        self.date_fin.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            filtro_frame,
            text="Filtrar",
            command=self.aplicar_filtro_fechas,
            width=90,
            height=32,
            font=("Segoe UI", 12, "bold"),
            fg_color="#3EA5FF",
            hover_color="#2196F3",
            corner_radius=6
        ).pack(side="left")

        # ===================== TOTALES ===================== #
        totales_frame = ctk.CTkFrame(self, fg_color="transparent")
        totales_frame.pack(fill="x", padx=25, pady=(15, 10))

        # Card Gasto
        self._create_total_card(totales_frame, "GASTOS", "gasto", "#DC3545", "#FFD6D9", "white")
        # Card Jornal Diario
        self._create_total_card(totales_frame, "J. DIARIO", "jornales_diario", "#1c39dd", "#C5CAF5", "white")
        # Card Jornal Mensual
        self._create_total_card(totales_frame, "J. MENSUAL", "jornales_mensual", "#1ca0dd", "#C5E8F5", "white")
        # Card Abono
        self._create_total_card(totales_frame, "ABONO", "abono", "#f1a643", "#FDE8C8", "#333")
        # Card Enviado
        self._create_total_card(totales_frame, "ENVIADO", "enviado", "#17a2b8", "#C5F0F5", "white")
        # Card Ventas
        self._create_total_card(totales_frame, "VENTAS", "venta", "#28a745", "#C8F5D0", "white")

        # ===================== TABLA ===================== #
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=("Segoe UI", 11),
                        rowheight=34,
                        background="#FFFFFF",
                        fieldbackground="#FFFFFF",
                        foreground="#222222",
                        borderwidth=1)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#2C3E50",
                        foreground="#FFFFFF",
                        relief="flat",
                        padding=(8, 6))
        style.map("Treeview",
                  background=[("selected", "#E3F2FD")],
                  foreground=[("selected", "#1565C0")])

        tabla_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        tabla_container.pack(fill="both", expand=True, padx=25, pady=(5, 10))

        tabla_frame = tk.Frame(tabla_container, bg="#FFFFFF")
        tabla_frame.pack(fill="both", expand=True, padx=2, pady=2)
        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

        # Tabla Detalle
        self.tabla_detalle_columns = ("Item", "Fecha", "Responsable", "Tipo", "Nombre", "Actividad", "Descripción", "Abono (S/.)", "Gasto (S/.)", "Jornal (S/.)", "J. Mensual (S/.)", "Enviado (S/.)", "Venta Cacao (S/.)")
        self.width1 = [50, 90, 110, 80, 150, 120, 160, 90, 90, 90, 95, 90, 110]

        self.tabla_detalle = ttk.Treeview(
            tabla_frame,
            columns=self.tabla_detalle_columns,
            show="headings",
            height=10,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        for i, col in enumerate(self.tabla_detalle_columns):
            self.tabla_detalle.heading(col, text=col)
            self.tabla_detalle.column(col, anchor=tk.CENTER, width=self.width1[i])

        # Grid layout for table
        self.tabla_detalle.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        scrollbar_y.config(command=self.tabla_detalle.yview)
        scrollbar_x.config(command=self.tabla_detalle.xview)

        tabla_frame.grid_rowconfigure(0, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)

        # Colores alternos
        self.tabla_detalle.tag_configure('evenrow', background='#F5F5F5')
        self.tabla_detalle.tag_configure('oddrow', background='#FFFFFF')

        # Tooltip for full description
        self.tooltip = ToolTip(self.tabla_detalle)
        self.full_descriptions = {}  # Store full descriptions by item id
        self.tabla_detalle.bind("<Motion>", self.on_mouse_move)
        self.tabla_detalle.bind("<Leave>", lambda e: self.tooltip.hide())

        # ===================== FOOTER ===================== #
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=25, pady=(5, 15))

        self.boton_exportar = ctk.CTkButton(
            footer_frame,
            text="Exportar a Excel",
            command=self.exportar_a_excel,
            width=150,
            height=38,
            font=("Segoe UI", 13, "bold"),
            fg_color="#28a745",
            hover_color="#1e7e34",
            corner_radius=8
        )
        self.boton_exportar.pack(side="right")
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
    def _truncate_text(self, text, max_length=30):
        """Truncate text and add ellipsis if longer than max_length."""
        text = str(text).replace("\n", " ").replace("\r", "")
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    def on_mouse_move(self, event):
        """Show tooltip when hovering over description column."""
        self.tooltip.hide()
        region = self.tabla_detalle.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tabla_detalle.identify_column(event.x)
        # Column #7 is "Descripción" (1-indexed)
        if column != "#7":
            return

        item = self.tabla_detalle.identify_row(event.y)
        if item and item in self.full_descriptions:
            full_text = self.full_descriptions[item]
            if full_text and len(str(full_text)) > 30:
                x = event.x_root + 15
                y = event.y_root + 10
                self.tooltip.show(full_text, x, y)

    def _create_total_card(self, parent, title, attr_name, bg_color, title_color, value_color):
        """Helper to create a total card."""
        frame = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10)
        frame.pack(side="left", padx=(0, 10))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(padx=15, pady=10)

        ctk.CTkLabel(inner, text=title, font=("Segoe UI", 10, "bold"), text_color=title_color).pack(anchor="w")
        label = ctk.CTkLabel(inner, text="S/ 0.0", font=("Segoe UI", 16, "bold"), text_color=value_color)
        label.pack(anchor="w")

        setattr(self, f"label_{attr_name}", label)

    def recargar_tabla(self):
        try:
            self.detalle_datos = self.process.getTransactions()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.tabla_detalle_columns  = ("Item", "Fecha", "Tipo", "Nombre", "Actividad", "Descripción", "Abono (S/.)" ,"Gasto (S/.)", "Jornal (S/.)" ,"Enviado (S/.)", "Venta Cacao (S/.)")
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

        # Clear stored descriptions
        self.full_descriptions = {}

        # Ordenando las filas ascendente por fecha
        if "Fecha" in datos.columns:
            datos = datos.sort_values(by="Fecha", ascending=True)

        total_gastos = 0.0
        total_jornal_diario = 0.0
        total_jornal_mensual = 0.0
        total_enviado = 0.0
        total_abono = 0.0
        total_venta = 0.0

        for idx, row in enumerate(datos.itertuples(index=False), start=1):
            fecha = row.Fecha
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_str = fecha.strftime("%Y-%m-%d")

            # Limpiando valores NaN
            responsable = row.Responsable if pd.notna(getattr(row, "Responsable", "")) else ""
            tipo = row.Tipo if pd.notna(getattr(row, "Tipo", "")) else ""
            nombre = row.Nombre if pd.notna(getattr(row, "Nombre", "")) else ""
            actividad = row.Actividad if pd.notna(getattr(row, "Actividad", "")) else ""
            descripcion = row.Descripcion if pd.notna(getattr(row, "Descripcion", "")) else ""
            gastoAbono = row.GastoAbono if pd.notna(getattr(row, "GastoAbono", "")) else 0.0
            monto = row.Monto if pd.notna(getattr(row, "Monto", "")) else 0.0
            jornalDiario = row.JornalDiario if pd.notna(getattr(row, "JornalDiario", "")) else 0.0
            jornalMensual = row.JornalMensual if pd.notna(getattr(row, "JornalMensual", "")) else 0.0
            enviado = row.Enviado if pd.notna(getattr(row, "Enviado", "")) else 0.0
            venta = row.Venta if pd.notna(getattr(row, "Venta", "")) else 0.0

            # Truncate description for display
            descripcion_truncada = self._truncate_text(descripcion, max_length=30)

            # Insertar en tabla con colores alternos
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            item_id = self.tabla_detalle.insert("", "end", values=(
                idx,
                fecha_str,
                responsable,
                tipo,
                nombre,
                actividad,
                descripcion_truncada,
                f"{gastoAbono:.2f}" if gastoAbono else "",
                f"{monto:.2f}" if monto else "",
                f"{jornalDiario:.2f}" if jornalDiario else "",
                f"{jornalMensual:.2f}" if jornalMensual else "",
                f"{enviado:.2f}" if enviado else "",
                f"{venta:.2f}" if venta else ""
            ), tags=(tag,))

            # Store full description for tooltip
            self.full_descriptions[item_id] = str(descripcion).replace("\r", "")

            # Acumular totales
            total_gastos += float(monto)
            total_jornal_diario += float(jornalDiario)
            total_jornal_mensual += float(jornalMensual)
            total_enviado += float(enviado)
            total_abono += float(gastoAbono)
            total_venta += float(venta)

        # Actualizar labels de totales
        self.label_gasto.configure(text=f"S/ {total_gastos:,.2f}")
        self.label_jornales_diario.configure(text=f"S/ {total_jornal_diario:,.2f}")
        self.label_jornales_mensual.configure(text=f"S/ {total_jornal_mensual:,.2f}")
        self.label_enviado.configure(text=f"S/ {total_enviado:,.2f}")
        self.label_abono.configure(text=f"S/ {total_abono:,.2f}")
        self.label_venta.configure(text=f"S/ {total_venta:,.2f}")

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
                export_data = self.process.addTotal(self.datos_filtrados)
                self.process.exportSummaryExcelFormatted(export_data, file_path, self.tabla_detalle_columns)
                #export_data.to_excel(file_path, index=False)
                print(f"Exportado exitosamente a {file_path}")

                # Ask user if they want to open the file
                if messagebox.askyesno("Éxito", f"Exportado exitosamente.\n\n¿Desea abrir el archivo?"):
                    # Open file with default application
                    if sys.platform == "win32":
                        os.startfile(file_path)
                    elif sys.platform == "darwin":  # macOS
                        subprocess.run(["open", file_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", file_path])
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