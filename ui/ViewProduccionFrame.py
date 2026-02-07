import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd
import webbrowser
from tkcalendar import DateEntry
import shutil

from services.process import Pipelines

class ProduccionFrame(ctk.CTkFrame):
    def __init__(self, master, process: Pipelines):
        super().__init__(master, fg_color="white")
        self.process = process

        # ===================== DATOS ===================== #
        try:
            self.datos = pd.DataFrame(self.process.getProduccion())
        except Exception as e:
            print(f"Error cargando datos de produccion: {e}")
            self.datos = pd.DataFrame(columns=[
                "COD", "Fecha", "Lugar", "N° Baldes", "Tipo Balde",
                "Peso (kg)", "Estado", "Responsable", "Url"
            ])

        # ===================== HEADER ===================== #
        header_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x")

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Produccion de Cacao",
            font=("Segoe UI", 24, "bold"),
            text_color="#1a1a2e"
        ).pack(side="left")

        # Filtro frame (derecha)
        filtro_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        filtro_frame.pack(side="right")

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

        # ===================== SPLIT PANELS ===================== #
        split_container = ctk.CTkFrame(self, fg_color="transparent")
        split_container.pack(fill="both", expand=True, padx=15, pady=(10, 15))
        split_container.grid_columnconfigure(0, weight=1)
        split_container.grid_columnconfigure(1, weight=1)
        split_container.grid_rowconfigure(0, weight=1)

        # --- San Fernando Panel ---
        self.sf_panel = self._create_place_panel(
            split_container, "San Fernando", "#6F4E37", col=0
        )

        # --- Las Palmas Panel ---
        self.lp_panel = self._create_place_panel(
            split_container, "Las Palmas", "#2E7D32", col=1
        )

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Prod.Treeview",
                        font=("Segoe UI", 12),
                        rowheight=34,
                        background="#FFFFFF",
                        fieldbackground="#FFFFFF",
                        foreground="#222222",
                        borderwidth=1,
                        relief="solid")
        style.configure("Prod.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#2C3E50",
                        foreground="#FFFFFF",
                        relief="flat",
                        padding=(6, 5))
        style.map("Prod.Treeview",
                  background=[("selected", "#E3F2FD")],
                  foreground=[("selected", "#1565C0")])
        style.map("Prod.Treeview.Heading",
                  background=[("active", "#34495E")])

        # Load data
        self.filterTableByDates()

    def _create_place_panel(self, parent, place_name, accent_color, col):
        """Create a panel for a specific place with KPI cards and table."""
        panel = ctk.CTkFrame(parent, fg_color="#FAFAFA", corner_radius=10, border_width=1, border_color="#E0E0E0")
        panel.grid(row=0, column=col, sticky="nsew", padx=5, pady=0)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # --- Place Title + Peso Total (same line) ---
        title_frame = ctk.CTkFrame(panel, fg_color=accent_color, corner_radius=0)
        title_frame.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            title_frame,
            text=f"  {place_name}",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left", padx=(15, 0), pady=6)

        peso_inner = ctk.CTkFrame(title_frame, fg_color="transparent")
        peso_inner.pack(side="right", padx=15, pady=4)
        ctk.CTkLabel(peso_inner, text="PESO TOTAL", font=("Segoe UI", 9), text_color="#E0E0E0").pack(anchor="e")
        lbl_peso = ctk.CTkLabel(peso_inner, text="0 kg", font=("Segoe UI", 16, "bold"), text_color="white")
        lbl_peso.pack(anchor="e")

        # --- Table ---
        tabla_container = ctk.CTkFrame(panel, fg_color="#FFFFFF", corner_radius=8)
        tabla_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(8, 10))

        tabla_frame = tk.Frame(tabla_container, bg="#FFFFFF")
        tabla_frame.pack(fill="both", expand=True, padx=2, pady=2)

        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical")

        columns = ["COD", "Fecha", "N° Baldes", "Tipo Balde", "Peso (kg)", "Estado"]
        widths = [75, 90, 70, 75, 75, 80]

        tree = ttk.Treeview(
            tabla_frame,
            columns=columns,
            show="headings",
            height=8,
            yscrollcommand=scrollbar_y.set,
            style="Prod.Treeview"
        )

        for i, c in enumerate(columns):
            tree.heading(c, text=c, anchor="center")
            tree.column(c, anchor="center", width=widths[i])

        tree.tag_configure("oddrow", background="#FFFFFF")
        tree.tag_configure("evenrow", background="#F5F5F5")
        tree.tag_configure("confirmed", foreground="#28a745")
        tree.tag_configure("pending", foreground="#FFC107")

        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_y.config(command=tree.yview)

        tabla_frame.grid_rowconfigure(0, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)

        tree.bind("<Double-1>", lambda e, t=tree: self.on_double_click(e, t))

        return {
            "tree": tree,
            "lbl_peso": lbl_peso,
            "columns": columns
        }

    def cargar_datos_panel(self, panel, datos):
        """Load data into a specific panel's tree and update its KPI cards."""
        tree = panel["tree"]
        for item in tree.get_children():
            tree.delete(item)

        total_peso = 0.0
        total_baldes = 0
        row_count = 0

        for _, row in datos.iterrows():
            try:
                fecha = row.get("Fecha", "")
                if isinstance(fecha, str):
                    fecha_str = fecha
                else:
                    fecha_str = fecha.strftime("%Y-%m-%d") if pd.notna(fecha) else ""

                peso = float(row.get("Peso (kg)", 0)) if pd.notna(row.get("Peso (kg)")) else 0
                baldes = float(row.get("N° Baldes", 0)) if pd.notna(row.get("N° Baldes")) else 0
                estado = row.get("Estado", "")
                total_peso += peso
                total_baldes += baldes

                tag = "evenrow" if row_count % 2 == 0 else "oddrow"

                tree.insert("", tk.END, values=(
                    row.get("COD", ""),
                    fecha_str,
                    f"{baldes:.1f}",
                    row.get("Tipo Balde", ""),
                    f"{peso:.1f}" if peso else "0",
                    estado
                ), tags=(tag,))
                row_count += 1

            except Exception as e:
                print(f"Error al cargar fila produccion: {row} -> {e}")

        panel["lbl_peso"].configure(text=f"{total_peso:,.1f} kg")

    def on_double_click(self, event, tree):
        item_id = tree.focus()
        if not item_id:
            return
        values = tree.item(item_id, "values")
        self.open_detail_window(values)

    def open_detail_window(self, values):
        """Open a read-only detail modal for a production record."""
        # Find full record from datos
        cod = values[0]
        record = self.datos[self.datos["COD"] == cod]
        if record.empty:
            return
        record = record.iloc[0]

        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Detalle Produccion - {cod}")

        detail_window.update_idletasks()
        width, height = 400, 380
        x = (detail_window.winfo_screenwidth() // 2) - (width // 2)
        y = (detail_window.winfo_screenheight() // 2) - (height // 2)
        detail_window.geometry(f"{width}x{height}+{x}+{y}")

        # --- Header ---
        status = record.get("Estado", "")
        header_color = "#28a745" if status == "confirmed" else "#FFC107"
        status_text = "Confirmado" if status == "confirmed" else status.capitalize() if status else "Sin estado"

        header_bg = ctk.CTkFrame(detail_window, fg_color=header_color, corner_radius=0)
        header_bg.pack(fill="x")

        header_inner = ctk.CTkFrame(header_bg, fg_color="transparent")
        header_inner.pack(padx=20, pady=12)

        ctk.CTkLabel(
            header_inner,
            text=f"Produccion {cod}",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text=f"Estado: {status_text}",
            font=("Segoe UI", 12),
            text_color="#E8F5E9" if status == "confirmed" else "#333333"
        ).pack(anchor="w")

        # --- Detail fields ---
        main_frame = ctk.CTkFrame(detail_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        fields = [
            ("Fecha", record.get("Fecha", "")),
            ("Lugar", record.get("Lugar", "")),
            ("N° Baldes", record.get("N° Baldes", "")),
            ("Tipo Balde", record.get("Tipo Balde", "")),
            ("Peso (kg)", f"{record.get('Peso (kg)', 0):.1f}"),
            ("Responsable", record.get("Responsable", "")),
        ]

        for i, (label, value) in enumerate(fields):
            ctk.CTkLabel(
                main_frame,
                text=label,
                font=("Segoe UI", 12, "bold"),
                text_color="#555555",
                anchor="w"
            ).grid(row=i, column=0, padx=(0, 15), pady=4, sticky="w")

            ctk.CTkLabel(
                main_frame,
                text=str(value) if pd.notna(value) else "-",
                font=("Segoe UI", 13),
                text_color="#111111",
                anchor="w"
            ).grid(row=i, column=1, pady=4, sticky="w")

        # --- Attachment button ---
        url = record.get("Url", "")
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(15, 0), sticky="ew")

        if url and pd.notna(url) and str(url).startswith("http"):
            def abrir_preview():
                chrome_path = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chrome.exe")
                if chrome_path:
                    webbrowser.get(f'"{chrome_path}" %s').open(str(url))
                else:
                    webbrowser.open(str(url))

            ctk.CTkButton(
                btn_frame,
                text="Ver Foto",
                fg_color="#3EA5FF",
                hover_color="#2196F3",
                width=150,
                height=34,
                font=("Segoe UI", 13),
                command=abrir_preview
            ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Cerrar",
            fg_color="#6C757D",
            hover_color="#5A6268",
            width=100,
            height=34,
            font=("Segoe UI", 13),
            command=detail_window.destroy
        ).pack(side="right")

    def filterTableByDates(self):
        try:
            fecha_ini = datetime.strptime(self.date_inicio.get(), "%Y-%m-%d")
            fecha_fin = datetime.strptime(self.date_fin.get(), "%Y-%m-%d")
        except Exception as e:
            print("Fechas invalidas:", e)
            return

        df = self.datos.copy()
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

        filtered = df[
            (df["Fecha"] >= fecha_ini) & (df["Fecha"] <= fecha_fin)
        ]

        # Split by place (case-insensitive)
        lugar_lower = filtered["Lugar"].str.lower()
        sf_data = filtered[lugar_lower == "san fernando"]
        lp_data = filtered[lugar_lower == "las palmas"]

        self.cargar_datos_panel(self.sf_panel, sf_data)
        self.cargar_datos_panel(self.lp_panel, lp_data)

    def recargar_tabla(self):
        try:
            self.datos = pd.DataFrame(self.process.getProduccion())
            self.filterTableByDates()
        except Exception as e:
            print(f"Error al recargar tabla de produccion: {e}")
