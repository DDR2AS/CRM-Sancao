from datetime import datetime, timedelta, timezone
from tkinter import filedialog, messagebox, ttk
from services.google_storage import gcpService
from tkcalendar import DateEntry
from dotenv import load_dotenv
import customtkinter as ctk
import tkinter as tk
import pandas as pd
import webbrowser
import threading
import shutil
import base64
import os

load_dotenv()

class EnviosFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master, fg_color="white")
        self.process = process
        # Iniciar actualización automática cada 2 minutos (120,000 ms)
        self.after(60000, self.update_cronjob)

        # ===================== TITULO Y FILTROS ===================== #
        titulo_filtro_frame = ctk.CTkFrame(self, fg_color="transparent")
        titulo_filtro_frame.pack(fill="x", padx=20, pady=(10, 0))

        titulo_label = ctk.CTkLabel(
            titulo_filtro_frame,
            text="Gestión de Envíos",
            font=("Arial", 22, "bold"),
            anchor="w",
            justify="left"
        )
        titulo_label.pack(side="left", padx=(0, 20))

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
        
        # ===================== TOTALES Y NUEVO ENVÍO ===================== #
        frame_totales = ctk.CTkFrame(self, fg_color="#f0f0f0")
        frame_totales.pack(fill="x", padx=20, pady=(10, 0))

        self.label_total = ctk.CTkLabel(
            frame_totales,
            text="Total Envíos: S/ 0.0",
            font=("Arial", 18, "bold"),
            text_color="#333333"
        )
        self.label_total.pack(side="left", padx=15, pady=10)

        ctk.CTkButton(
            frame_totales, 
            text="Nuevo Envío", 
            command=self.abrir_ventana_envio
        ).pack(side="right", padx=15, pady=10)
        # ===================== FATOS ===================== #
        try:
            self.datos_table = self.process.getEnvios()
        except Exception as e:
            print("Error al obtener datos desde process.getEnvios():", e)
            self.columns = ("COD", "Fecha envío", "Monto (S/)", "Descripción", "Url")
            self.datos_table = pd.DataFrame(self.columns)

        # Estilos
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
        # Tabla
        self.columns = ("COD", "Fecha envío", "Monto (S/)", "Descripción", "Url")
        self.width1 = [64,109,125,315,355]

        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=10)

        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=self.width1[i])

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.cargar_datos(self.datos_table)
    
    # ========= FUNCIONES ========= #
    def update_cronjob(self):
        print(f"[{datetime.now()}] Recargando datos...")
        self.recargar_tabla()
        self.filterTableByDates()
        self.after(120000, self.update_cronjob)  # 2 minutos
    
    def abrir_ventana_envio(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Nuevo Envío")
        self.archivo_nuevo = None

        # Centrar ventana
        ventana.update_idletasks()
        w, h = 450, 500
        x = (ventana.winfo_screenwidth() // 2) - (w // 2)
        y = (ventana.winfo_screenheight() // 2) - (h // 2)
        ventana.geometry(f"{w}x{h}+{x}+{y}")
        ventana.transient(self)
        ventana.grab_set()
        ventana.focus_force()

        # --- Header con color ---
        header_bg = ctk.CTkFrame(ventana, fg_color="#17a2b8", corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Nuevo Envío de Dinero",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text="Registrar transferencia",
            font=("Segoe UI", 12),
            text_color="#D1ECF1"
        ).pack(anchor="w")

        # --- Main container ---
        main_frame = ctk.CTkFrame(ventana, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=15)

        # --- Form frame ---
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)

        # Fecha
        ctk.CTkLabel(form_frame, text="Fecha", font=("Segoe UI", 14, "bold"), text_color="#222222").grid(row=0, column=0, padx=(0, 12), pady=8, sticky="w")
        entry_fecha = DateEntry(form_frame, width=18, font=("Segoe UI", 11))
        entry_fecha.grid(row=0, column=1, pady=8, sticky="w")

        # Monto
        ctk.CTkLabel(form_frame, text="Monto (S/.)", font=("Segoe UI", 14, "bold"), text_color="#222222").grid(row=1, column=0, padx=(0, 12), pady=8, sticky="w")
        entry_monto = ctk.CTkEntry(form_frame, width=200, height=36, font=("Segoe UI", 14), placeholder_text="Ej: 500.00")
        entry_monto.grid(row=1, column=1, pady=8, sticky="w")

        # Descripción
        ctk.CTkLabel(form_frame, text="Descripción", font=("Segoe UI", 14, "bold"), text_color="#222222").grid(row=2, column=0, padx=(0, 12), pady=8, sticky="nw")
        textbox_descripcion = ctk.CTkTextbox(form_frame, width=250, height=100, font=("Segoe UI", 13))
        textbox_descripcion.grid(row=2, column=1, pady=8, sticky="w")

        # --- File upload section ---
        file_frame = ctk.CTkFrame(main_frame, fg_color="#EBEBEB", corner_radius=8)
        file_frame.pack(fill="x", pady=(10, 5))

        file_inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_inner.pack(padx=12, pady=10)

        file_path_var = tk.StringVar()
        status_label = ctk.CTkLabel(file_inner, text="Comprobante (opcional)", font=("Segoe UI", 13, "bold"), text_color="#333333")
        status_label.pack(side="left", padx=(0, 10))

        boton_archivo = ctk.CTkButton(
            file_inner,
            text="Seleccionar",
            width=100,
            height=32,
            font=("Segoe UI", 13),
            fg_color="#3EA5FF",
            hover_color="#2196F3"
        )
        boton_archivo.pack(side="left", padx=(0, 8))

        file_name_label = ctk.CTkLabel(file_inner, text="", font=("Segoe UI", 11), text_color="#666666")
        file_name_label.pack(side="left")

        def seleccionar_archivo():
            archivo = filedialog.askopenfilename(
                parent=ventana,
                filetypes=[
                    ("Imagenes", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
                    ("PDF", "*.pdf"),
                    ("Todos los archivos", "*.*")
                ]
            )
            if archivo:
                file_path_var.set(archivo)
                file_name_label.configure(text=os.path.basename(archivo)[:25] + "..." if len(os.path.basename(archivo)) > 25 else os.path.basename(archivo))

        boton_archivo.configure(command=seleccionar_archivo)

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
            command=ventana.destroy
        )
        btn_cancelar.pack(side="left")

        btn_guardar = ctk.CTkButton(
            button_frame,
            text="Guardar Envío",
            fg_color="#28a745",
            hover_color="#1e7e34",
            width=140,
            height=38,
            font=("Segoe UI", 14, "bold")
        )
        btn_guardar.pack(side="right")

        def guardar():
            try:
                sentAt = entry_fecha.get_date()
                tz = timezone(timedelta(hours=-5))
                sentAt_with_time = datetime.combine(sentAt, datetime.now().time()).replace(tzinfo=tz)
                created_at = datetime.now(tz=tz).isoformat(timespec="milliseconds")

                monto_str = entry_monto.get().strip()
                if not monto_str:
                    raise ValueError("El monto es requerido.")
                monto = float(monto_str)

                descripcion = textbox_descripcion.get("1.0", "end").strip()
                if not descripcion:
                    raise ValueError("La descripción no puede estar vacía.")

                # Disable buttons while saving
                btn_guardar.configure(state="disabled")
                btn_cancelar.configure(state="disabled")
                status_label.configure(text="Guardando...")

                def proceso_guardado():
                    try:
                        archivo_info = None
                        attachment_url = ""
                        ruta_archivo = file_path_var.get()

                        # Upload to GCS if file selected
                        if ruta_archivo:
                            try:
                                gcs = gcpService(credentials_path=os.getenv("GCS_CREDENTIALS_PATH"))
                                bucket_name = os.getenv("GCS_BUCKET_NAME")
                                resultado = gcs.upload_file(
                                    bucket_name=bucket_name,
                                    local_path=ruta_archivo,
                                    folder_prefix="images-vouchers"
                                )
                                attachment_url = resultado.get("url", "")

                                # Store attachment data for later linking
                                self.archivo_nuevo = {
                                    "url": resultado.get("url"),
                                    "fileGsUrl": resultado.get("fileGsUrl"),
                                    "mimeType": resultado.get("mimeType"),
                                    "fileSize": resultado.get("fileSize"),
                                    "recordType": "envio"
                                }
                            except Exception as e:
                                print(f"Error uploading to GCS: {e}")

                        data = {
                            "type": "Efectivo",
                            "amount": monto,
                            "description": descripcion,
                            "sentAt": sentAt_with_time.strftime("%Y-%m-%d"),
                            "createdBy": "Draft",
                            "month": datetime.now().strftime("%Y%m"),
                            "createdAt": created_at,
                            "fileDriveUrl": attachment_url
                        }

                        self.process.postSentMoney(data, archivo_info)

                        ventana.after(0, lambda: ventana.attributes("-topmost", False))
                        ventana.after(0, lambda: messagebox.showinfo("Éxito", "Envío guardado correctamente", parent=ventana))
                        ventana.after(0, ventana.destroy)
                        ventana.after(0, self.recargar_tabla)

                    except Exception as e:
                        ventana.after(0, lambda: btn_guardar.configure(state="normal"))
                        ventana.after(0, lambda: btn_cancelar.configure(state="normal"))
                        ventana.after(0, lambda: status_label.configure(text=f"Error: {str(e)[:30]}"))
                        print(f"Error guardando envío: {e}")

                threading.Thread(target=proceso_guardado, daemon=True).start()

            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}", parent=ventana)

        btn_guardar.configure(command=guardar)

    # ========= FUNCIONES ========= #
    def mostrar_ancho_columnas(self):
        print("Anchura actual de columnas:")
        for col in self.tree:
            ancho = self.tree.column(col)["width"]
            print(f" - {col}: {ancho} px")

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)
        datos = datos.sort_values(by="Fecha", ascending=True)

        if datos.empty:
            return
        total = 0.0
        for _, row in datos.iterrows():
            try:
                fecha = row.get("Fecha")
                if isinstance(fecha, str):
                    fecha = datetime.strptime(fecha, "%Y-%m-%d")
                fecha_str = fecha.strftime("%Y-%m-%d")

                # Filtrando valores nan
                url = row['Url'] if pd.notna(row.get('Url')) else ""
                amount = float(row.get("Monto Total", 0))
                total += amount
                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    f"{row.get('Monto Total', 0):.1f}",
                    row.get("Descripcion", ""),
                    url
                ))
            except Exception as e:
                print("Error cargando fila:", e)
        self.label_total.configure(text=f"Total Envíos: S/ {total:,.1f}")
            
    def recargar_tabla(self):
        try:
            nuevos_datos = self.process.getEnvios()
            self.cargar_datos(nuevos_datos)
        except Exception as e:
            print("Error al recargar la tabla:", e)
            self.columns = ("COD", "Fecha envío", "Monto (S/)", "Descripción", "Url")
            self.datos_table = pd.DataFrame(self.columns)
            self.cargar_datos(nuevos_datos)
    
    def open_url_chrome(self, event):
        # Detectar la fila y columna clicada
        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)  # "#1", "#2", ...

        # Verificar que sea la columna URL (en tu caso es la quinta => "#5")
        if item_id and col == "#5":
            valores = self.tree.item(item_id, "values")
            url = valores[4]  # Índice 4 porque es la quinta columna
            if url.startswith("http"):
                chrome_path = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chrome.exe")
                if chrome_path:
                    webbrowser.get(f'"{chrome_path}" %s').open(url)
                else:
                    webbrowser.open(url)

    def filterTableByDates(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas inválidas:", e)
            return

        df = self.datos_table.copy()
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

        self.datos_filtrados = df[
            (df["Fecha"] >= fecha_ini) & (df["Fecha"] <= fecha_fin)
        ]
        self.cargar_datos(self.datos_filtrados)

    def on_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return

        col = self.tree.identify_column(event.x)
        col_index = int(col.replace("#", "")) - 1
        values = self.tree.item(item_id, "values")

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
        edit_window.title("Editar Envío")
        self.archivo_subido = None

        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 420, 450
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header con color ---
        header_bg = ctk.CTkFrame(edit_window, fg_color="#17a2b8", corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Editar Envío",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text=f"Código: {values[0]}",
            font=("Segoe UI", 12),
            text_color="#D1ECF1"
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
            label.grid(row=row_idx, column=0, padx=(0, 12), pady=6, sticky="w")

            if col == "Descripción":
                text_widget = ctk.CTkTextbox(form_frame, width=240, height=60, font=("Segoe UI", 13))
                text_widget.grid(row=row_idx, column=1, pady=6, sticky="w")
                text_widget.insert("1.0", values[i] if values[i] else "")
                entries[col] = text_widget
            else:
                entry = ctk.CTkEntry(form_frame, width=240, font=("Segoe UI", 14), text_color="#111111")
                entry.insert(0, values[i] if values[i] else "")
                entry.grid(row=row_idx, column=1, pady=6, sticky="w")
                entries[col] = entry

            row_idx += 1

        # --- File upload section ---
        file_frame = ctk.CTkFrame(main_frame, fg_color="#EBEBEB", corner_radius=8)
        file_frame.pack(fill="x", pady=(5, 3))

        file_inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_inner.pack(padx=12, pady=8)

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
        current_url = values[4] if len(values) > 4 else ""

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
            hover_color="#5A6268",
            command=abrir_preview
        )
        btn_preview.pack(side="left")

        # --- Button frame ---
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

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

        # --- Funciones Guardar / Eliminar ---
        def save_changes():
            new_values = []
            for col in self.columns:
                widget = entries[col]
                if isinstance(widget, ctk.CTkEntry):
                    new_values.append(widget.get())
                elif isinstance(widget, ctk.CTkTextbox):
                    new_values.append(widget.get("1.0", "end").strip())
                else:
                    new_values.append(None)

            values_dict = dict(zip(self.columns, new_values))
            # Remove Url from update if using attachments
            if self.archivo_subido:
                values_dict["fileDriveUrl"] = self.archivo_subido.get("url", "")

            self.process.updateSendMoney(
                s_code=new_values[0],
                data=values_dict
            )
            self.tree.item(item_id, values=new_values)
            self.archivo_subido = {}
            self.recargar_tabla()
            edit_window.destroy()

        def delete_sendMoney():
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar este envío?"):
                if self.process.deleteSendMoney(values[0]):
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

                        self.archivo_subido = {
                            "url": resultado.get("url"),
                            "fileGsUrl": resultado.get("fileGsUrl"),
                            "mimeType": resultado.get("mimeType"),
                            "fileSize": resultado.get("fileSize")
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
        btn_eliminar.configure(command=delete_sendMoney)
        boton_archivo.configure(command=seleccionar_archivo)
