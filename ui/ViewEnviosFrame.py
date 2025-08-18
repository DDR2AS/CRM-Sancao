from datetime import datetime, timedelta, timezone
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import customtkinter as ctk
import tkinter as tk
import pandas as pd
import webbrowser
import threading
import shutil 
import base64
import os

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
        ventana.geometry("500x570")

        # Centrar ventana
        ventana.update_idletasks()
        w, h = 500, 570
        x = (ventana.winfo_screenwidth() // 2) - (w // 2)
        y = (ventana.winfo_screenheight() // 2) - (h // 2)
        ventana.geometry(f"{w}x{h}+{x}+{y}")
        ventana.transient(self)     
        ventana.grab_set()       
        ventana.focus_force()

        contenido = ctk.CTkFrame(ventana)
        contenido.pack(expand=True, fill="both", padx=40, pady=20)

        # Fecha
        ctk.CTkLabel(contenido, text="Fecha", font=("Arial", 14)).pack(pady=(10, 5))
        entry_fecha = DateEntry(contenido, width=20)
        entry_fecha.pack(pady=(0, 10))

        # Monto
        ctk.CTkLabel(contenido, text="Monto (*)", font=("Arial", 14)).pack(pady=(10, 5))
        entry_monto = ctk.CTkEntry(contenido, width=250, height=35)
        entry_monto.pack(pady=(0, 10))

        # Descripción
        ctk.CTkLabel(contenido, text="Descripción (*)", font=("Arial", 14)).pack(pady=(10, 5))
        textbox_descripcion = ctk.CTkTextbox(contenido, width=350, height=120)
        textbox_descripcion.pack(pady=(0, 15))

        # Archivo
        ctk.CTkLabel(contenido, text="Archivo (opcional)", font=("Arial", 14)).pack(pady=(5, 5))
        file_path_var = tk.StringVar()

        def seleccionar_archivo():
            archivo = filedialog.askopenfilename(filetypes=[("Todos los archivos", "*.*")])
            if archivo:
                file_path_var.set(archivo)
                boton_archivo.configure(text=os.path.basename(archivo))

        boton_archivo = ctk.CTkButton(contenido, text="Seleccionar archivo", command=seleccionar_archivo)
        boton_archivo.pack(pady=(0, 20))

        def guardar():
            try:
                sentAt = entry_fecha.get_date()
                tz = timezone(timedelta(hours=-5))
                sentAt_with_time = datetime.combine(sentAt, datetime.now().time()).replace(tzinfo=tz)
                created_at = datetime.now(tz=tz).isoformat(timespec="milliseconds")

                monto = float(entry_monto.get())
                descripcion = textbox_descripcion.get("1.0", "end").strip()
                if not descripcion:
                    raise ValueError("La descripción no puede estar vacía.")

                archivo_info = None
                ruta_archivo = file_path_var.get()
                if ruta_archivo:
                    with open(ruta_archivo, "rb") as f:
                        archivo_info = {
                            "nombre": os.path.basename(ruta_archivo),
                            "base64": base64.b64encode(f.read()).decode("utf-8"),
                            "tipo": os.path.splitext(ruta_archivo)[-1]
                        }

                data = {
                    "type" : "Efectivo",
                    "amount": monto,
                    "description": descripcion,
                    "sentAt": sentAt_with_time.strftime("%Y-%m-%d"),
                    "createdBy" : "Draft",
                    "month" : datetime.now().strftime("%Y%m"),
                    "createdAt": created_at,
                }

                self.process.postSentMoney(data, archivo_info)
                ventana.attributes("-topmost", False)
                messagebox.showinfo("Éxito", "Envío guardado correctamente", parent=ventana)
                ventana.destroy()
                self.recargar_tabla()
                if archivo_info:
                    self.master.after(10000, self.recargar_tabla)

            except ValueError as e:
                ventana.attributes("-topmost", False)
                messagebox.showerror("Error", str(e), parent=ventana)
                ventana.attributes("-topmost", True)
            except Exception as e:
                ventana.attributes("-topmost", False)
                messagebox.showerror("Error", f"No se pudo guardar: {e}", parent=ventana)
                ventana.attributes("-topmost", True)

        ctk.CTkButton(contenido, text="Guardar", fg_color="green", hover_color="#006400", command=guardar).pack(pady=(10, 5))

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
        edit_window.title("Editar Venta")
        edit_window.geometry("350x350")
        self.archivo_subido = None
        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 380, 350
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
            # Agregar fileDriveId y fileDriveUrl al diccionario
            if self.archivo_subido:
                values["fileDriveId"] = self.archivo_subido.get("fileDriveId", "")

            self.process.updateSendMoney(
                s_code=new_values[0],
                data=values
            )
            self.tree.item(item_id, values=new_values)
            self.archivo_subido = {"fileDriveId": "", "fileDriveUrl": ""}
            self.recargar_tabla()
            edit_window.destroy()

        def delete_sendMoney():
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta venta?"):
                if self.process.deleteSendMoney(values[0]):
                    self.tree.delete(item_id)
                self.recargar_tabla()
                edit_window.destroy()

        btn_guardar.configure(command=save_changes)
        btn_eliminar.configure(command=delete_sendMoney)

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
