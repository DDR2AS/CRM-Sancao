from datetime import datetime
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import webbrowser
import pandas as pd

class GastosFrame(ctk.CTkFrame):
    def __init__(self, master, process):
        super().__init__(master)
        self.process = process
        
        try:
            self.datos = self.process.getGastos()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.datos = pd.DataFrame()

        # Iniciar actualización automática cada 2 minutos (120,000 ms)
        self.after(60000, self.update_cronjob)

        titulo_label = ctk.CTkLabel(
            self,
            text="Lista de Gastos",
            font=("Arial", 22, "bold"),
            anchor="w",       # alinea el texto a la izquierda
            justify="left"    # justificación del texto
        )
        titulo_label.pack(fill="x", padx=20, pady=(5, 0))

        # Selector de mes
        self.meses = self.obtener_meses_disponibles()
        self.mes_seleccionado = ctk.StringVar(value="Todos")

        filtro_frame = ctk.CTkFrame(self)
        filtro_frame.pack(pady=(15, 0))

        ctk.CTkLabel(filtro_frame, text="Filtrar por mes:").pack(side="left", padx=(0, 10))

        self.selector_mes = ctk.CTkOptionMenu(
            filtro_frame,
            values=["Todos"] + self.meses,
            variable=self.mes_seleccionado,
            command=self.filtrar_por_mes
        )
        self.selector_mes.pack(side="left")

        # Total
        frame_totales = ctk.CTkFrame(self, fg_color="#d9d9d9")
        frame_totales.pack(anchor="w", padx=20, pady=20)

        # Sub-frame para gasto
        frame_gasto = ctk.CTkFrame(frame_totales, fg_color="#ff4d4f", corner_radius=10)
        frame_gasto.pack(side="left", padx=(0, 15), ipadx=15, ipady=10)
        
        self.label_gasto = ctk.CTkLabel(frame_gasto, text="Gasto Total: S/ 0.0", font=("Segoe UI", 15, "bold"), text_color="white")
        self.label_gasto.pack()

        #self.total_label = ctk.CTkLabel(self, text="Gasto Total: S/ 0.00", font=("Arial", 24, "bold"))
        #self.total_label.pack(pady=10)

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
        self.tree.bind("<Double-1>", self.on_edit)

        # Tooltip para descripción
        self.tooltip = tk.Label(self.tree, text="", bg="yellow", wraplength=300, relief="solid", borderwidth=1)
        self.tooltip.place_forget()

        self.tree.bind("<Motion>", self.show_tooltip)
        self.tree.bind("<Leave>", lambda e: self.tooltip.place_forget())
        
        # To delete
        self.boton_mostrar_ancho = ctk.CTkButton(self, text="Mostrar ancho columnas", command=self.mostrar_ancho_columnas)
        self.boton_mostrar_ancho.pack(pady=(0, 15))
        self.cargar_datos(self.datos)

    # ========= FUNCIONES ========= #
    def recargar_tabla(self):
        try:
            self.datos = self.process.getGastos()
        except Exception as e:
            print("Error al obtener datos desde process.getGastos():", e)
            self.datos = pd.DataFrame()

    def update_cronjob(self):
        """Recarga los datos y vuelve a ejecutar en 2 minutos."""
        print(f"[{datetime.now()}] Recargando datos...")
        self.recargar_tabla()
        self.filtrar_por_mes(self.mes_seleccionado.get())
        self.after(120000, self.update_cronjob)  # 2 minutos

    def mostrar_ancho_columnas(self):
        print("Anchura actual de columnas:")
        for col in self.columns:
            ancho = self.tree.column(col)["width"]
            print(f" - {col}: {ancho} px")

    def obtener_meses_disponibles(self):
        meses = set()
        for _, row in self.datos.iterrows():
            try:
                fecha = datetime.strptime(row["Fecha"], "%Y-%m-%d")
                meses.add(fecha.strftime("%Y-%m"))
            except Exception as e:
                print(f"Fecha inválida: {row['Fecha']} → {e}")
        return sorted(list(meses), reverse=True)

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

    def filtrar_por_mes(self, mes):
        if mes == "Todos":
            filtrado = self.datos
        else:
            filtrado = self.datos[
                self.datos["Fecha"].str.startswith(mes)
            ]
        self.cargar_datos(filtrado)
    
    def on_edit(self, event):
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
            if url.strip():
                webbrowser.open(url)
            return

        # Si no es URL → abrir ventana de edición
        edit_window = tk.Toplevel(self)
        edit_window.title("Editar gasto")

        entries = []
        for i, col in enumerate(self.columns):
            tk.Label(edit_window, text=col).grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(edit_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, values[i])
            entries.append(entry)

        def save_changes():
            new_values = [e.get() for e in entries]

            # Aquí llamas a tu función para guardar en la BD
            # self.process.update_gasto(cod=new_values[0], data=dict(zip(self.columns, new_values)))

            self.tree.item(row_id, values=new_values)
            edit_window.destroy()

        tk.Button(edit_window, text="Guardar", command=save_changes).grid(
            row=len(self.columns), column=0, columnspan=2, pady=10
        )

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
