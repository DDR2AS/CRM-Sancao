from tkinter import messagebox, ttk
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from datetime import datetime
from tkcalendar import DateEntry

import pandas as pd

class JornalesFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master,fg_color="white")

        self.process = process

        try:
            self.datos = self.process.getJornales()
        except Exception as e:
            print("Error al obtener datos desde process.getJornales(): ", e)
            self.datos = pd.DataFrame()

        # Frame contenedor de título y filtros en una sola fila
        titulo_filtro_frame = ctk.CTkFrame(self, fg_color="transparent")
        titulo_filtro_frame.pack(fill="x", padx=20, pady=(10, 0))

        # ===================== TITULO ===================== #
        titulo_label = ctk.CTkLabel(
            titulo_filtro_frame,
            text="Jornales",
            font=("Arial", 22, "bold"),
            anchor="w",
            justify="left"
        )
        titulo_label.pack(side="left", padx=(0, 20))

        # ===================== Filtro Fecha inicio y Fecha fin ===================== #
        filtro_frame = ctk.CTkFrame(titulo_filtro_frame, fg_color="transparent")
        filtro_frame.pack(side="right")  # alineado a la derecha en la misma fila

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

        ctk.CTkButton(
            filtro_frame,
            text="Filtrar",
            command=self.filterTableByDates
        ).pack(side="left", padx=10, pady=10)

        # ===================== TOTALES ===================== #
        frame_totales = ctk.CTkFrame(self, fg_color="white")
        frame_totales.pack(anchor="w", padx=20, pady=5)

        # Sub-frame para Jornal
        frame_jornal = ctk.CTkFrame(frame_totales, fg_color="#1c69f7", corner_radius=10)
        frame_jornal.pack(side="left", padx=(0, 15), ipadx=15, ipady=10)

        self.label_gasto = ctk.CTkLabel(frame_jornal, text="Total Jornal: S/ 0.0", font=("Segoe UI", 15, "bold"), text_color="white")
        self.label_gasto.pack()

        # Estilos de tabla
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
        self.columns = ("COD","Fecha Trabajo", "Actividad", "Monto Total", "Trabajador")
        self.width1 = [70,120,300,300,300]
        self.tree = ttk.Treeview(tabla_frame, columns=self.columns, show="headings", height=8, yscrollcommand=scrollbar_y, xscrollcommand=scrollbar_x)
        
        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=self.width1[i])
        
        self.tree.pack(side="left", fill="both", expand=True)
        # Asociar scrollbars
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.cargar_datos(self.datos)

        # ========= FUNCIONES ========= #
    def recargar_tabla(self):
        try:
            self.datos = self.process.getJornales()
            self.cargar_datos(self.datos)
        except Exception as e:
            print("Error al recargar la tabla:", e)
    def on_double_click(self,event):
        item_id = self.tree.focus()
        if not item_id:
            return
        values = self.tree.item(item_id, "values")
        self.open_edit_window(item_id, values)

    def open_edit_window(self, item_id, values):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editar Jornal")
        edit_window.geometry("350x260")
        self.archivo_subido = None
        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 380, 260
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f"{width}x{height}+{x}+{y}")

        entries = {}
        for i, col in enumerate(self.columns):
            label = ctk.CTkLabel(edit_window, text=col)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            entry = ctk.CTkEntry(edit_window, width=250)
            entry.insert(0, values[i])
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries[col] = entry

        # --- Botones de acción ---
        button_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        button_frame.grid(row=len(self.columns)+1, column=0, columnspan=2, pady=20)

        btn_guardar = ctk.CTkButton(button_frame, text="Guardar", fg_color="#4CAF50")
        btn_guardar.pack(side="left", padx=10)
        btn_eliminar = ctk.CTkButton(button_frame, text="Eliminar", fg_color="#E53935")
        btn_eliminar.pack(side="left", padx=10)

        # --- Funciones Guardar / Eliminar ---
        def save_changes():
            new_values = [entries[col].get() for col in self.columns]
            values = dict(zip(self.columns, new_values))

            self.process.updateJornal(
                j_code=new_values[0],
                data=values
            )
            self.tree.item(item_id, values=new_values)
            self.recargar_tabla()
            edit_window.destroy()

        def delete_sendMoney():
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta Jornal?"):
                if self.process.deleteJornal(values[0]):
                    self.tree.delete(item_id)
                self.recargar_tabla()
                edit_window.destroy()

        btn_guardar.configure(command=save_changes)
        btn_eliminar.configure(command=delete_sendMoney)

    def filterTableByDates(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas inválidas:", e)
            return

        df = self.datos.copy()
        df["Fecha Trabajo"] = pd.to_datetime(df["Fecha Trabajo"], errors="coerce")
        df["Actividad"] = df["Actividad"].fillna('') 

        self.datos_filtrados = df[
            (df["Fecha Trabajo"] >= fecha_ini) &
            (df["Fecha Trabajo"] <= fecha_fin)
        ]

        self.cargar_datos(self.datos_filtrados)

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)
        datos = datos.sort_values(by="Fecha Trabajo", ascending=True)
        total = 0.0
        for _, row in datos.iterrows():
            fecha = row['Fecha Trabajo']
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_str = fecha.strftime("%Y-%m-%d")
            try:
                monto = float(row.get("Monto Total", 0))
                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    row.get("Actividad", ""),
                    monto,
                    row.get("Trabajador", "")
                ))
                total += monto
            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.label_gasto.configure(text=f"Total Jornal: S/ {total:,.1f}")