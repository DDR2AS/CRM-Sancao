import customtkinter as ctk
from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.process import Pipelines


class InicioFrame(ctk.CTkFrame):
    def __init__(self, master, process: Pipelines = None):
        super().__init__(master, fg_color="white")
        self.process = process

        # Load data
        if self.process is not None:
            try:
                self.datos = self.process.getTransactions()
            except Exception as e:
                print("Error al obtener datos:", e)
                self.datos = pd.DataFrame()
        else:
            self.datos = pd.DataFrame()

        # ===================== SCROLLABLE CONTAINER ===================== #
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="white")
        self.scroll.pack(fill="both", expand=True)

        # ===================== HEADER ===================== #
        header_frame = ctk.CTkFrame(self.scroll, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x")

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(
            header_inner,
            text="Dashboard",
            font=("Segoe UI", 24, "bold"),
            text_color="#1a1a2e"
        ).pack(side="left")

        # Year-Month Selector (right side)
        selector_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        selector_frame.pack(side="right")

        ctk.CTkLabel(
            selector_frame,
            text="Período:",
            font=("Segoe UI", 12),
            text_color="#555"
        ).pack(side="left", padx=(0, 8))

        # Generate month options (last 12 months + current)
        self.month_options = self._generate_month_options()

        self.month_selector = ctk.CTkComboBox(
            selector_frame,
            values=self.month_options,
            width=150,
            height=32,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 11),
            command=self.on_month_change
        )
        self.month_selector.set(self.month_options[0])  # Current month
        self.month_selector.pack(side="left")

        # ===================== SUMMARY CARDS ===================== #
        cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_frame.pack(fill="x", padx=25, pady=25)

        # Configure grid for responsive cards
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")

        # Row 1: Egresos
        self._create_summary_card(cards_frame, "GASTOS", "gasto", "#DC3545", "💰", 0, 0)
        self._create_summary_card(cards_frame, "JORNALES DIARIO", "jornales_diario", "#1c39dd", "👷", 0, 1)
        self._create_summary_card(cards_frame, "JORNALES MENSUAL", "jornales_mensual", "#1ca0dd", "📋", 0, 2)

        # Row 2: Otros
        self._create_summary_card(cards_frame, "ABONO", "abono", "#f1a643", "💵", 1, 0)
        self._create_summary_card(cards_frame, "ENVIADO", "enviado", "#17a2b8", "📤", 1, 1)
        self._create_summary_card(cards_frame, "VENTAS", "venta", "#28a745", "🍫", 1, 2)

        # ===================== BALANCE CARD ===================== #
        balance_frame = ctk.CTkFrame(self.scroll, fg_color="#F8F9FA", corner_radius=12)
        balance_frame.pack(fill="x", padx=25, pady=(0, 25))

        balance_inner = ctk.CTkFrame(balance_frame, fg_color="transparent")
        balance_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            balance_inner,
            text="📊 BALANCE DEL MES",
            font=("Segoe UI", 14, "bold"),
            text_color="#555"
        ).pack(anchor="w")

        self.label_balance = ctk.CTkLabel(
            balance_inner,
            text="S/ 0.00",
            font=("Segoe UI", 32, "bold"),
            text_color="#1a1a2e"
        )
        self.label_balance.pack(anchor="w", pady=(5, 0))

        self.label_balance_desc = ctk.CTkLabel(
            balance_inner,
            text="Ingresos - Egresos",
            font=("Segoe UI", 11),
            text_color="#888"
        )
        self.label_balance_desc.pack(anchor="w")

        # ===================== CHART ===================== #
        chart_frame = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        chart_frame.pack(fill="x", padx=25, pady=(0, 25))

        self.fig = Figure(figsize=(8, 3.5), dpi=100, facecolor="white")
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)

        # Hover annotation
        self._annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(0, 12),
            textcoords="offset points", ha="center",
            fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFFEE", ec="#CCCCCC", lw=0.8)
        )
        self._annot.set_visible(False)
        self._chart_bars = []
        self._chart_line = None
        self.canvas.mpl_connect("motion_notify_event", self._on_chart_hover)

        # Load initial data
        self.update_dashboard()

        # If process is None, schedule a reload after 10 seconds (DB might be connecting)
        if self.process is None:
            self.after(10000, self._try_reload_after_connection)

    def _generate_month_options(self):
        """Generate list of year-month options for the last 12 months"""
        options = []
        today = datetime.today()

        for i in range(12):
            # Calculate month going backwards
            month = today.month - i
            year = today.year

            while month <= 0:
                month += 12
                year -= 1

            # Format: "Enero 2026"
            month_names = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            options.append(f"{month_names[month - 1]} {year}")

        return options

    def _parse_selected_month(self):
        """Parse the selected month option to get year and month"""
        selected = self.month_selector.get()
        month_names = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        parts = selected.split(" ")
        month_name = parts[0]
        year = int(parts[1])
        month = month_names.index(month_name) + 1

        return year, month

    def _create_summary_card(self, parent, title, attr_name, color, icon, row, col):
        """Create a summary card with icon and value"""
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=15)

        # Header row with icon and title
        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x")

        ctk.CTkLabel(
            header_row,
            text=icon,
            font=("Segoe UI", 24)
        ).pack(side="left")

        ctk.CTkLabel(
            header_row,
            text=title,
            font=("Segoe UI", 11, "bold"),
            text_color="#888"
        ).pack(side="left", padx=(10, 0))

        # Value
        value_label = ctk.CTkLabel(
            inner,
            text="S/ 0.00",
            font=("Segoe UI", 22, "bold"),
            text_color=color
        )
        value_label.pack(anchor="w", pady=(10, 0))

        # Store reference to update later
        setattr(self, f"label_{attr_name}", value_label)

    def on_month_change(self, selection):
        """Called when month selector changes"""
        self.update_dashboard()

    def update_dashboard(self):
        """Update all dashboard values based on selected month"""
        year, month = self._parse_selected_month()

        # Filter data by selected month
        df = self.datos.copy()
        if df.empty:
            self._set_all_values(0, 0, 0, 0, 0, 0)
            return

        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

        # Filter by year and month
        filtered = df[
            (df["Fecha"].dt.year == year) &
            (df["Fecha"].dt.month == month)
        ]

        # Calculate totals (using pd.to_numeric to avoid FutureWarning)
        total_gasto = pd.to_numeric(filtered["Monto"], errors="coerce").fillna(0).sum() if "Monto" in filtered.columns else 0
        total_jornal_diario = pd.to_numeric(filtered["JornalDiario"], errors="coerce").fillna(0).sum() if "JornalDiario" in filtered.columns else 0
        total_jornal_mensual = pd.to_numeric(filtered["JornalMensual"], errors="coerce").fillna(0).sum() if "JornalMensual" in filtered.columns else 0
        total_abono = pd.to_numeric(filtered["GastoAbono"], errors="coerce").fillna(0).sum() if "GastoAbono" in filtered.columns else 0
        total_enviado = pd.to_numeric(filtered["Enviado"], errors="coerce").fillna(0).sum() if "Enviado" in filtered.columns else 0
        total_venta = pd.to_numeric(filtered["Venta"], errors="coerce").fillna(0).sum() if "Venta" in filtered.columns else 0

        self._set_all_values(
            total_gasto,
            total_jornal_diario,
            total_jornal_mensual,
            total_abono,
            total_enviado,
            total_venta
        )

        self._update_chart()

    def _set_all_values(self, gasto, jornal_diario, jornal_mensual, abono, enviado, venta):
        """Set all card values and calculate balance"""
        self.label_gasto.configure(text=f"S/ {gasto:,.2f}")
        self.label_jornales_diario.configure(text=f"S/ {jornal_diario:,.2f}")
        self.label_jornales_mensual.configure(text=f"S/ {jornal_mensual:,.2f}")
        self.label_abono.configure(text=f"S/ {abono:,.2f}")
        self.label_enviado.configure(text=f"S/ {enviado:,.2f}")
        self.label_venta.configure(text=f"S/ {venta:,.2f}")

        # Calculate balance: Ingresos (Venta + Abono) - Egresos (Gasto + Jornales + Enviado)
        ingresos = venta + abono
        egresos = gasto + jornal_diario + jornal_mensual + enviado
        balance = ingresos - egresos

        # Update balance with color
        if balance >= 0:
            self.label_balance.configure(text=f"S/ {balance:,.2f}", text_color="#28a745")
        else:
            self.label_balance.configure(text=f"S/ {balance:,.2f}", text_color="#DC3545")

        self.label_balance_desc.configure(
            text=f"Ingresos: S/ {ingresos:,.2f}  |  Egresos: S/ {egresos:,.2f}"
        )

    def _compute_monthly_summary(self):
        """Compute ingresos, egresos and balance for the last 6 months."""
        df = self.datos.copy()
        if df.empty:
            return [], [], [], []

        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

        year, month = self._parse_selected_month()

        months_labels = []
        ingresos_list = []
        egresos_list = []
        balance_list = []

        month_names_short = [
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
        ]

        for i in range(5, -1, -1):
            m = month - i
            y = year
            while m <= 0:
                m += 12
                y -= 1

            filtered = df[
                (df["Fecha"].dt.year == y) & (df["Fecha"].dt.month == m)
            ]

            gasto = pd.to_numeric(filtered.get("Monto", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
            jornal_d = pd.to_numeric(filtered.get("JornalDiario", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
            jornal_m = pd.to_numeric(filtered.get("JornalMensual", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
            enviado = pd.to_numeric(filtered.get("Enviado", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
            venta = pd.to_numeric(filtered.get("Venta", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
            abono = pd.to_numeric(filtered.get("GastoAbono", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()

            ingresos = venta + abono
            egresos = gasto + jornal_d + jornal_m + enviado

            months_labels.append(f"{month_names_short[m - 1]}\n{y}")
            ingresos_list.append(ingresos)
            egresos_list.append(egresos)
            balance_list.append(ingresos - egresos)

        return months_labels, ingresos_list, egresos_list, balance_list

    def _update_chart(self):
        """Redraw the chart with current data."""
        labels, ingresos, egresos, balance = self._compute_monthly_summary()

        self.ax.clear()
        self._chart_bars = []
        self._chart_line = None

        # Re-create annotation after clear
        self._annot = self.ax.annotate(
            "", xy=(0, 0), xytext=(0, 12),
            textcoords="offset points", ha="center",
            fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#FFFFFFEE", ec="#CCCCCC", lw=0.8)
        )
        self._annot.set_visible(False)

        if not labels:
            self.ax.text(0.5, 0.5, "Sin datos", ha="center", va="center",
                         fontsize=14, color="#888", transform=self.ax.transAxes)
            self.canvas.draw()
            return

        x = np.arange(len(labels))
        width = 0.32

        bars_ing = self.ax.bar(x - width / 2, ingresos, width, color="#28a745", label="Ingresos", zorder=2)
        bars_egr = self.ax.bar(x + width / 2, egresos, width, color="#DC3545", label="Egresos", zorder=2)
        line = self.ax.plot(x, balance, color="#3EA5FF", linewidth=2, linestyle="--", marker="o",
                            markersize=6, label="Balance", zorder=3)

        self._chart_bars = list(bars_ing) + list(bars_egr)
        self._chart_line = line[0]

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(labels, fontsize=9)
        self.ax.legend(fontsize=9, loc="upper left")
        self.ax.set_ylabel("S/", fontsize=10)
        self.ax.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)
        self.ax.set_axisbelow(True)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.fig.tight_layout()
        self.canvas.draw()

    def _on_chart_hover(self, event):
        """Show value tooltip when hovering over bars or line points."""
        if event.inaxes != self.ax:
            if self._annot.get_visible():
                self._annot.set_visible(False)
                self.canvas.draw_idle()
            return

        # Check bars
        for bar in self._chart_bars:
            if bar.contains(event)[0]:
                val = bar.get_height()
                x = bar.get_x() + bar.get_width() / 2
                y = val
                self._annot.xy = (x, y)
                self._annot.set_text(f"S/ {val:,.0f}")
                self._annot.set_visible(True)
                self.canvas.draw_idle()
                return

        # Check line points
        if self._chart_line is not None:
            contains, info = self._chart_line.contains(event)
            if contains:
                idx = info["ind"][0]
                xdata = self._chart_line.get_xdata()
                ydata = self._chart_line.get_ydata()
                self._annot.xy = (xdata[idx], ydata[idx])
                self._annot.set_text(f"S/ {ydata[idx]:,.0f}")
                self._annot.set_visible(True)
                self.canvas.draw_idle()
                return

        if self._annot.get_visible():
            self._annot.set_visible(False)
            self.canvas.draw_idle()

    def _try_reload_after_connection(self):
        """Try to reload data after DB connection is ready"""
        try:
            # Get process from parent app
            app = self.winfo_toplevel()
            if hasattr(app, 'process') and app.process is not None:
                self.process = app.process
                self.datos = self.process.getTransactions()
                self.update_dashboard()
                print("✅ Dashboard recargado con datos de la BD")
        except Exception as e:
            print(f"Error al recargar dashboard: {e}")

    def recargar_datos(self):
        """Reload data from database"""
        if self.process is None:
            return
        try:
            self.datos = self.process.getTransactions()
            self.update_dashboard()
        except Exception as e:
            print("Error al recargar datos:", e)
