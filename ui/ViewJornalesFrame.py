from tkinter import messagebox, ttk
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from datetime import datetime
from tkcalendar import DateEntry
import pandas as pd

from services.process import Pipelines

class JornalesFrame(ctk.CTkFrame):
    def __init__(self, master, process: Pipelines):
        super().__init__(master, fg_color="white")

        self.process = process

        try:
            self.datos = self.process.getJornales()
        except Exception as e:
            print("Error al obtener datos desde process.getJornales(): ", e)
            self.columns = ("COD", "Fecha Trabajo", "Actividad", "Descripción", "Monto Total", "Trabajador", "Tipo")
            self.datos = pd.DataFrame(columns=self.columns)

        # ===================== HEADER ===================== #
        header_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x")

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=15)

        # Título
        ctk.CTkLabel(
            header_inner,
            text="Gestión de Jornales",
            font=("Segoe UI", 24, "bold"),
            text_color="#1a1a2e"
        ).pack(side="left")

        # Filtro frame (derecha)
        filtro_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        filtro_frame.pack(side="right")

        # Obtener primer día del mes actual
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
            command=self.filterTableByDates,
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

        # Card Jornal Diario
        frame_diario = ctk.CTkFrame(totales_frame, fg_color="#1c39dd", corner_radius=10)
        frame_diario.pack(side="left")

        diario_inner = ctk.CTkFrame(frame_diario, fg_color="transparent")
        diario_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(diario_inner, text="J. DIARIO", font=("Segoe UI", 11), text_color="#C5CAF5").pack(anchor="w")
        self.label_diario = ctk.CTkLabel(diario_inner, text="S/ 0.0", font=("Segoe UI", 22, "bold"), text_color="white")
        self.label_diario.pack(anchor="w")

        # Card Jornal Mensual
        frame_mensual = ctk.CTkFrame(totales_frame, fg_color="#1ca0dd", corner_radius=10)
        frame_mensual.pack(side="left", padx=(15, 0))

        mensual_inner = ctk.CTkFrame(frame_mensual, fg_color="transparent")
        mensual_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(mensual_inner, text="J. MENSUAL", font=("Segoe UI", 11), text_color="#C5E8F5").pack(anchor="w")
        self.label_mensual = ctk.CTkLabel(mensual_inner, text="S/ 0.0", font=("Segoe UI", 22, "bold"), text_color="white")
        self.label_mensual.pack(anchor="w")

        # Card Total
        frame_total = ctk.CTkFrame(totales_frame, fg_color="#6C757D", corner_radius=10)
        frame_total.pack(side="left", padx=(15, 0))

        total_inner = ctk.CTkFrame(frame_total, fg_color="transparent")
        total_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(total_inner, text="TOTAL", font=("Segoe UI", 11), text_color="#E9ECEF").pack(anchor="w")
        self.label_gasto = ctk.CTkLabel(total_inner, text="S/ 0.0", font=("Segoe UI", 22, "bold"), text_color="white")
        self.label_gasto.pack(anchor="w")

        # Botón Crear (derecha)
        ctk.CTkButton(
            totales_frame,
            text="+ Nuevo Jornal",
            fg_color="#28a745",
            hover_color="#1e7e34",
            text_color="white",
            font=("Segoe UI", 13, "bold"),
            width=140,
            height=38,
            corner_radius=8,
            command=self.insert_new_data
        ).pack(side="right")

        # ===================== TABLA ===================== #
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        font=("Segoe UI", 13),
                        rowheight=38,
                        background="#FFFFFF",
                        fieldbackground="#FFFFFF",
                        foreground="#222222",
                        borderwidth=1,
                        relief="solid")
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 13, "bold"),
                        background="#2C3E50",
                        foreground="#FFFFFF",
                        relief="flat",
                        padding=(10, 8))
        style.map("Treeview",
                  background=[("selected", "#E3F2FD")],
                  foreground=[("selected", "#1565C0")])
        style.map("Treeview.Heading",
                  background=[("active", "#34495E")])

        # Frame contenedor para tabla y scrollbar
        tabla_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        tabla_container.pack(fill="both", expand=True, padx=25, pady=(5, 15))

        tabla_frame = tk.Frame(tabla_container, bg="#FFFFFF")
        tabla_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

        # Tabla Detalle
        self.columns = ("COD", "Fecha Trabajo", "Actividad", "Descripción", "Monto Total", "Trabajador", "Tipo")
        self.widths = [80, 110, 150, 180, 110, 220, 90]
        self.tree = ttk.Treeview(
            tabla_frame,
            columns=self.columns,
            show="headings",
            height=10,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=self.widths[i])

        # Tags para filas alternadas
        self.tree.tag_configure("oddrow", background="#FFFFFF")
        self.tree.tag_configure("evenrow", background="#F5F5F5")

        # Ubicación de tabla y scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Configurar scrollbars
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # Expandir tabla al redimensionar
        tabla_frame.grid_rowconfigure(0, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.filterTableByDates()

    # ========= FUNCIONES ========= #
    def insert_new_data(self):
        insert_window = ctk.CTkToplevel(self)
        insert_window.title("Nuevo Jornal")

        # --- Centrar ventana ---
        insert_window.update_idletasks()
        width, height = 450, 480
        x = (insert_window.winfo_screenwidth() // 2) - (width // 2)
        y = (insert_window.winfo_screenheight() // 2) - (height // 2)
        insert_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header con color ---
        header_bg = ctk.CTkFrame(insert_window, fg_color="#1c39dd", corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Nuevo Jornal",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text="Registrar trabajo diario",
            font=("Segoe UI", 12),
            text_color="#C5CAF5"
        ).pack(anchor="w")

        # --- Main container ---
        main_frame = ctk.CTkFrame(insert_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=15)

        # --- Form frame ---
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)

        # Opciones para Actividad y Tipo
        actividades = [
            "Chaleo", "Poda", "Cosecha", "Secado", "Fermentado",
            "Cortar Árboles", "Vivero", "Mantenimiento de equipo",
            "Abono", "Limpieza", "Otro"
        ]
        tipos = ["Diario", "Mensual"]

        entries = {}
        row_idx = 0
        for col in self.columns:
            if col == "COD":
                continue  # Skip COD for new entries

            label = ctk.CTkLabel(form_frame, text=col, font=("Segoe UI", 14, "bold"), text_color="#222222", anchor="w")
            label.grid(row=row_idx, column=0, padx=(0, 12), pady=6, sticky="w")

            if col == "Actividad":
                combo = ctk.CTkComboBox(form_frame, values=actividades, width=240, font=("Segoe UI", 13))
                combo.set("")
                combo.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = combo
            elif col == "Tipo":
                combo = ctk.CTkComboBox(form_frame, values=tipos, width=240, font=("Segoe UI", 13))
                combo.set("Diario")
                combo.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = combo
            elif col == "Descripción":
                text_widget = ctk.CTkTextbox(form_frame, width=240, height=60, font=("Segoe UI", 13))
                text_widget.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = text_widget
            elif col == "Fecha Trabajo":
                date_entry = DateEntry(form_frame, date_pattern="yyyy-mm-dd", font=("Segoe UI", 11), width=18)
                date_entry.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = date_entry
            else:
                entry = ctk.CTkEntry(form_frame, width=240, font=("Segoe UI", 13))
                entry.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = entry

            row_idx += 1

        # --- Button frame ---
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))

        btn_cancelar = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            fg_color="#6C757D",
            hover_color="#5A6268",
            width=110,
            height=38,
            font=("Segoe UI", 14, "bold"),
            command=insert_window.destroy
        )
        btn_cancelar.pack(side="left")

        btn_guardar = ctk.CTkButton(
            button_frame,
            text="Guardar Jornal",
            fg_color="#28a745",
            hover_color="#1e7e34",
            width=140,
            height=38,
            font=("Segoe UI", 14, "bold")
        )
        btn_guardar.pack(side="right")

        # --- Funciones Guardar ---
        def save_new_entry():
            new_values = []
            for col in self.columns:
                if col == "COD":
                    new_values.append("")  # Will be generated by backend
                    continue
                widget = entries.get(col)
                if isinstance(widget, ctk.CTkEntry):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkComboBox):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkTextbox):
                    new_values.append(widget.get("1.0", "end").strip())
                elif isinstance(widget, DateEntry):
                    new_values.append(widget.get())
                else:
                    new_values.append("")

            data = dict(zip(self.columns, new_values))

            # Aquí iría tu lógica real de guardado:
            # self.process.insertJornal(data)
            print("Nuevo registro:", data)

            messagebox.showinfo("Éxito", "Nuevo Jornal creado correctamente.")
            insert_window.destroy()

        btn_guardar.configure(command=save_new_entry)
        
    def recargar_tabla(self):
        try:
            self.datos = self.process.getJornales()
            self.filterTableByDates()
        except Exception as e:
            print("Error al recargar la tabla:", e)
            self.columns = ("COD","Fecha Trabajo", "Actividad", "Descripción", "Monto Total", "Trabajador")
            self.datos = pd.DataFrame(columns=self.columns)
            self.filterTableByDates()

    def on_double_click(self,event):
        item_id = self.tree.focus()
        if not item_id:
            return
        values = self.tree.item(item_id, "values")
        self.open_edit_window(item_id, values)

    def open_edit_window(self, item_id, values):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editar Jornal")

        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 450, 480
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header con color ---
        header_bg = ctk.CTkFrame(edit_window, fg_color="#1c39dd", corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Editar Jornal",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text=f"Código: {values[0]}",
            font=("Segoe UI", 12),
            text_color="#C5CAF5"
        ).pack(anchor="w")

        # --- Main container ---
        main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=15)

        # --- Form frame ---
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)

        # Opciones para Actividad y Tipo
        actividades = [
            "Chaleo", "Poda", "Cosecha", "Secado", "Fermentado",
            "Cortar Árboles", "Vivero", "Mantenimiento de equipo",
            "Abono", "Limpieza", "Otro"
        ]
        tipos = ["Diario", "Mensual"]

        entries = {}
        row_idx = 0
        for i, col in enumerate(self.columns):
            # Skip COD in form since it's in header
            if col == "COD":
                entry = ctk.CTkEntry(form_frame, width=240, fg_color="#D0D0D0", text_color="#444444")
                entry.insert(0, values[i])
                entry.configure(state="disabled")
                entries[col] = entry
                continue

            label = ctk.CTkLabel(form_frame, text=col, font=("Segoe UI", 14, "bold"), text_color="#222222", anchor="w")
            label.grid(row=row_idx, column=0, padx=(0, 12), pady=6, sticky="w")

            if col == "Actividad":
                combo = ctk.CTkComboBox(form_frame, values=actividades, width=240, font=("Segoe UI", 13))
                combo.set(values[i] if values[i] else "")
                combo.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = combo
            elif col == "Tipo":
                combo = ctk.CTkComboBox(form_frame, values=tipos, width=240, font=("Segoe UI", 13))
                combo.set(values[i] if values[i] else "Diario")
                combo.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = combo
            elif col == "Descripción":
                text_widget = ctk.CTkTextbox(form_frame, width=240, height=60, font=("Segoe UI", 13))
                text_widget.insert("1.0", values[i] if values[i] else "")
                text_widget.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = text_widget
            else:
                entry = ctk.CTkEntry(form_frame, width=240, font=("Segoe UI", 13))
                entry.insert(0, values[i] if values[i] else "")
                entry.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = entry

            row_idx += 1

        # --- Button frame ---
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))

        btn_eliminar = ctk.CTkButton(
            button_frame,
            text="Eliminar",
            fg_color="#E53935",
            hover_color="#C62828",
            width=110,
            height=38,
            font=("Segoe UI", 14, "bold")
        )
        btn_eliminar.pack(side="left")

        btn_guardar = ctk.CTkButton(
            button_frame,
            text="Guardar cambios",
            fg_color="#4CAF50",
            hover_color="#388E3C",
            width=140,
            height=38,
            font=("Segoe UI", 14, "bold")
        )
        btn_guardar.pack(side="right")

        # --- Funciones Guardar / Eliminar ---
        def save_changes():
            new_values = []
            for col in self.columns:
                widget = entries[col]
                if isinstance(widget, ctk.CTkEntry):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkComboBox):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkTextbox):
                    new_values.append(widget.get("1.0", "end").strip())
                else:
                    new_values.append("")

            values_dict = dict(zip(self.columns, new_values))

            self.process.updateJornal(
                j_code=new_values[0],
                data=values_dict
            )
            self.tree.item(item_id, values=new_values)
            self.recargar_tabla()
            edit_window.destroy()

        def delete_jornal():
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar este jornal?"):
                if self.process.deleteJornal(values[0]):
                    self.tree.delete(item_id)
                self.recargar_tabla()
                edit_window.destroy()

        btn_guardar.configure(command=save_changes)
        btn_eliminar.configure(command=delete_jornal)

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
        datos = datos.sort_values(by="COD", ascending=True)

        total = 0.0
        total_diario = 0.0
        total_mensual = 0.0
        row_count = 0

        for _, row in datos.iterrows():
            fecha = row['Fecha Trabajo']
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_str = fecha.strftime("%Y-%m-%d")
            try:
                monto = float(row.get("Monto Total", 0))
                descripcion = row.Descripcion if pd.notna(getattr(row, "Descripcion", "")) else ""
                tipo = row.Periodo if pd.notna(getattr(row, "Periodo", "")) else ""

                # Alternar colores de fila
                tag = "evenrow" if row_count % 2 == 0 else "oddrow"
                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    row.get("Actividad", ""),
                    descripcion,
                    f"{monto:.2f}",
                    row.get("Trabajador", ""),
                    tipo
                ), tags=(tag,))

                total += monto
                if tipo == "Mensual":
                    total_mensual += monto
                else:
                    total_diario += monto
                row_count += 1

            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.label_diario.configure(text=f"S/ {total_diario:,.2f}")
        self.label_mensual.configure(text=f"S/ {total_mensual:,.2f}")
        self.label_gasto.configure(text=f"S/ {total:,.2f}")