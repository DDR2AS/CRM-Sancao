import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from services.google_storage import gcpService
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import webbrowser
from tkcalendar import DateEntry
import threading
import shutil
import os

load_dotenv() 


class SalesFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master, fg_color="white")
        self.process = process

        # ===================== DATOS ===================== #
        try:
            self.datos = pd.DataFrame(self.process.getSales())
        except Exception as e:
            print(f"Error cargando datos de ventas: {e}")
            self.columns = ["COD", "Fecha Venta", "Producto", "Peso (kg)", "Precio x Kg", "Monto (S/)", "Url"]
            self.datos = pd.DataFrame(columns=self.columns)

        # ===================== HEADER ===================== #
        header_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x")

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=15)

        # Título
        ctk.CTkLabel(
            header_inner,
            text="Venta de Cacao",
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

        # Card de venta total
        frame_venta = ctk.CTkFrame(totales_frame, fg_color="#28a745", corner_radius=10)
        frame_venta.pack(side="left")

        venta_inner = ctk.CTkFrame(frame_venta, fg_color="transparent")
        venta_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(venta_inner, text="TOTAL VENTAS", font=("Segoe UI", 11), text_color="#C8F5D0").pack(anchor="w")
        self.label_total = ctk.CTkLabel(venta_inner, text="S/ 0.0", font=("Segoe UI", 22, "bold"), text_color="white")
        self.label_total.pack(anchor="w")

        # Card de peso total
        frame_peso = ctk.CTkFrame(totales_frame, fg_color="#6C757D", corner_radius=10)
        frame_peso.pack(side="left", padx=(15, 0))

        peso_inner = ctk.CTkFrame(frame_peso, fg_color="transparent")
        peso_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(peso_inner, text="PESO TOTAL", font=("Segoe UI", 11), text_color="#E9ECEF").pack(anchor="w")
        self.label_peso = ctk.CTkLabel(peso_inner, text="0 kg", font=("Segoe UI", 22, "bold"), text_color="white")
        self.label_peso.pack(anchor="w")

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

        # Scrollbar vertical
        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

        self.columns = ["COD", "Fecha Venta", "Producto", "Peso (kg)", "Precio x Kg", "Monto (S/)", "Url"]
        self.widths = [90, 120, 130, 100, 110, 120, 250]

        self.tree = ttk.Treeview(
            tabla_frame,
            columns=self.columns,
            show="headings",
            height=10,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", width=self.widths[i])

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

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)
        datos = datos.sort_values(by="Fecha Venta", ascending=True)
        total = 0.0
        total_peso = 0.0
        row_count = 0

        for _, row in datos.iterrows():
            try:
                fecha = row.get("Fecha Venta", "")
                if isinstance(fecha, str):
                    fecha = datetime.strptime(fecha, "%Y-%m-%d")
                fecha_str = fecha.strftime("%Y-%m-%d")
                amount = float(row.get("Monto", 0))
                peso = float(row.get("Peso", 0)) if pd.notna(row.get("Peso")) else 0
                total += amount
                total_peso += peso

                # Alternar colores de fila
                tag = "evenrow" if row_count % 2 == 0 else "oddrow"
                url = row.get("Url", "")
                url_str = url if pd.notna(url) else ""

                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    row.get("Producto", ""),
                    f"{peso:.1f}" if peso else "",
                    row.get("PrecioxKg", ""),
                    f"{amount:.2f}",
                    url_str
                ), tags=(tag,))
                row_count += 1

            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.label_total.configure(text=f"S/ {total:,.2f}")
        self.label_peso.configure(text=f"{total_peso:,.1f} kg")

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
        edit_window.title("Editar Venta")
        self.archivo_subido = None

        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 420, 430
        x = (edit_window.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_window.winfo_screenheight() // 2) - (height // 2)
        edit_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header con color ---
        header_bg = ctk.CTkFrame(edit_window, fg_color="#28a745", corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Editar Venta",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text=f"Código: {values[0]}",
            font=("Segoe UI", 12),
            text_color="#D4EDDA"
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

            if col == "Producto":
                combo = ctk.CTkComboBox(
                    form_frame,
                    values=["Cacao en baba", "Cacao seco", "Otro"],
                    width=240,
                    font=("Segoe UI", 14),
                    text_color="#111111"
                )
                combo.set(values[i])
                combo.grid(row=row_idx, column=1, pady=5, sticky="w")
                entries[col] = combo
            elif col == "Url":
                entry = ctk.CTkEntry(form_frame, width=240, font=("Segoe UI", 14), text_color="#111111")
                entry.insert(0, values[i] if values[i] else "")
                entry.grid(row=row_idx, column=1, pady=5, sticky="w")
                entries[col] = entry
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
        current_url = values[6] if len(values) > 6 else ""

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
                else:
                    new_values.append(None)
            values_dict = dict(zip(self.columns, new_values))
            print(values_dict)
            self.process.updateSale(
                v_code=new_values[0],
                data=values_dict
            )
            self.tree.item(item_id, values=new_values)
            self.archivo_subido = {}
            self.recargar_tabla()
            edit_window.destroy()

        def delete_sale():
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta venta?"):
                if self.process.deleteSale(values[0]):
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

                        # Get sale code
                        v_code = values[0]

                        # Check if sale already has an attachment
                        sale = self.process.mongo_service.get_sale_by_code(v_code)
                        existing_attachment_id = sale.get("attachmentId") if sale else None

                        attachment_data = {
                            "url": resultado.get("url"),
                            "fileGsUrl": resultado.get("fileGsUrl"),
                            "mimeType": resultado.get("mimeType"),
                            "fileSize": resultado.get("fileSize"),
                            "recordType": "sale",
                            "recordCode": v_code
                        }

                        if existing_attachment_id:
                            # Update existing attachment
                            self.process.mongo_service.update_attachment(existing_attachment_id, attachment_data)
                            attachment_id = existing_attachment_id
                        else:
                            # Create new attachment
                            attachment_id = self.process.mongo_service.create_attachment(attachment_data)
                            # Update sale with attachmentId
                            self.process.mongo_service.update_sale_attachment(v_code, attachment_id)

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
        btn_eliminar.configure(command=delete_sale)
        boton_archivo.configure(command=seleccionar_archivo)

    def recalcular_total(self):
        total = 0.0
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            try:
                amount = float(values[5])
                total += amount
            except:
                pass
        self.label_total.configure(text=f"Total Ventas: S/ {total:,.1f}")

    def recargar_tabla(self):
        try:
            self.datos = pd.DataFrame(self.process.getSales())
            self.filterTableByDates()
        except Exception as e:
            print(f"Error al recargar tabla de ventas: {e}")
            self.columns = ["COD", "Fecha Venta", "Producto", "Peso (kg)", "Precio x Kg", "Monto (S/)", "Url"]
            self.datos = pd.DataFrame(columns=self.columns)
            self.filterTableByDates()

    def filterTableByDates(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas inválidas:", e)
            return

        df = self.datos.copy()
        df["Fecha Venta"] = pd.to_datetime(df["Fecha Venta"], errors="coerce")

        self.datos_filtrados = df[
            (df["Fecha Venta"] >= fecha_ini) & (df["Fecha Venta"] <= fecha_fin)
        ]
        self.cargar_datos(self.datos_filtrados)