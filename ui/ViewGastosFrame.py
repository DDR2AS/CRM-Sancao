from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from tkcalendar import DateEntry
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import webbrowser
import pandas as pd
import threading
import shutil
import base64
import os

class GastosFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master, fg_color="white")
        self.process = process
        
        try:
            self.datos = self.process.getGastos()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.columns = ("COD","Fecha", "Tipo", "Producto", "Cantidad", "Monto Total", "Descripción", "Url")
            self.datos = pd.DataFrame(columns=self.columns)

        # Iniciar actualización automática cada 2 minutos (120,000 ms)
        self.after(60000, self.update_cronjob)

        # Frame contenedor de título y filtro en una sola fila
        titulo_filtro_frame = ctk.CTkFrame(self, fg_color="transparent")
        titulo_filtro_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        # ===================== TITULO ===================== #
        # Label de título
        titulo_label = ctk.CTkLabel(
            titulo_filtro_frame,
            text="Gastos (Abono - Menú - Víveres - Gastos)",
            font=("Arial", 22, "bold"),
            anchor="w",
            justify="left"
        )
        titulo_label.pack(side="left", padx=(0, 20))  # un poco de espacio a la derecha

        filtro_frame = ctk.CTkFrame(titulo_filtro_frame, fg_color="transparent")
        filtro_frame.pack(side="right")
        
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

        # ===================== TOTALES GASTOS ===================== #
        frame_totales = ctk.CTkFrame(self, fg_color="white")
        frame_totales.pack(anchor="w", padx=20, pady=12)

        # Sub-frame para gasto
        frame_gasto = ctk.CTkFrame(frame_totales, fg_color="#ff4d4f", corner_radius=10)
        frame_gasto.pack(side="left", ipadx=15, ipady=10)
        
        self.label_gasto = ctk.CTkLabel(frame_gasto, text="Gasto Total: S/ 0.0", font=("Segoe UI", 15, "bold"), text_color="white")
        self.label_gasto.pack()

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
        # ===================== TABLA ===================== #
        # Frame contenedor para tabla y scrollbar
        tabla_frame = tk.Frame(self)
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")

        # Scrollbar horizontal
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

        # Tabla
        self.columns = ("COD","Fecha", "Tipo", "Producto", "Cantidad", "Monto Total", "Descripción", "Url")
        self.widths = [70, 120, 64, 181, 95, 140, 300,200]

        self.tree = ttk.Treeview(
            tabla_frame,
            columns=self.columns,
            show="headings",
            height=8,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        # Configuración de columnas
        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            if col == "Descripción":
                self.tree.column(col, anchor=tk.W, width=self.widths[i])  # izquierda
            else:
                self.tree.column(col, anchor=tk.CENTER, width=self.widths[i])  # centrado

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

        # Para poder editar con doble click
        self.tree.bind("<Double-1>", self.on_double_click)

        # Tooltip para descripción
        self.tooltip = tk.Label(self.tree, text="", bg="yellow", wraplength=300, relief="solid", borderwidth=1)
        self.tooltip.place_forget()

        self.tree.bind("<Motion>", self.show_tooltip)
        self.tree.bind("<Leave>", lambda e: self.tooltip.place_forget())
        
        # To delete
        #self.boton_mostrar_ancho = ctk.CTkButton(self, text="Mostrar ancho columnas", command=self.mostrar_ancho_columnas)
        #self.boton_mostrar_ancho.pack(pady=(0, 15))
        self.cargar_datos(self.datos)

    # ========= FUNCIONES ========= #
    def filterTableByDates(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas inválidas:", e)
            return

        df = self.datos.copy()
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

        self.datos_filtrados = df[
            (df["Fecha"] >= fecha_ini) & (df["Fecha"] <= fecha_fin)
        ]
        self.cargar_datos(self.datos_filtrados)

    def recargar_tabla(self):
        try:
            self.datos = self.process.getGastos()
            self.cargar_datos(self.datos)
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.columns = ("COD","Fecha", "Tipo", "Producto", "Cantidad", "Monto Total", "Descripción", "Url")
            self.datos = pd.DataFrame(columns=self.columns)
            self.cargar_datos(self.datos)

    def update_cronjob(self):
        print(f"[{datetime.now()}] Recargando datos...")
        self.recargar_tabla()
        self.filterTableByDates()
        self.after(120000, self.update_cronjob)  # 2 minutos

    def mostrar_ancho_columnas(self):
        print("Anchura actual de columnas:")
        for col in self.columns:
            ancho = self.tree.column(col)["width"]
            print(f" - {col}: {ancho} px")

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = 0.0
        for _, row in datos.iterrows():
            try:
                cantidad = row.get("Cantidad", 0)
                monto = float(row.get("Monto Total", 0))
                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    row.get("Fecha", ""),
                    row.get("Tipo", ""),
                    row.get("Producto", ""),
                    cantidad,
                    monto,
                    row.get("Descripcion", ""),
                    row.get("fileDriveUrl","")
                ))
                total += monto
            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.label_gasto.configure(text=f"Gasto Total: S/ {total:,.1f}")
    
    def on_double_click(self, event):
        item_id = self.tree.focus()
        # Detectar fila y columna
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not row_id or not col_id:
            return

        col_index = int(col_id.replace("#", "")) - 1
        values = self.tree.item(row_id, "values")

        # Si es columna URL → abrir en navegador
        if self.columns[col_index] == "Url":
            url = values[col_index]
            if url.strip().startswith("http"):
                chrome_path = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chrome.exe")
                if chrome_path:
                    webbrowser.get(f'"{chrome_path}" %s').open(url)
                else:
                    webbrowser.open(url)
        else :
            self.open_edit_window(item_id, values)
    
    def open_edit_window(self, item_id, values):
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editar Gasto")
        edit_window.geometry("380x520")
        self.archivo_subido = None
        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 380, 520
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f"{width}x{height}+{x}+{y}")

        entries = {}
        for i, col in enumerate(self.columns):
            label = ctk.CTkLabel(edit_window, text=col)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if col == 'Descripción':
                text_widget = ctk.CTkTextbox(edit_window, width=250, height=80)
                text_widget.grid(row=i, column=1, padx=10, pady=10, sticky="w")
                text_widget.insert("1.0", values[i])
                entries[col] = text_widget
            elif col == "Producto":
                combo = ctk.CTkComboBox(
                    edit_window,
                    values=[
                        "Abono", "Aceite Quemado", "Aceite para Lubricar",
                        "Gasolina", "Latiguillos", "Urea",
                        "Manta para secado", "Baldes de plástico",
                        "Sacos", "Herramientas"
                    ],
                    width=250
                )
                combo.set(values[i])  # valor actual
                combo.grid(row=i, column=1, padx=10, pady=10, sticky="w")
                entries[col] = combo
            else:
                entry = ctk.CTkEntry(edit_window, width=250)
                entry.insert(0, values[i])
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
                entries[col] = entry

        button_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        button_frame.grid(row=len(self.columns)+1, column=0, columnspan=2, pady=20)

        btn_guardar = ctk.CTkButton(button_frame, text="Guardar", fg_color="#4CAF50")
        btn_guardar.pack(side="left", padx=10)
        btn_eliminar = ctk.CTkButton(button_frame, text="Eliminar", fg_color="#E53935")
        btn_eliminar.pack(side="left", padx=10)

        def save_changes():
            new_values = []
            for col in self.columns:
                widget = entries[col]
                if isinstance(widget, ctk.CTkEntry):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkComboBox):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkTextbox):
                    # Para CTkTextbox necesitamos índices
                    new_values.append(widget.get("0.0", "end").strip())
                else:
                    new_values.append(None)  # Por si acaso
            values = dict(zip(self.columns, new_values))
            if self.archivo_subido:
                values["fileDriveId"] = self.archivo_subido.get("fileDriveId", "")
            print(values)
            # Guardar en BD
            self.process.updateExpenses(
                e_code=new_values[0],
                data=values
            )
            self.tree.item(item_id, values=new_values)
            self.archivo_subido = {"fileDriveId": "", "fileDriveUrl": ""}
            self.recargar_tabla()
            edit_window.destroy()

        def delete_expense():
            if tk.messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar este gasto?"):
                if self.process.deleteExpense(values[0]):  # values[0] = COD
                    self.tree.delete(item_id)  # eliminar de la tabla
                self.recargar_tabla()
                edit_window.destroy()

        btn_guardar.configure(command=save_changes)
        btn_eliminar.configure(command=delete_expense)

        # --- Selector de archivo ---
        file_path_var = tk.StringVar()
        # --- Label de estado ---
        status_label = ctk.CTkLabel(edit_window, text="", fg_color="transparent", text_color="gray")
        status_label.grid(row=len(self.columns)+2, column=0, columnspan=2, pady=5)

        def seleccionar_archivo():
            self.archivo_subido = {"fileDriveId": "", "fileDriveUrl": ""}
            archivo = filedialog.askopenfilename(parent=edit_window,filetypes=[("Todos los archivos", "*.*")])
            if archivo:
                file_path_var.set(archivo)

                # Deshabilitar botones mientras sube
                btn_guardar.configure(state="disabled")
                btn_eliminar.configure(state="disabled")
                # Actualizar label a "subiendo..."
                status_label.configure(text="Subiendo archivo a Drive...")

                def subir_archivo():
                    archivo_info = None
                    with open(archivo, "rb") as f:
                        archivo_info = {
                            "nombre": os.path.basename(archivo),
                            "base64": base64.b64encode(f.read()).decode("utf-8"),
                            "tipo": os.path.splitext(archivo)[-1]
                        }
                    resultado = self.process.uploadFile(file_info=archivo_info)
                    
                    self.archivo_subido["fileDriveId"] = resultado.get("fileDriveId", "")
                    self.archivo_subido["fileDriveUrl"] = resultado.get("fileDriveUrl", "")

                    # Actualizar entry de URL en el hilo principal
                    edit_window.after(0, lambda res=resultado: entries["Url"].delete(0, "end"))
                    edit_window.after(0, lambda res=resultado: entries["Url"].insert(0, res.get("fileDriveUrl", "")))
                    edit_window.after(0, lambda res=resultado: entries["Url"].icursor("end"))

                    # Rehabilitar botones en el hilo principal
                    edit_window.after(0, lambda: btn_guardar.configure(state="normal"))
                    edit_window.after(0, lambda: btn_eliminar.configure(state="normal"))
                    status_label.configure(text="Subida completada")

                threading.Thread(target=subir_archivo, daemon=True).start()

        boton_archivo = ctk.CTkButton(edit_window, text="Seleccionar archivo", command=seleccionar_archivo)
        boton_archivo.grid(row=len(self.columns), column=1, padx=10, pady=5, sticky="w")

    def show_tooltip(self, event):
            """Muestra tooltip si el ratón está sobre 'Descripción' y el texto es más largo que el ancho visible."""
            region = self.tree.identify("region", event.x, event.y)
            if region != "cell":
                self.tooltip.place_forget()
                return

            column = self.tree.identify_column(event.x)
            col_index = int(column.replace("#", "")) - 1

            # Solo mostrar para columna Descripción
            if self.columns[col_index] != "Descripción":
                self.tooltip.place_forget()
                return

            row_id = self.tree.identify_row(event.y)
            if not row_id:
                self.tooltip.place_forget()
                return

            text = self.tree.item(row_id, "values")[col_index]
            col_width = self.tree.column(self.columns[col_index], width=None)

            # Calcular si el texto excede el ancho visible
            if len(text) * 7 > col_width:  # 7 px aprox por caracter
                self.tooltip.config(text=text)
                self.tooltip.place(x=event.x_root - self.tree.winfo_rootx() + 10,
                                y=event.y_root - self.tree.winfo_rooty() + 20)
            else:
                self.tooltip.place_forget()
