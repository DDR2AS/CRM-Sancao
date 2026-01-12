from tkinter import filedialog, messagebox, ttk
from services.google_storage import gcpService
from dotenv import load_dotenv
from datetime import datetime
from tkcalendar import DateEntry
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import webbrowser
import pandas as pd
import threading
import shutil
import os

load_dotenv()

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

        # ===================== HEADER ===================== #
        header_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=15)

        # Título
        ctk.CTkLabel(
            header_inner,
            text="Registro de Gastos",
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

        # Card de gasto total
        frame_gasto = ctk.CTkFrame(totales_frame, fg_color="#DC3545", corner_radius=10)
        frame_gasto.pack(side="left")

        gasto_inner = ctk.CTkFrame(frame_gasto, fg_color="transparent")
        gasto_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(gasto_inner, text="GASTO TOTAL", font=("Segoe UI", 11), text_color="#FFD6D9").pack(anchor="w")
        self.label_gasto = ctk.CTkLabel(gasto_inner, text="S/ 0.0", font=("Segoe UI", 22, "bold"), text_color="white")
        self.label_gasto.pack(anchor="w")

        # ===================== TABLA ===================== #
        # Estilos de la tabla
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
        # Grid lines
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Treeview",
                        bordercolor="#DDDDDD",
                        lightcolor="#DDDDDD",
                        darkcolor="#DDDDDD")

        # Frame contenedor para tabla y scrollbar
        tabla_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        tabla_container.pack(fill="both", expand=True, padx=25, pady=(5, 15))

        tabla_frame = tk.Frame(tabla_container, bg="#FFFFFF")
        tabla_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")

        # Scrollbar horizontal
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

        # Tabla
        self.columns = ("COD", "Fecha", "Tipo", "Producto", "Cantidad", "Monto Total", "Descripción", "Url")
        self.widths = [75, 100, 70, 150, 80, 110, 280, 180]

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
                self.tree.column(col, anchor=tk.W, width=self.widths[i])
            else:
                self.tree.column(col, anchor=tk.CENTER, width=self.widths[i])

        # Tags para filas alternadas (grid visual)
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
        self.filterTableByDates()

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
            self.filterTableByDates()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.columns = ("COD","Fecha", "Tipo", "Producto", "Cantidad", "Monto Total", "Descripción", "Url")
            self.datos = pd.DataFrame(columns=self.columns)
            self.filterTableByDates()

    def update_cronjob(self):
        print(f"[{datetime.now()}] Recargando datos...")
        self.recargar_tabla()
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
        row_count = 0
        for _, row in datos.iterrows():
            try:
                cantidad = row.get("Cantidad", 0)
                monto = float(row.get("Monto Total", 0))
                fecha = row.get("Fecha", "")
                if pd.notna(fecha):
                    fecha = pd.to_datetime(fecha).strftime("%Y-%m-%d")

                # Alternar colores de fila
                tag = "evenrow" if row_count % 2 == 0 else "oddrow"
                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha,
                    row.get("Tipo", ""),
                    row.get("Producto", ""),
                    cantidad,
                    monto,
                    row.get("Descripcion", ""),
                    row.get("Url", "")
                ), tags=(tag,))
                total += monto
                row_count += 1
            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.label_gasto.configure(text=f"S/ {total:,.2f}")
    
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
        self.archivo_subido = None

        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 420, 530
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header con color ---
        header_bg = ctk.CTkFrame(edit_window, fg_color="#2C3E50", corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Editar Gasto",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text=f"Código: {values[0]}",
            font=("Segoe UI", 12),
            text_color="#BDC3C7"
        ).pack(anchor="w")

        # --- Main container ---
        main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # --- Form frame ---
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)

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
            label.grid(row=row_idx, column=0, padx=(0, 12), pady=5, sticky="w")

            if col == 'Descripción':
                text_widget = ctk.CTkTextbox(form_frame, width=240, height=60, font=("Segoe UI", 14), text_color="#111111")
                text_widget.grid(row=row_idx, column=1, pady=5, sticky="w")
                text_widget.insert("1.0", values[i])
                entries[col] = text_widget
            elif col == "Producto":
                combo = ctk.CTkComboBox(
                    form_frame,
                    values=[
                        "Abono", "Aceite Quemado", "Aceite para Lubricar",
                        "Gasolina", "Latiguillos", "Urea",
                        "Manta para secado", "Baldes de plástico",
                        "Sacos", "Herramientas", "Víveres", "Otro"
                    ],
                    width=240,
                    font=("Segoe UI", 14),
                    text_color="#111111"
                )
                combo.set(values[i])
                combo.grid(row=row_idx, column=1, pady=5, sticky="w")
                entries[col] = combo
            else:
                entry = ctk.CTkEntry(form_frame, width=240, font=("Segoe UI", 14), text_color="#111111")
                entry.insert(0, values[i])
                entry.grid(row=row_idx, column=1, pady=5, sticky="w")
                entries[col] = entry

            row_idx += 1

        # --- File upload section ---
        file_frame = ctk.CTkFrame(main_frame, fg_color="#EBEBEB", corner_radius=8)
        file_frame.pack(fill="x", pady=(1, 3))

        file_inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_inner.pack(padx=12, pady=6)

        file_path_var = tk.StringVar()
        status_label = ctk.CTkLabel(file_inner, text="Comprobante", font=("Segoe UI", 13, "bold"), text_color="#333333")
        status_label.pack(side="left", padx=(0, 10))

        boton_archivo = ctk.CTkButton(
            file_inner,
            text="Subir",
            width=80,
            height=30,
            font=("Segoe UI", 13),
            fg_color="#3EA5FF",
            hover_color="#2196F3"
        )
        boton_archivo.pack(side="left", padx=(0, 8))

        # Get current URL from values
        current_url = values[7] if len(values) > 7 else ""

        def abrir_preview():
            url = entries["Url"].get().strip() if "Url" in entries else current_url
            if url and url.startswith("http"):
                webbrowser.open(url)
            else:
                messagebox.showinfo("Sin comprobante", "No hay comprobante adjunto")

        btn_preview = ctk.CTkButton(
            file_inner,
            text="Ver",
            width=60,
            height=30,
            font=("Segoe UI", 13),
            fg_color="#6C757D",
            hover_color="#5A6268"
        )
        btn_preview.pack(side="left")
        btn_preview.configure(command=abrir_preview)

        # --- Button frame ---
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(8, 0))

        btn_eliminar = ctk.CTkButton(
            button_frame,
            text="Eliminar",
            fg_color="#E53935",
            hover_color="#C62828",
            width=110,
            height=36,
            font=("Segoe UI", 14, "bold")
        )
        btn_eliminar.pack(side="left")

        btn_guardar = ctk.CTkButton(
            button_frame,
            text="Guardar cambios",
            fg_color="#4CAF50",
            hover_color="#388E3C",
            width=130,
            height=36,
            font=("Segoe UI", 14, "bold")
        )
        btn_guardar.pack(side="right")

        def save_changes():
            new_values = []
            for col in self.columns:
                widget = entries[col]
                if isinstance(widget, ctk.CTkEntry):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkComboBox):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkTextbox):
                    new_values.append(widget.get("0.0", "end").strip())
                else:
                    new_values.append(None)
            values_dict = dict(zip(self.columns, new_values))
            # Remove Url from update (deprecated fileDriveUrl)
            values_dict.pop("Url", None)
            print(values_dict)
            self.process.updateExpenses(
                e_code=new_values[0],
                data=values_dict
            )
            self.tree.item(item_id, values=new_values)
            self.archivo_subido = {}
            self.recargar_tabla()
            edit_window.destroy()

        def delete_expense():
            if tk.messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar este gasto?"):
                if self.process.deleteExpense(values[0]):
                    self.tree.delete(item_id)
                self.recargar_tabla()
                edit_window.destroy()

        def seleccionar_archivo():
            self.archivo_subido = {}
            archivo = filedialog.askopenfilename(
                parent=edit_window,
                filetypes=[
                    ("Imagenes", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
                    ("PDF", "*.pdf"),
                    ("Todos los archivos", "*.*")
                ]
            )
            if archivo:
                file_path_var.set(archivo)
                btn_guardar.configure(state="disabled")
                btn_eliminar.configure(state="disabled")
                status_label.configure(text="Subiendo a GCS...")

                def subir_archivo():
                    try:
                        # Initialize GCS service
                        gcs = gcpService(credentials_path=os.getenv("GCS_CREDENTIALS_PATH"))
                        bucket_name = os.getenv("GCS_BUCKET_NAME")

                        # Upload to GCS
                        resultado = gcs.upload_file(
                            bucket_name=bucket_name,
                            local_path=archivo,
                            folder_prefix="images-vouchers"
                        )

                        # Get expense code
                        e_code = values[0]

                        # Check if expense already has an attachment
                        expense = self.process.mongo_service.get_expense_by_code(e_code)
                        existing_attachment_id = expense.get("attachmentId") if expense else None

                        attachment_data = {
                            "url": resultado.get("url"),
                            "fileGsUrl": resultado.get("fileGsUrl"),
                            "mimeType": resultado.get("mimeType"),
                            "fileSize": resultado.get("fileSize"),
                            "recordType": "expense",
                            "recordCode": e_code
                        }

                        if existing_attachment_id:
                            # Update existing attachment
                            self.process.mongo_service.update_attachment(existing_attachment_id, attachment_data)
                            attachment_id = existing_attachment_id
                        else:
                            # Create new attachment
                            attachment_id = self.process.mongo_service.create_attachment(attachment_data)
                            # Update expense with attachmentId
                            self.process.mongo_service.update_expense_attachment(e_code, attachment_id)

                        self.archivo_subido = {
                            "attachmentId": str(attachment_id),
                            "url": resultado.get("url")
                        }

                        # Update UI
                        edit_window.after(0, lambda: entries["Url"].delete(0, "end"))
                        edit_window.after(0, lambda: entries["Url"].insert(0, resultado.get("url", "")))
                        edit_window.after(0, lambda: entries["Url"].icursor("end"))
                        edit_window.after(0, lambda: btn_guardar.configure(state="normal"))
                        edit_window.after(0, lambda: btn_eliminar.configure(state="normal"))
                        edit_window.after(0, lambda: status_label.configure(text="Subida completada"))

                    except Exception as e:
                        print(f"Error uploading file: {e}")
                        edit_window.after(0, lambda: btn_guardar.configure(state="normal"))
                        edit_window.after(0, lambda: btn_eliminar.configure(state="normal"))
                        edit_window.after(0, lambda: status_label.configure(text=f"Error: {str(e)[:30]}"))

                threading.Thread(target=subir_archivo, daemon=True).start()

        btn_guardar.configure(command=save_changes)
        btn_eliminar.configure(command=delete_expense)
        boton_archivo.configure(command=seleccionar_archivo)

    def show_tooltip(self, event):
            """Muestra tooltip si el ratón está sobre 'Descripción' y el texto es más largo que el ancho visible o tiene múltiples líneas."""
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

            # Show tooltip if text exceeds width OR contains newlines
            has_multiline = "\n" in str(text)
            exceeds_width = len(str(text)) * 7 > col_width

            if has_multiline or exceeds_width:
                self.tooltip.config(text=text)
                self.tooltip.place(x=event.x_root - self.tree.winfo_rootx() + 10,
                                y=event.y_root - self.tree.winfo_rooty() + 20)
            else:
                self.tooltip.place_forget()
