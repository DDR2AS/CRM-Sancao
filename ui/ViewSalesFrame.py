import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
import webbrowser
from tkcalendar import DateEntry
import shutil 


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

        # ===================== TITULO Y FILTROS ===================== #
        titulo_filtro_frame = ctk.CTkFrame(self, fg_color="transparent")
        titulo_filtro_frame.pack(fill="x", padx=20, pady=(10, 0))

        titulo_label = ctk.CTkLabel(
            titulo_filtro_frame,
            text="Venta de Cacao",
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

        # ===================== TOTALES ===================== #
        frame_totales = ctk.CTkFrame(self, fg_color="#f0f0f0")
        frame_totales.pack(fill="x", padx=20, pady=(10, 0))

        self.label_total = ctk.CTkLabel(
            frame_totales,
            text="Total Ventas: S/ 0.0",
            font=("Arial", 18, "bold"),
            text_color="#333333"
        )
        self.label_total.pack(side="left", padx=15, pady=10)

        # ===================== TABLA ===================== #
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

        tabla_frame = tk.Frame(self)
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

        self.columns = ["COD", "Fecha Venta","Producto", "Peso (kg)", "Precio x Kg", "Monto (S/)", "Url"]
        self.widths = [120, 160, 100, 120, 120, 120, 280]

        self.tree = ttk.Treeview(tabla_frame, columns=self.columns, show="headings", height=15,
                                 yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", width=self.widths[i])

        self.tree.pack(side="left", fill="both", expand=True)
        # Asociar scrollbars
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        tabla_frame.grid_rowconfigure(0, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click)

        self.cargar_datos(self.datos)

    def cargar_datos(self, datos):
        for item in self.tree.get_children():
            self.tree.delete(item)
        datos = datos.sort_values(by="Fecha Venta", ascending=True)
        total = 0.0
        for _, row in datos.iterrows():
            try:
                fecha = row.get("Fecha Venta", "")
                if isinstance(fecha, str):
                    fecha = datetime.strptime(fecha, "%Y-%m-%d")
                fecha_str = fecha.strftime("%Y-%m-%d")
                amount = float(row.get("Monto", 0))
                total += amount

                self.tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    row.get("Producto", ""),
                    row.get("Peso", ""),
                    row.get("PrecioxKg", ""),
                    amount,
                    row.get("fileDriveUrl", "")
                ))

            except Exception as e:
                print(f"Error al cargar fila: {row} → {e}")

        self.label_total.configure(text=f"Total Ventas: S/ {total:,.1f}")

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
        edit_window.geometry("400x330")
        
        # --- Centrar ventana ---
        edit_window.update_idletasks()
        width, height = 400, 330
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

        button_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        button_frame.grid(row=len(self.columns), column=0, columnspan=2, pady=20)

        def save_changes():
            new_values = [entries[col].get() for col in self.columns]
            print(new_values)
            # Guardar en BD
            self.process.updateSale(
                v_code=new_values[0],
                data=dict(zip(self.columns, new_values))
            )
            self.tree.item(item_id, values=new_values)
            self.recalcular_total()
            edit_window.destroy()

        def delete_sale():
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta venta?"):
                if self.process.deleteSale(values[0]):
                    self.tree.delete(item_id)
                self.recalcular_total()
                edit_window.destroy()

        ctk.CTkButton(button_frame, text="Guardar", command=save_changes, fg_color="#4CAF50").pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Eliminar", command=delete_sale, fg_color="#E53935").pack(side="left", padx=10)

    def recalcular_total(self):
        total = 0.0
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            try:
                amount = float(values[4]) 
                total += amount
            except:
                pass
        self.label_total.configure(text=f"Total Ventas: S/ {total:,.2f}")

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