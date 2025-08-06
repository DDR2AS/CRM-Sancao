import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta, timezone
import pandas as pd
import base64
import os

class EnviosFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master)
        self.process = process

        ctk.CTkLabel(self, text="Gestión de Envíos", font=("Arial", 20)).pack(pady=10)
        ctk.CTkButton(self, text="Nuevo Envío", command=self.abrir_ventana_envio).pack(pady=20)

        try:
            self.datos_table = self.process.getEnvios()
        except Exception as e:
            print("Error al obtener datos desde process.getEnvios():", e)
            self.datos_table = pd.DataFrame()

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
        self.columns = ("COD", "Fecha envío", "Monto Total", "Descripción", "Url")
        self.width1 = [64,109,125,335,345]

        self.tree = ttk.Treeview(self, columns=self.columns, show="headings", height=10)

        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=self.width1[i])

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.cargar_datos(self.datos_table)
                # To - Delete
        self.boton_mostrar_ancho = ctk.CTkButton(self, text="Mostrar ancho columnas", command=self.mostrar_ancho_columnas)
        self.boton_mostrar_ancho.pack(pady=(0, 15))

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

        if datos.empty:
            return

        for _, row in datos.iterrows():
            try:
                fecha = row.get("Fecha")
                if isinstance(fecha, str):
                    fecha = datetime.fromisoformat(fecha)
                fecha_str = fecha.strftime("%Y-%m-%d")

                # Filtrando valores nan
                url = row['Url'] if pd.notna(row.get('Url')) else ""

                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    f"{row.get('Monto Total', 0):.2f}",
                    row.get("Descripcion", ""),
                    url
                ))
            except Exception as e:
                print("Error cargando fila:", e)
    
    def recargar_tabla(self):
        try:
            nuevos_datos = self.process.getEnvios()
            self.cargar_datos(nuevos_datos)
        except Exception as e:
            print("Error al recargar la tabla:", e)
