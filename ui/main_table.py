import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

class MainTable(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.columns = ("Fecha", "Descripción", "Categoría", "Monto", "Estado")

        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=120)

        # Datos de ejemplo
        data = [
            ["2025-07-01", "Compra abono", "Agrícola", "150.00", "Pagado"],
            ["2025-07-02", "Venta cacao", "Ingreso", "800.00", "Recibido"],
            ["2025-07-03", "Flete", "Transporte", "50.00", "Pendiente"],
        ]

        for row in data:
            self.tree.insert("", tk.END, values=row)

        self.tree.pack(fill="both", expand=True)
